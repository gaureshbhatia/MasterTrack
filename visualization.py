from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from database import (
    get_current_month_budget,
    get_current_month_expenses,
)
from live_expenditure import generate_live_expenditure_graph


def get_month_range():
    """Return the current time, beginning of this month, and beginning of next month."""

    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    if now.month == 12:
        next_month_start = datetime(now.year + 1, 1, 1)
    else:
        next_month_start = datetime(now.year, now.month + 1, 1)

    return now, month_start, next_month_start


def generate_charts(user_id, username):
    """
    Retrieve the authenticated user's current-month data,
    generate separate PNG charts, and return their paths.
    """

    now, month_start, next_month_start = get_month_range()

    # --------------------------------------------------
    # GET CURRENT-MONTH DATA FROM SQLITE DATABASE
    # --------------------------------------------------

    transactions = get_current_month_expenses(
        user_id,
        month_start,
        next_month_start
    )

    monthly_budget = get_current_month_budget(
        user_id,
        month_start
    )

    monthly_budget = float(monthly_budget)

    # --------------------------------------------------
    # CREATE USER-SPECIFIC OUTPUT FOLDER
    # --------------------------------------------------

    output_folder = (
        Path("charts")
        / username
        / now.strftime("%Y-%m")
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # PROCESS TRANSACTION DATA
    # --------------------------------------------------

    category_totals = defaultdict(float)
    daily_totals = defaultdict(float)
    total_expenses = 0.0

    for created_at, category_name, amount in transactions:

        amount = float(amount)

        # SQLite may return DATETIME as a string
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Ignore accidentally future-dated transactions
        if created_at.date() <= now.date():

            category_totals[category_name] += amount
            daily_totals[created_at.day] += amount
            total_expenses += amount

    chart_paths = {}

    # ==================================================
    # 1. CATEGORY-WISE EXPENSE DOUGHNUT CHART
    # ==================================================

    if category_totals:

        categories = list(category_totals.keys())
        expenses = list(category_totals.values())

        colors = [
            "#FF595E",
            "#FFCA3A",
            "#8AC926",
            "#1982C4",
            "#6A4C93",
            "#FF70A6",
            "#00B4D8",
            "#F77F00"
        ]

        fig, ax = plt.subplots(
            figsize=(8, 6),
            facecolor="#F7F9FC"
        )

        ax.pie(
            expenses,
            labels=categories,
            colors=colors[:len(categories)],
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.78,
            wedgeprops={
                "edgecolor": "white",
                "linewidth": 2
            }
        )

        # Doughnut-chart centre
        centre_circle = plt.Circle(
            (0, 0),
            0.50,
            color="#F7F9FC"
        )

        ax.add_artist(centre_circle)

        ax.text(
            0,
            0,
            f"₹{total_expenses:,.0f}",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=15,
            fontweight="bold",
            color="#333333"
        )

        ax.set_title(
            "Expenses by Category",
            fontsize=17,
            fontweight="bold",
            pad=18
        )

        pie_path = output_folder / "category_expenses.png"

        fig.savefig(
            pie_path,
            dpi=150,
            bbox_inches="tight",
            facecolor=fig.get_facecolor()
        )

        plt.close(fig)

        chart_paths["pie"] = str(pie_path)

    # ==================================================
    # 2. MONTHLY BUDGET VS EXPENDITURE BAR CHART
    # ==================================================

    # A budget of -1 means the user has not set a budget
    if monthly_budget >= 0:

        fig, ax = plt.subplots(
            figsize=(8, 6),
            facecolor="#F7F9FC"
        )

        labels = [
            "Monthly Budget",
            "Spent Till Date"
        ]

        values = [
            monthly_budget,
            total_expenses
        ]

        bars = ax.bar(
            labels,
            values,
            color=[
                "#00B894",
                "#FF595E"
            ],
            width=0.55,
            edgecolor="white",
            linewidth=2
        )

        ax.bar_label(
            bars,
            labels=[
                f"₹{monthly_budget:,.0f}",
                f"₹{total_expenses:,.0f}"
            ],
            padding=5,
            fontweight="bold"
        )

        ax.set_title(
            "Monthly Budget vs Expenditure",
            fontsize=17,
            fontweight="bold",
            pad=18
        )

        ax.set_ylabel("Amount")

        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(
                lambda value, position: f"₹{value:,.0f}"
            )
        )

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.30
        )

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        bar_path = (
            output_folder
            / "budget_vs_expenditure.png"
        )

        fig.savefig(
            bar_path,
            dpi=150,
            bbox_inches="tight",
            facecolor=fig.get_facecolor()
        )

        plt.close(fig)

        chart_paths["bar"] = str(bar_path)

    # ==================================================
    
    # ==================================================
    # CALCULATE BUDGET SUMMARY
    # ==================================================

    remaining_budget = None
    budget_used_percentage = None

    if monthly_budget >= 0:

        remaining_budget = (
            monthly_budget
            - total_expenses
        )

        if monthly_budget > 0:

            budget_used_percentage = (
                total_expenses
                / monthly_budget
            ) * 100

    # ==================================================
    # RETURN DATA TO FRONTEND
    # ==================================================

    return {
        "charts": chart_paths,
        "total_expenses": total_expenses,
        "monthly_budget": monthly_budget,
        "remaining_budget": remaining_budget,
        "budget_used_percentage": budget_used_percentage,
        "up_to_date": now.strftime("%d-%m-%Y"),
        "transaction_count": len(transactions)
    }