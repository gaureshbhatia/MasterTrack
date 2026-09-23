from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generate_budget_loading_bar(
    total_expenses,
    monthly_budget,
    output_path
):
    """
    Generate a budget usage loading bar.

    Red portion = percentage of monthly budget spent.
    Transparent portion = remaining budget.
    """

    total_expenses = float(total_expenses)
    monthly_budget = float(monthly_budget)

    # Calculate percentage of budget used
    if monthly_budget > 0:
        percentage_used = (
            total_expenses / monthly_budget
        ) * 100
    else:
        percentage_used = 0

    # The visual bar should not extend beyond 100%
    display_percentage = min(
        max(percentage_used, 0),
        100
    )

    # Make sure output folder exists
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Create figure
    fig, ax = plt.subplots(
        figsize=(8, 1)
    )

    # Transparent background
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    # --------------------------------------------------
    # RED SPENT PORTION
    # --------------------------------------------------

    spent_bar = Rectangle(
        (0, 0),
        display_percentage,
        1,
        facecolor="red",
        edgecolor="none"
    )

    ax.add_patch(spent_bar)

    # --------------------------------------------------
    # OUTER BORDER
    # --------------------------------------------------

    border = Rectangle(
        (0, 0),
        100,
        1,
        facecolor="none",
        edgecolor="black",
        linewidth=2
    )

    ax.add_patch(border)

    # --------------------------------------------------
    # GRAPH SETTINGS
    # --------------------------------------------------

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1)

    ax.axis("off")

    # Remove extra margins
    fig.subplots_adjust(
        left=0,
        right=1,
        top=1,
        bottom=0
    )

    # --------------------------------------------------
    # SAVE PNG
    # --------------------------------------------------

    fig.savefig(
        output_path,
        dpi=150,
        transparent=True,
        bbox_inches="tight",
        pad_inches=0
    )

    plt.close(fig)

    return str(output_path)