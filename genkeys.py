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
	#Create the application tables and insert a test user if the users table is empty.
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
		cursor.execute(
			"""
			SELECT COUNT(*)
			FROM information_schema.COLUMNS
			WHERE TABLE_SCHEMA = DATABASE()
				AND TABLE_NAME = 'users'
				AND COLUMN_NAME = 'monthly_budget_inr'
			"""
		)
		if cursor.fetchone()[0] == 0:
			cursor.execute(
			"""
			ALTER TABLE users
			ADD COLUMN monthly_budget_inr DECIMAL(10, 2) NOT NULL DEFAULT -1.00
			"""
			)
		cursor.execute(
			"""
			SELECT COUNT(*)
			FROM information_schema.COLUMNS
			WHERE TABLE_SCHEMA = DATABASE()
				AND TABLE_NAME = 'users'
				AND COLUMN_NAME = 'budget_month'
			"""
		)
		if cursor.fetchone()[0] == 0:
			cursor.execute(
			"""
			ALTER TABLE users
			ADD COLUMN budget_month DATE NULL
			"""
			)
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS expense_categories (
				id INT PRIMARY KEY,
				name VARCHAR(100) NOT NULL UNIQUE
			)
			"""
		)
		cursor.executemany(
			"""
			INSERT INTO expense_categories (id, name)
			VALUES (%s, %s)
			ON DUPLICATE KEY UPDATE name = VALUES(name)
			""",
			[(1, "Type 1"), (2, "Type 2"), (3, "Type 3"), (4, "Type 4")],
		)
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS expenses (
				id INT AUTO_INCREMENT PRIMARY KEY,
				user_id INT NOT NULL,
				category_id INT NOT NULL,
				amount DECIMAL(10, 2) NOT NULL,
				created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				CONSTRAINT fk_expenses_user
					FOREIGN KEY (user_id) REFERENCES users(id),
				CONSTRAINT fk_expenses_category
					FOREIGN KEY (category_id) REFERENCES expense_categories(id)
			)
			"""
		)
		cursor.execute(
			"""
			SELECT COLUMN_NAME
			FROM information_schema.COLUMNS
			WHERE TABLE_SCHEMA = DATABASE()
				AND TABLE_NAME = 'expenses'
				AND COLUMN_NAME IN ('amount', 'amount_inr')
			"""
		)
		expense_amount_columns = {row[0] for row in cursor.fetchall()}
		if expense_amount_columns == {"amount_inr"}:
			cursor.execute(
				"""
				ALTER TABLE expenses
				CHANGE COLUMN amount_inr amount DECIMAL(10, 2) NOT NULL
				"""
			)
		elif expense_amount_columns == {"amount", "amount_inr"}:
			raise DatabaseConnectionError(
				"The expenses table contains both amount and amount_inr columns. "
				"Reconcile the duplicate columns before starting the app."
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


def get_user_id(username):
	#Resolve the authenticated username to its database ID for expense ownership.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
		row = cursor.fetchone()
	finally:
		connection.close()

	if row is None:
		raise ValueError("The logged-in user could not be found.")
	return row[0]


def get_expense_categories():
	#Load the category lookup values so the dropdown matches the database mapping.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute("SELECT id, name FROM expense_categories ORDER BY id")
		return cursor.fetchall()
	finally:
		connection.close()


def add_expense(user_id, category_id, amount):
	#Insert one expense using parameterized SQL and the authenticated user's ID.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			INSERT INTO expenses (user_id, category_id, amount)
			VALUES (%s, %s, %s)
			""",
			(user_id, category_id, amount),
		)
		connection.commit()
	finally:
		connection.close()


def get_current_month_expenses(user_id, month_start, next_month_start):
	#Return only this user's expenses in the current calendar month.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			SELECT e.created_at, c.name, e.amount
			FROM expenses AS e
			JOIN expense_categories AS c ON c.id = e.category_id
			WHERE e.user_id = %s
				AND e.created_at >= %s
				AND e.created_at < %s
			ORDER BY e.created_at DESC, e.id DESC
			""",
			(user_id, month_start, next_month_start),
		)
		return cursor.fetchall()
	finally:
		connection.close()


def get_current_month_budget(user_id, month_start):
	#Reset the budget lazily when the user first opens the app in a new month.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			SELECT monthly_budget_inr, budget_month
			FROM users
			WHERE id = %s
			""",
			(user_id,),
		)
		row = cursor.fetchone()
		if row is None:
			raise ValueError("The logged-in user could not be found.")

		budget_inr, budget_month = row
		current_month = month_start.date()
		if budget_month != current_month:
			budget_inr = -1
			cursor.execute(
				"""
				UPDATE users
				SET monthly_budget_inr = %s, budget_month = %s
				WHERE id = %s
				""",
				(budget_inr, current_month, user_id),
			)
			connection.commit()
		return budget_inr
	finally:
		connection.close()


def set_current_month_budget(user_id, month_start, budget_inr):
	#Save the budget for this user's current calendar month.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			UPDATE users
			SET monthly_budget_inr = %s, budget_month = %s
			WHERE id = %s
			""",
			(budget_inr, month_start.date(), user_id),
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
