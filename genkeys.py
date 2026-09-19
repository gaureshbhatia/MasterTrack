import getpass
import sqlite3

import streamlit_authenticator as stauth

DATABASE = "users.db"

def initialize_database():
	"""Create the credentials table if it dsnt exist."""
	with sqlite3.connect(DATABASE) as connection:
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password_hash TEXT NOT NULL
			)
			"""
		)
#-----------------TEST USER-----------------
		if connection.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None:
			test_username = "test"
			test_password = "password"
			test_password_hash = stauth.Hasher.hash(test_password)
			connection.execute(
				"INSERT INTO users (username, password_hash) VALUES (?, ?)",
				(test_username, test_password_hash),
			)

def sign_up(username, password):
	"""Hash and insert one user into the database."""
	password_hash = stauth.Hasher.hash(password)

	try:
		with sqlite3.connect(DATABASE) as connection:
			connection.execute(
				"INSERT INTO users (username, password_hash) VALUES (?, ?)",
				(username, password_hash),
			)
	except sqlite3.IntegrityError as error:
		raise ValueError(f"Username '{username}' already exists.") from error


def collect_user_input():
	"""Ask for a username and confirm a password ,dont display it"""
	username = input("Username: ").strip()
	if not username:
		raise ValueError("Username cannot be empty.")

	password = getpass.getpass("Password: ")
	if not password:
		raise ValueError("Password cannot be empty.")

	confirmed_password = getpass.getpass("Confirm password: ")
	if password != confirmed_password:
		raise ValueError("Passwords do not match.")

	return username, password


def main():
	initialize_database()

	try:
		username, password = collect_user_input()
		sign_up(username, password)
	except ValueError as error:
		print(f"Error: {error}")
		return

	print(f"User '{username}' created successfully.")


if __name__ == "__main__":
	main()
