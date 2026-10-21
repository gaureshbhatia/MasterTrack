import getpass
import sqlite3

import streamlit as st
import streamlit_authenticator as stauth

from database import (
	DatabaseConnectionError,
	get_database_connection,
	initialize_database,
)

def sign_up(username, password):
	#Hash and insert one user into the database.
	password_hash = stauth.Hasher.hash(password)

	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"INSERT INTO users (username, password_hash) VALUES (?, ?)",
			(username, password_hash),
		)
		connection.commit()
	except sqlite3.IntegrityError as error:
		raise ValueError(f"Username '{username}' already exists.") from error
	finally:
		connection.close()


def collect_user_input():
	#Ask for a username and confirm a password ,dont display the password
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
