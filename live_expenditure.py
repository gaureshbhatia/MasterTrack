from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from database import get_current_month_expenses


def get_month_range():
    now = datetime.now()

    month_start = datetime(
        now.year,
        now.month,
        1
    )

    if now.month == 12:
        next_month_start = datetime(
            now.year + 1,
            1,
            1
        )
    else:
        next_month_start = datetime(
            now.year,
            now.month + 1,
            1
        )

    return now, month_start, next_month_start


def generate_live_expenditure_graph(
    user_id,
    username
):
    """
    Generate the cumulative expenditure graph
    for the authenticated user for the current month.
    """

    now, month_start, next_month_start = get_month_range()

    # Get current-month expenses from database.py
    transactions = get_current_month_expenses(
        user_id,
        month_start,
        next_month_start
    )

    # Create every day from the 1st until today
    daily_expenses = {
        day: 0.0
        for day in range(1, now.day + 1)
    }

    # Process expense transactions
    for created_at, category_name, amount in transactions:

        # SQLite may return the date as a string
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(
                created_at
            )

        # Ignore accidentally future-dated transactions
        if created_at.date() <= now.date():
            daily_expenses[created_at.day] += float(
                amount
            )

    days = list(
        daily_expenses.keys()
    )

    daily_amounts = list(
        daily_expenses.values()
    )

    # Calculate cumulative expenditure
    cumulative_amounts = []

    running_total = 0.0

    for daily_amount in daily_amounts:

        running_total += daily_amount

        cumulative_amounts.append(
            running_total
        )

    # Create graph output folder
    graph_folder = (
        Path("graphs")
        / username
        / now.strftime("%Y-%m")
    )

    graph_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    graph_path = (
        graph_folder
        / "live_monthly_expenditure.png"
    )

    # --------------------------------------------------
    # CREATE GRAPH
    # --------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(11, 6),
        facecolor="#F4F7FB"
    )

    ax.set_facecolor(
        "#F4F7FB"
    )

    ax.plot(
        days,
        cumulative_amounts,
        color="#6C5CE7",
        linewidth=3,
        marker="o",
        markersize=6,
        markerfacecolor="#FFD166",
        markeredgecolor="#6C5CE7"
    )

    ax.fill_between(
        days,
        cumulative_amounts,
        color="#A29BFE",
        alpha=0.30
    )

    ax.set_title(
        f"Live Expenditure — {now.strftime('%B %Y')}",
        fontsize=18,
        fontweight="bold",
        pad=15
    )

    ax.set_xlabel(
        "Day of the Month"
    )

    ax.set_ylabel(
        "Total Expenditure Till Date"
    )

    ax.set_xticks(days)

    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(
            lambda value, position:
            f"₹{value:,.0f}"
        )
    )

    ax.grid(
        linestyle="--",
        alpha=0.30
    )

    ax.spines["top"].set_visible(
        False
    )

    ax.spines["right"].set_visible(
        False
    )

    # Display final expenditure value
    if running_total > 0:

        ax.annotate(
            f"₹{running_total:,.0f}",
            xy=(
                days[-1],
                cumulative_amounts[-1]
            ),
            xytext=(-50, 20),
            textcoords="offset points",
            fontsize=11,
            fontweight="bold",
            color="#6C5CE7",
            arrowprops={
                "arrowstyle": "->",
                "color": "#6C5CE7"
            }
        )

    fig.tight_layout()

    fig.savefig(
        graph_path,
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )

    plt.close(fig)

    return {
        "graph_path": str(graph_path),
        "month": now.strftime("%B %Y"),
        "up_to_date": now.strftime("%d-%m-%Y"),
        "total_expenditure": running_total
    }