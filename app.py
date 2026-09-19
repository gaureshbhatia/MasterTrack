import sqlite3

import streamlit as st
import streamlit_authenticator as stauth

from genkeys import DATABASE, initialize_database, sign_up


def load_credentials():
	"""Load stored password hashes in Streamlit Authenticator's format."""
	with sqlite3.connect(DATABASE) as connection:
		rows = connection.execute(
			"SELECT username, password_hash FROM users ORDER BY username"
		).fetchall()

	return {
		"usernames": {
			username: {"name": username, "password": password_hash}
			for username, password_hash in rows
		}
	}


def show_signup_form():
	"""Render the username/password signup form."""
	st.subheader("Sign up")
	with st.form("signup_form", clear_on_submit=True):
		username = st.text_input("Username", key="signup_username")
		password = st.text_input("Password", type="password", key="signup_password")
		confirmed_password = st.text_input(
			"Confirm password", type="password", key="signup_password_confirmation"
		)
		submitted = st.form_submit_button("Sign up")

	if not submitted:
		return

	username = username.strip()
	if not username or not password:
		st.error("Enter a username and password.")
	elif password != confirmed_password:
		st.error("Passwords do not match.")
	else:
		try:
			sign_up(username, password)
		except ValueError as error:
			st.error(str(error))
		else:
			st.success("Account created. You can now log in.")
			st.rerun()


def main():
	st.set_page_config(page_title="Personal Finance", page_icon="$")
	initialize_database()

	st.title("Welcome to Personal Finance")

	try:
		cookie_key = st.secrets["auth_cookie_key"]
	except KeyError:
		st.error(
			"Missing auth cookie key. Add auth_cookie_key to "
			".streamlit/secrets.toml before starting the app."
		)
		st.stop()

	authenticator = stauth.Authenticate(
		load_credentials(),
		cookie_name="personal_finance_auth",
		cookie_key=cookie_key,
		cookie_expiry_days=30,
		auto_hash=False,
	)
	authenticator.login(fields={
		"Form name": "Log in",
		"Username": "Username",
		"Password": "Password",
		"Login": "Log in",
	})

	authentication_status = st.session_state.get("authentication_status")
	if authentication_status:
		authenticator.logout("Log out")
		st.success(f"Welcome, {st.session_state['username']}!")
		st.write("Your personal finance dashboard will appear here.")
	elif authentication_status is False:
		st.error("Incorrect username or password.")
	else:
		st.divider()
		show_signup_form()


if __name__ == "__main__":
	main()
