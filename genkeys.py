import getpass
import sqlite3

import streamlit as st
import streamlit_authenticator as stauth


DATABASE = "users.db"


class DatabaseConnectionError(RuntimeError):
	#Raise this when the database cannot be opened or is misconfigured.
	pass


def get_database_connection():
	try:
		connection = sqlite3.connect(
			DATABASE,
			detect_types=sqlite3.PARSE_DECLTYPES,
		)
		connection.execute("PRAGMA foreign_keys = ON")
		return connection
	except sqlite3.Error as error:
		raise DatabaseConnectionError(
			"Cannot open the local SQLite database. Check that the application "
			"directory is writable."
		) from error


def initialize_database():
	#Create the application tables and insert a test user if the users table is empty.
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password_hash TEXT NOT NULL,
				monthly_budget_inr NUMERIC NOT NULL DEFAULT -1.00,
				budget_month DATE
			)
			"""
		)
		user_columns = {
			row[1] for row in cursor.execute("PRAGMA table_info(users)")
		}
		if "monthly_budget_inr" not in user_columns:
			cursor.execute(
				"ALTER TABLE users ADD COLUMN monthly_budget_inr NUMERIC "
				"NOT NULL DEFAULT -1.00"
			)
		if "budget_month" not in user_columns:
			cursor.execute("ALTER TABLE users ADD COLUMN budget_month DATE")
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS expense_categories (
				id INTEGER PRIMARY KEY,
				name TEXT NOT NULL UNIQUE
			)
			"""
		)
		cursor.executemany(
			"""
			INSERT INTO expense_categories (id, name)
			VALUES (?, ?)
			ON CONFLICT(id) DO UPDATE SET name = excluded.name
			""",
			[(1, "Type 1"), (2, "Type 2"), (3, "Type 3"), (4, "Type 4")],
		)
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS expenses (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				category_id INTEGER NOT NULL,
				amount NUMERIC NOT NULL,
				created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (user_id) REFERENCES users(id),
				FOREIGN KEY (category_id) REFERENCES expense_categories(id)
			)
			"""
		)
		expense_amount_columns = {
			row[1] for row in cursor.execute("PRAGMA table_info(expenses)")
			if row[1] in {"amount", "amount_inr"}
		}
		if expense_amount_columns == {"amount_inr"}:
			cursor.execute("ALTER TABLE expenses RENAME COLUMN amount_inr TO amount")
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
				"INSERT INTO users (username, password_hash) VALUES (?, ?)",
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
		cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
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
			VALUES (?, ?, ?)
			""",
			(user_id, category_id, float(amount)),
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
			WHERE e.user_id = ?
				AND e.created_at >= ?
				AND e.created_at < ?
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
			WHERE id = ?
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
					SET monthly_budget_inr = ?, budget_month = ?
					WHERE id = ?
				""",
				(float(budget_inr), current_month, user_id),
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
			SET monthly_budget_inr = ?, budget_month = ?
			WHERE id = ?
			""",
			(float(budget_inr), month_start.date(), user_id),
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
