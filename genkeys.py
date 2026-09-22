import getpass

import mysql.connector
import streamlit as st
import streamlit_authenticator as stauth


class DatabaseConnectionError(RuntimeError):
	pass
	#if server not reached


def get_database_connection():
	#connect to mysql database using credentials from .streamlit/secrets.toml
	try:
		return mysql.connector.connect(**dict(st.secrets["mysql"]))
	except mysql.connector.Error as error:
		raise DatabaseConnectionError(
			"Cannot connect to MySQL. Start the MySQL service and verify the "
			"connection settings in .streamlit/secrets.toml."
		) from error


def initialize_database():
	#Create the users table if it doesn't exist and insert a test user if the table is empty.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INT AUTO_INCREMENT PRIMARY KEY,
				username VARCHAR(255) NOT NULL UNIQUE,
				password_hash VARCHAR(255) NOT NULL
			)
			"""
		)
		cursor.execute("SELECT 1 FROM users LIMIT 1")
		if cursor.fetchone() is None:
			test_username = "test"
			test_password = "password"
			test_password_hash = stauth.Hasher.hash(test_password)
			cursor.execute(
				"INSERT INTO users (username, password_hash) VALUES (%s, %s)",
				(test_username, test_password_hash),
			)
		connection.commit()
	finally:
		connection.close()

def sign_up(username, password):
	#Hash and insert one user into the database.
	password_hash = stauth.Hasher.hash(password)

	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"INSERT INTO users (username, password_hash) VALUES (%s, %s)",
			(username, password_hash),
		)
		connection.commit()
	except mysql.connector.IntegrityError as error:
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
