from datetime import datetime
from pathlib import Path

from database import (
    get_database_connection,
    get_user_id,
    initialize_database,
    set_current_month_budget,
)
from visualization import generate_charts


TEST_USERNAME = "visualization_test_user"
TEST_MONTHLY_BUDGET = 30000.0


def create_sample_data():
    """Create repeatable current-month test data in users.db."""

    initialize_database()
    now = datetime.now()

    connection = get_database_connection()
    try:
        cursor = connection.cursor()

        # Create a dedicated visualization test user if it does not exist.
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash)
            VALUES (?, ?)
            """,
            (TEST_USERNAME, "sample_hash_not_for_login"),
        )

        cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (TEST_USERNAME,),
        )
        user_id = cursor.fetchone()[0]

        cursor.execute(
            "SELECT id, name FROM expense_categories ORDER BY id"
        )
        categories = cursor.fetchall()

        if not categories:
            raise RuntimeError("No expense categories were found.")

        # Remove only this test user's current-month rows, making the test rerunnable.
        cursor.execute(
            """
            DELETE FROM expenses
            WHERE user_id = ?
              AND CAST(strftime('%m', created_at) AS INTEGER) = ?
              AND CAST(strftime('%Y', created_at) AS INTEGER) = ?
            """,
            (user_id, now.month, now.year),
        )

        sample_expenses = [
            (2, 1200.0, 0),
            (5, 800.0, 1),
            (8, 2450.0, 2),
            (12, 1750.0, 3),
            (16, 600.0, 0),
            (20, 1300.0, 1),
            (now.day, 900.0, 2),
        ]

        for day, amount, category_index in sample_expenses:
            if day > now.day:
                continue

            category_id = categories[category_index % len(categories)][0]
            created_at = now.replace(
                day=day,
                hour=12,
                minute=0,
                second=0,
                microsecond=0,
            )

            cursor.execute(
                """
                INSERT INTO expenses (
                    user_id,
                    category_id,
                    amount,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    category_id,
                    amount,
                    created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

        connection.commit()
    finally:
        connection.close()

    set_current_month_budget(
        user_id=user_id,
        month_start=datetime(now.year, now.month, 1),
        budget_inr=TEST_MONTHLY_BUDGET,
    )

    return user_id


def main():
    user_id = create_sample_data()

    # Confirm that the same user can be resolved through database.py.
    resolved_user_id = get_user_id(TEST_USERNAME)
    assert resolved_user_id == user_id

    result = generate_charts(
        user_id=user_id,
        username=TEST_USERNAME,
    )

    print("\nVisualization test completed successfully.")
    print(f"Total expenditure: Rs. {result['total_expenses']:,.2f}")
    print(f"Monthly budget: Rs. {result['monthly_budget']:,.2f}")
    print(f"Remaining budget: Rs. {result['remaining_budget']:,.2f}")
    print(f"Budget used: {result['budget_used_percentage']:.1f}%")
    print(f"Transactions: {result['transaction_count']}")
    print("\nGenerated PNG files:")

    for chart_name, chart_path in result["charts"].items():
        exists = Path(chart_path).is_file()
        print(f"  {chart_name}: {chart_path} | exists={exists}")


if __name__ == "__main__":
    main()
