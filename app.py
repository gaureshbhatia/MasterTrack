import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth

from genkeys import (
	DatabaseConnectionError,
	add_expense,
	get_expense_categories,
	get_database_connection,
	get_current_month_budget,
	get_current_month_expenses,
	get_user_id,
	initialize_database,
	set_current_month_budget,
	sign_up,
)


def ensure_cookie_key():
	#Ensure that the auth_cookie_key is set in .streamlit/secrets.toml. If not, generate a new key and write it to the file.
	secret_path = Path(".streamlit/secrets.toml")
	secret_path.parent.mkdir(parents=True, exist_ok=True)

	cookie_key = None
	if secret_path.exists():
		with secret_path.open("r", encoding="utf-8") as secret_file:
			for line in secret_file:
				if line.strip().startswith("auth_cookie_key"):
					_, value = line.split("=", 1)
					cookie_key = value.strip().strip('"').strip("'")
					break

	if not cookie_key or cookie_key in {"replace-with-a-long-random-secret", ""}:
		cookie_key = secrets.token_urlsafe(32)
		if secret_path.exists():
			content = secret_path.read_text(encoding="utf-8")
			lines = content.splitlines()
			updated_lines = []
			replaced = False
			for line in lines:
				if line.strip().startswith("auth_cookie_key"):
					updated_lines.append(f'auth_cookie_key = "{cookie_key}"')
					replaced = True
				else:
					updated_lines.append(line)
			if not replaced:
				updated_lines.append(f'auth_cookie_key = "{cookie_key}"')
			secret_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
		else:
			secret_path.write_text(f'auth_cookie_key = "{cookie_key}"\n', encoding="utf-8")

	return cookie_key


def load_credentials():
	#Load the credentials from the MySQL database so that authenticator can read them.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute("SELECT username, password_hash FROM users ORDER BY username")
		rows = cursor.fetchall()
	finally:
		connection.close()

	return {
		"usernames": {
			username: {"name": username, "password": password_hash}
			for username, password_hash in rows
		}
	}


def show_login_screen(authenticator):
	#Render the login form and handle login attempts.
	authenticator.login(fields={
		"Form name": "Log in",
		"Username": "Username",
		"Password": "Password",
		"Login": "Log in",
	})

	if st.button("Create account", key="show_signup_button"):
		st.session_state["auth_screen"] = "signup"
		st.rerun()

	authentication_status = st.session_state.get("authentication_status")
	if authentication_status is False:
		st.error("Incorrect username or password.")


def show_signup_form():
	#Render the sign-up form and handle account creation.
	st.subheader("Sign up")
	with st.form("signup_form", clear_on_submit=True):
		username = st.text_input("Username", key="signup_username")
		password = st.text_input("Password", type="password", key="signup_password")
		confirmed_password = st.text_input(
			"Confirm password", type="password", key="signup_password_confirmation"
		)
		submitted = st.form_submit_button("Sign up")

	if submitted:
		username = username.strip()
		if not username or not password:
			st.error("Enter a username and password.")
		elif password != confirmed_password:
			st.error("Passwords do not match.")
		else:
			try:
				sign_up(username, password)
			except (DatabaseConnectionError, ValueError) as error:
				st.error(str(error))
			else:
				st.success("Account created. You can now log in.")
				st.session_state["auth_screen"] = "login"
				st.rerun()

	if st.button("Back to login", key="show_login_button"):
		st.session_state["auth_screen"] = "login"
		st.rerun()


def show_expense_form(username):
	#Render the initial save-only expense entry form.
	st.subheader("Add an expense")
	category_options = get_expense_categories()
	category_names = {name: category_id for category_id, name in category_options}

	with st.form("expense_form", clear_on_submit=True):
		amount_column, category_column = st.columns(2)
		with amount_column:
			amount_text = st.text_input("Amount (INR)", placeholder="0.00")
		with category_column:
			category_name = st.selectbox("Expense type", list(category_names))
		submitted = st.form_submit_button("Save expense")

	if submitted:
		try:
			amount_inr = Decimal(amount_text.strip())
		except (InvalidOperation, AttributeError):
			st.error("Enter a valid INR amount, such as 125.50.")
			return

		if not amount_inr.is_finite() or amount_inr <= 0:
			st.error("The amount must be greater than zero.")
			return
		if amount_inr.as_tuple().exponent < -2:
			st.error("Enter an amount with no more than two decimal places.")
			return

		try:
			user_id = get_user_id(username)
			add_expense(user_id, category_names[category_name], amount_inr)
		except (DatabaseConnectionError, ValueError) as error:
			st.error(str(error))
		else:
			st.success("Expense saved successfully.")


def get_current_month_boundaries():
	now = datetime.now()
	month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
	if month_start.month == 12:
		next_month_start = month_start.replace(
			year=month_start.year + 1, month=1
		)
	else:
		next_month_start = month_start.replace(month=month_start.month + 1)
	return now, month_start, next_month_start


def show_monthly_budget(username, month_start):
	user_id = get_user_id(username)
	budget_inr = get_current_month_budget(user_id, month_start)
	if budget_inr == -1:
		prompt = "Would you like to set a budget for this month?"
	else:
		prompt = "Would you like to update the budget for this month?"

	st.subheader(prompt)
	with st.form("monthly_budget_form", clear_on_submit=True):
		budget_text = st.text_input(
			"Monthly budget (INR)",
			value="" if budget_inr == -1 else f"{budget_inr:.2f}",
			placeholder="0.00",
		)
		submitted = st.form_submit_button("Save budget")

	if submitted:
		try:
			new_budget = Decimal(budget_text.strip())
		except (InvalidOperation, AttributeError):
			st.error("Enter a valid INR budget, such as 25000.00.")
			return

		if not new_budget.is_finite() or new_budget < 0:
			st.error("The budget must be zero or greater.")
			return
		if new_budget.as_tuple().exponent < -2:
			st.error("Enter a budget with no more than two decimal places.")
			return

		try:
			set_current_month_budget(user_id, month_start, new_budget)
		except DatabaseConnectionError as error:
			st.error(str(error))
		else:
			st.success("Monthly budget saved successfully.")
			st.rerun()


def show_current_month_expenses(username):
	#Use calendar-month boundaries rather than a rolling 30-day window.
	now, month_start, next_month_start = get_current_month_boundaries()

	user_id = get_user_id(username)
	expenses = get_current_month_expenses(
		user_id, month_start, next_month_start
	)
	st.subheader(f"Spending for {now.strftime('%B %Y')}")

	if not expenses:
		st.info("No expenses recorded this month.")
		return

	st.table(
		[
			{	
				"Amount (INR)": f"{amount_inr:.2f}",
				"Category": category_name,
				"Date": created_at.strftime("%Y-%m-%d %H:%M"),
			}
			for created_at, category_name, amount_inr in expenses
		]
	)


def main():
	st.set_page_config(page_title="Personal Finance", page_icon="$")

	try:
		initialize_database()
		credentials = load_credentials()
	except DatabaseConnectionError as error:
		st.title("Welcome to Personal Finance")
		st.error(str(error))
		st.info(
			"Install and start MySQL, create the personal_finance database, "
			"then restart Streamlit."
		)
		st.stop()

	st.title("Welcome to Personal Finance")
	st.session_state.setdefault("auth_screen", "login")

	cookie_key = ensure_cookie_key()
	authenticator = stauth.Authenticate(
		credentials,
		cookie_name="personal_finance_auth",
		cookie_key=cookie_key,
		cookie_expiry_days=30,
		auto_hash=False,
	)

	authentication_status = st.session_state.get("authentication_status")

	if authentication_status:
		st.markdown(
			"""
			<style>
			[data-testid="stSidebar"],
			[data-testid="stSidebarContent"],
			[data-testid="stSidebarUserContent"] {
				background: transparent;
				box-shadow: none;
			}
			</style>
			""",
			unsafe_allow_html=True,
		)

		with st.sidebar:
			authenticator.logout("Log out")
		try:
			_, month_start, _ = get_current_month_boundaries()
			show_monthly_budget(st.session_state["username"], month_start)
			show_expense_form(st.session_state["username"])
			show_current_month_expenses(st.session_state["username"])
		except DatabaseConnectionError as error:
			st.error(str(error))
	elif st.session_state["auth_screen"] == "signup":
		show_signup_form()
	else:
		show_login_screen(authenticator)


if __name__ == "__main__":
	main()
