from pathlib import Path

import matplotlib.pyplot as plt


def generate_budget_loading_bar(
    total_expenses,
    monthly_budget,
    output_folder,
):
    """Create a transparent, bordered budget-usage bar and return its PNG path."""

    total_expenses = float(total_expenses)
    monthly_budget = float(monthly_budget)

    # In database.py, -1 means that no budget has been set.
    if monthly_budget <= 0:
        return None

    percentage_used = (total_expenses / monthly_budget) * 100
    displayed_percentage = min(percentage_used, 100)
    remaining_amount = monthly_budget - total_expenses

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    image_path = output_folder / "monthly_budget_progress.png"

    fig, ax = plt.subplots(figsize=(10, 1.2))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    # Transparent complete bar with a visible border.
    ax.barh(
        0,
        100,
        height=0.48,
        facecolor="none",
        edgecolor="#263238",
        linewidth=2.5,
        zorder=1,
    )

    # Red section indicates the percentage of budget already used.
    ax.barh(
        0,
        displayed_percentage,
        height=0.48,
        color="#E53935",
        edgecolor="none",
        zorder=2,
    )

    # Redraw the border above the filled section.
    ax.barh(
        0,
        100,
        height=0.48,
        facecolor="none",
        edgecolor="#263238",
        linewidth=2.5,
        zorder=3,
    )

    if displayed_percentage >= 25:
        label_x = displayed_percentage / 2
        label_color = "white"
        alignment = "center"
    else:
        label_x = displayed_percentage + 3
        label_color = "#263238"
        alignment = "left"

    ax.text(
        label_x,
        0,
        f"{percentage_used:.1f}% used",
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
        transparent=True,
        pad_inches=0.05,
    )
    plt.close(fig)

    return {
        "path": str(image_path),
        "percentage_used": percentage_used,
        "remaining_amount": remaining_amount,
    }
