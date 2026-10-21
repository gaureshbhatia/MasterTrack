from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from budget_loading_bar import generate_budget_loading_bar
from database import get_current_month_budget, get_current_month_expenses
from live_expenditure import generate_live_expenditure_graph


CURRENT_SESSION_CHARTS_FOLDER = Path("charts") / "current session"
PLACEHOLDER_CHARTS_FOLDER = Path("charts") / "visualization_test_user"


def get_month_range(current_date=None):
    """Return now, the first day of this month, and the first day of next month."""

    current_date = current_date or datetime.now()
    month_start = datetime(current_date.year, current_date.month, 1)

    if current_date.month == 12:
        next_month_start = datetime(current_date.year + 1, 1, 1)
    else:
        next_month_start = datetime(
            current_date.year,
            current_date.month + 1,
            1,
        )

    return current_date, month_start, next_month_start


def _as_datetime(value):
    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(str(value))


def _current_transactions(transactions, current_date):
    """Remove any accidentally future-dated rows from the current-month data."""

    return [
        transaction
        for transaction in transactions
        if _as_datetime(transaction[0]).date() <= current_date.date()
    ]


def generate_category_pie_chart(
    transactions,
    output_folder,
):
    category_totals = defaultdict(float)

    for _created_at, category_name, amount in transactions:
        category_totals[category_name] += float(amount)

    if not category_totals:
        return None

    categories = list(category_totals.keys())
    expenses = list(category_totals.values())
    total_expenses = sum(expenses)

    colors = [
        "#FF595E",
        "#FFCA3A",
        "#8AC926",
        "#1982C4",
        "#6A4C93",
        "#FF70A6",
        "#00B4D8",
        "#F77F00",
    ]

    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#F7F9FC")

    ax.pie(
        expenses,
        labels=categories,
        colors=[colors[index % len(colors)] for index in range(len(categories))],
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.78,
        wedgeprops={
            "edgecolor": "white",
            "linewidth": 2,
        },
    )

    centre_circle = plt.Circle((0, 0), 0.50, color="#F7F9FC")
    ax.add_artist(centre_circle)

    ax.text(
        0,
        0,
        f"₹{total_expenses:,.0f}",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color="#333333",
    )

    ax.set_title(
        "Expenses by Category",
        fontsize=17,
        fontweight="bold",
        pad=18,
    )

    image_path = Path(output_folder) / "category_expenses.png"
    fig.savefig(
        image_path,
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)

    return str(image_path)


def generate_budget_comparison_chart(
    total_expenses,
    monthly_budget,
    output_folder,
):
    """Generate a standard bar chart comparing the budget with spending."""

    if monthly_budget <= 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#F7F9FC")

    labels = ["Monthly Budget", "Spent Till Date"]
    values = [monthly_budget, total_expenses]

    bars = ax.bar(
        labels,
        values,
        color=["#1982C4", "#FF595E"],
        width=0.55,
        edgecolor="white",
        linewidth=2,
    )

    ax.bar_label(
        bars,
        labels=[f"₹{value:,.0f}" for value in values],
        padding=5,
        fontweight="bold",
    )

    ax.set_title(
        "Monthly Budget vs Expenditure",
        fontsize=17,
        fontweight="bold",
        pad=18,
    )
    ax.set_ylabel("Amount")
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda value, _position: f"₹{value:,.0f}")
    )
    ax.grid(axis="y", linestyle="--", alpha=0.30)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    image_path = Path(output_folder) / "budget_vs_expenditure.png"
    fig.savefig(
        image_path,
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)

    return str(image_path)


def generate_charts(user_id, username):
    """Fetch SQLite values and return every generated PNG path to the frontend."""

    current_date, month_start, next_month_start = get_month_range()

    transactions = get_current_month_expenses(
        user_id,
        month_start,
        next_month_start,
    )
    transactions = _current_transactions(transactions, current_date)

    monthly_budget = float(
        get_current_month_budget(user_id, month_start)
    )

    total_expenses = sum(
        float(amount)
        for _created_at, _category_name, amount in transactions
    )

    output_folder = CURRENT_SESSION_CHARTS_FOLDER
    output_folder.mkdir(parents=True, exist_ok=True)

    chart_paths = {}

    pie_path = generate_category_pie_chart(
        transactions,
        output_folder,
    )
    if pie_path is not None:
        chart_paths["pie"] = pie_path

    comparison_path = generate_budget_comparison_chart(
        total_expenses,
        monthly_budget,
        output_folder,
    )
    if comparison_path is not None:
        chart_paths["bar"] = comparison_path

    live_result = generate_live_expenditure_graph(
        transactions,
        current_date,
        output_folder,
    )
    chart_paths["line"] = live_result["path"]

    loading_result = generate_budget_loading_bar(
        total_expenses,
        monthly_budget,
        output_folder,
    )
    if loading_result is not None:
        chart_paths["progress"] = loading_result["path"]

    if monthly_budget >= 0:
        remaining_budget = monthly_budget - total_expenses
    else:
        remaining_budget = None

    if monthly_budget > 0:
        budget_used_percentage = (
            total_expenses / monthly_budget
        ) * 100
    else:
        budget_used_percentage = None

    return {
        "charts": chart_paths,
        "total_expenses": total_expenses,
        "monthly_budget": monthly_budget,
        "remaining_budget": remaining_budget,
        "budget_used_percentage": budget_used_percentage,
        "up_to_date": current_date.strftime("%d-%m-%Y"),
        "transaction_count": len(transactions),
    }
