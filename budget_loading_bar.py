from pathlib import Path

import matplotlib.pyplot as plt

from chart_theme import (
    BACKGROUND_COLOR,
    EXPENSE_COLOR,
    MUTED_TEXT_COLOR,
    SURFACE_COLOR,
    TEXT_COLOR,
)


def generate_budget_loading_bar(
    total_expenses,
    monthly_budget,
    output_folder,
):
    """Create a budget-usage bar or an empty placeholder if no budget is set."""

    total_expenses = float(total_expenses)
    monthly_budget = float(monthly_budget)
    budget_is_set = monthly_budget > 0
    percentage_used = (
        (total_expenses / monthly_budget) * 100 if budget_is_set else None
    )
    displayed_percentage = min(percentage_used, 100) if budget_is_set else 0
    remaining_amount = monthly_budget - total_expenses if budget_is_set else None

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    image_name = (
        "monthly_budget_progress.png"
        if budget_is_set
        else "monthly_budget_progress_placeholder.png"
    )
    image_path = output_folder / image_name

    fig, ax = plt.subplots(figsize=(10, 1.2))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    # Transparent complete bar with a visible border.
    ax.barh(
        0,
        100,
        height=0.48,
        facecolor="none",
        edgecolor=MUTED_TEXT_COLOR,
        linewidth=2.5,
        zorder=1,
    )

    if budget_is_set:
        ax.barh(
            0,
            displayed_percentage,
            height=0.48,
            color=EXPENSE_COLOR,
            edgecolor="none",
            zorder=2,
        )

    # Redraw the border above the filled section.
    ax.barh(
        0,
        100,
        height=0.48,
        facecolor="none",
        edgecolor=MUTED_TEXT_COLOR,
        linewidth=2.5,
        zorder=3,
    )

    if budget_is_set and displayed_percentage >= 25:
        label_x = displayed_percentage / 2
        label_color = TEXT_COLOR
        alignment = "center"
        label = f"{percentage_used:.1f}% used"
    elif budget_is_set:
        label_x = displayed_percentage + 3
        label_color = TEXT_COLOR
        alignment = "left"
        label = f"{percentage_used:.1f}% used"
    else:
        label_x = 50
        label_color = TEXT_COLOR
        alignment = "center"
        label = "Budget for this month has not been set"

    ax.text(
        label_x,
        0,
        label,
        ha=alignment,
        va="center",
        fontsize=13,
        fontweight="bold",
        color=label_color,
        zorder=4,
    )

    ax.set_xlim(-1, 101)
    ax.set_ylim(-0.35, 0.35)
    ax.axis("off")

    fig.tight_layout()
    fig.savefig(
        image_path,
        dpi=150,
        bbox_inches="tight",
        facecolor=BACKGROUND_COLOR,
        transparent=False,
        pad_inches=0.05,
    )
    plt.close(fig)

    return {
        "path": str(image_path),
        "percentage_used": percentage_used,
        "remaining_amount": remaining_amount,
    }
