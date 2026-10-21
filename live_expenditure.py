from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from chart_theme import (
    BACKGROUND_COLOR,
    GRID_COLOR,
    MUTED_TEXT_COLOR,
    PRIMARY_COLOR,
    SURFACE_COLOR,
    TEXT_COLOR,
)


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

    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BACKGROUND_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    ax.plot(
        days,
        cumulative_expenses,
        color=PRIMARY_COLOR,
        linewidth=3,
        marker="o",
        markersize=6,
        markerfacecolor="#EF4444",
        markeredgecolor=BACKGROUND_COLOR,
    )

    ax.fill_between(
        days,
        cumulative_expenses,
        color=PRIMARY_COLOR,
        alpha=0.22,
    )

    ax.set_title(
        f"Live Expenditure — {current_date.strftime('%B %Y')}",
        fontsize=17,
        fontweight="bold",
        color=TEXT_COLOR,
        pad=18,
    )
    ax.set_xlabel("Day of the Month", color=TEXT_COLOR)
    ax.set_ylabel("Cumulative Expenditure", color=TEXT_COLOR)
    ax.tick_params(colors=TEXT_COLOR)
    ax.set_xticks(days)

    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda value, _position: f"₹{value:,.0f}")
    )

    ax.grid(linestyle="--", color=GRID_COLOR, alpha=0.55)
    for spine in ax.spines.values():
        spine.set_color(MUTED_TEXT_COLOR)

    if running_total > 0:
        ax.annotate(
            f"₹{running_total:,.0f}",
            xy=(days[-1], cumulative_expenses[-1]),
            xytext=(-55, 20),
            textcoords="offset points",
            fontweight="bold",
            color=PRIMARY_COLOR,
            arrowprops={
                "arrowstyle": "->",
                "color": PRIMARY_COLOR,
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
