import sqlite3
import os


# ==================================================
# DATABASE CONFIGURATION
# ==================================================

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "finance.db"
)


# ==================================================
# DATABASE CONNECTION
# ==================================================

def connect_database():
    connection = sqlite3.connect(DATABASE)

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ==================================================
# CREATE TABLES
# ==================================================

def create_tables():

    connection = connect_database()
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # USERS TABLE
        # --------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE
            )
        """)


        # --------------------------------------------------
        # EXPENSE CATEGORIES TABLE
        # --------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expense_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE
            )
        """)


        # --------------------------------------------------
        # EXPENSES TABLE
        # --------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (category_id)
                    REFERENCES expense_categories(id)
                    ON DELETE RESTRICT
            )
        """)


        # --------------------------------------------------
        # INCOME TABLE
        # --------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)


        # --------------------------------------------------
        # BUDGETS TABLE
        # --------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (category_id)
                    REFERENCES expense_categories(id)
                    ON DELETE RESTRICT,

                UNIQUE (
                    user_id,
                    category_id,
                    month,
                    year
                )
            )
        """)

        connection.commit()

        print("All tables have been created successfully.")

    except sqlite3.Error as error:

        connection.rollback()

        print("Database error:", error)

        raise

    finally:

        cursor.close()
        connection.close()


# ==================================================
# GET CURRENT MONTH EXPENSES
# ==================================================

def get_current_month_expenses(
    user_id,
    month_start,
    next_month_start
):

    connection = connect_database()
    cursor = connection.cursor()

    try:

        query = """
            SELECT
                expenses.created_at,
                expense_categories.category,
                expenses.amount

            FROM expenses

            JOIN expense_categories
                ON expenses.category_id =
                   expense_categories.id

            WHERE expenses.user_id = ?

            AND expenses.created_at >= ?

            AND expenses.created_at < ?

            ORDER BY expenses.created_at
        """

        cursor.execute(
            query,
            (
                user_id,
                month_start.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                next_month_start.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        transactions = cursor.fetchall()

        return transactions

    finally:

        cursor.close()
        connection.close()


# ==================================================
# GET CURRENT MONTH BUDGET
# ==================================================

def get_current_month_budget(
    user_id,
    month_start
):

    connection = connect_database()
    cursor = connection.cursor()

    try:

        query = """
            SELECT COALESCE(
                SUM(amount),
                -1
            )

            FROM budgets

            WHERE user_id = ?

            AND month = ?

            AND year = ?
        """

        cursor.execute(
            query,
            (
                user_id,
                month_start.month,
                month_start.year
            )
        )

        result = cursor.fetchone()

        return result[0]

    finally:

        cursor.close()
        connection.close()


# ==================================================
# RUN DATABASE SETUP
# ==================================================

if __name__ == "__main__":

    print("Starting database setup...\n")

    print(
        "Database location:",
        DATABASE
    )

    create_tables()

    print(
        "\nDatabase setup completed."
    )