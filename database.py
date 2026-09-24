import os
import sqlite3


DATABASE = os.path.join(
	os.path.dirname(os.path.abspath(__file__)),
	"users.db",
)


class DatabaseConnectionError(RuntimeError):
	"""Raised when the application database cannot be opened."""


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
	"""Create the user, category, expense, and budget tables."""
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password_hash TEXT NOT NULL
			)
			"""
		)
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS expense_categories (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE
			)
			"""
		)
		cursor.executemany(
			"INSERT OR IGNORE INTO expense_categories (name) VALUES (?)",
			[("Type 1",), ("Type 2",), ("Type 3",), ("Type 4",)],
		)
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS expenses (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				amount REAL NOT NULL,
				category_id INTEGER NOT NULL,
				created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
				FOREIGN KEY (category_id) REFERENCES expense_categories(id)
			)
			"""
		)
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS budgets (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				amount REAL NOT NULL,
				month INTEGER NOT NULL,
				year INTEGER NOT NULL,
				FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
				UNIQUE (user_id, month, year)
			)
			"""
		)
		connection.commit()
	finally:
		connection.close()


def get_user_id(username):
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


def add_expense(user_id, amount, category_id):
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


def get_expense_categories():
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute("SELECT id, name FROM expense_categories ORDER BY id")
		return cursor.fetchall()
	finally:
		connection.close()


def get_current_month_expenses(user_id, month_start, next_month_start):
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
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			SELECT COALESCE(SUM(amount), -1)
			FROM budgets
			WHERE user_id = ? AND month = ? AND year = ?
			""",
			(user_id, month_start.month, month_start.year),
		)
		return cursor.fetchone()[0]
	finally:
		connection.close()


def set_current_month_budget(user_id, month_start, budget_inr):
	connection = get_database_connection()
	try:
		cursor = connection.cursor()
		cursor.execute(
			"""
			INSERT INTO budgets (user_id, amount, month, year)
			VALUES (?, ?, ?, ?)
			ON CONFLICT(user_id, month, year)
			DO UPDATE SET amount = excluded.amount
			""",
			(user_id, float(budget_inr), month_start.month, month_start.year),
		)
		connection.commit()
	finally:
		connection.close()

if __name__ == "__main__":
	initialize_database()
	print(f"Database initialized at {DATABASE}")
