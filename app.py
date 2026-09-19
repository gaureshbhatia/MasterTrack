import secrets
import sqlite3
from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth

from genkeys import DATABASE, initialize_database, sign_up


def ensure_cookie_key():
	"""Create and persist a cookie key in .streamlit/secrets.toml if needed."""
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


def show_login_screen(authenticator):
	"""Render the login screen and let users open the signup screen."""
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
	"""Render the username/password signup form."""
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
			except ValueError as error:
				st.error(str(error))
			else:
				st.success("Account created. You can now log in.")
				st.session_state["auth_screen"] = "login"
				st.rerun()

	if st.button("Back to login", key="show_login_button"):
		st.session_state["auth_screen"] = "login"
		st.rerun()


def main():
	st.set_page_config(page_title="Personal Finance", page_icon="$")
	initialize_database()

	st.title("Welcome to Personal Finance")
	st.session_state.setdefault("auth_screen", "login")

	cookie_key = ensure_cookie_key()
	authenticator = stauth.Authenticate(
		load_credentials(),
		cookie_name="personal_finance_auth",
		cookie_key=cookie_key,
		cookie_expiry_days=30,
		auto_hash=False,
	)

	authentication_status = st.session_state.get("authentication_status")
	if authentication_status:
		authenticator.logout("Log out")
		st.write("hello, ur logged in")
		st.success(f"Welcome, {st.session_state['username']}!")
		st.write("Your personal finance dashboard will appear here.")
	elif st.session_state["auth_screen"] == "signup":
		show_signup_form()
	else:
		show_login_screen(authenticator)


if __name__ == "__main__":
	main()
