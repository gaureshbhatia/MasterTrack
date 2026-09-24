from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def _as_datetime(value):
    """Convert an SQLite timestamp value into a datetime object."""

    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(str(value))


def generate_live_expenditure_graph(
    transactions,
    current_date,
    output_folder,
):
    """Create a cumulative expense graph from month start through today."""

    daily_totals = defaultdict(float)

    for created_at, _category_name, amount in transactions:
        transaction_date = _as_datetime(created_at)

        # Exclude any accidentally future-dated transaction.
        if transaction_date.date() <= current_date.date():
            daily_totals[transaction_date.day] += float(amount)

    days = list(range(1, current_date.day + 1))
    cumulative_expenses = []
    running_total = 0.0

    for day in days:
        running_total += daily_totals.get(day, 0.0)
        cumulative_expenses.append(running_total)

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    image_path = output_folder / "live_monthly_expenditure.png"

    fig, ax = plt.subplots(figsize=(11, 6), facecolor="#F7F9FC")
    ax.set_facecolor("#F7F9FC")

    ax.plot(
        days,
        cumulative_expenses,
        color="#6A4C93",
        linewidth=3,
        marker="o",
        markersize=6,
        markerfacecolor="#FFCA3A",
        markeredgecolor="#6A4C93",
    )

    ax.fill_between(
        days,
        cumulative_expenses,
        color="#B8A1D9",
        alpha=0.35,
    )

    ax.set_title(
        f"Live Expenditure — {current_date.strftime('%B %Y')}",
        fontsize=17,
        fontweight="bold",
        pad=18,
    )
    ax.set_xlabel("Day of the Month")
    ax.set_ylabel("Cumulative Expenditure")
    ax.set_xticks(days)

    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda value, _position: f"₹{value:,.0f}")
    )

    ax.grid(linestyle="--", alpha=0.30)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if running_total > 0:
        ax.annotate(
            f"₹{running_total:,.0f}",
            xy=(days[-1], cumulative_expenses[-1]),
            xytext=(-55, 20),
            textcoords="offset points",
            fontweight="bold",
            color="#6A4C93",
            arrowprops={
                "arrowstyle": "->",
                "color": "#6A4C93",
            },
        )

    fig.tight_layout()
    fig.savefig(
        image_path,
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)

    return {
        "path": str(image_path),
        "total_expenses": running_total,
    }
