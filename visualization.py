from pathlib import Path
import matplotlib.pyplot as plt


def generate_charts():
    output_folder = Path("charts")
    output_folder.mkdir(exist_ok=True)

    # Sample data for testing
    categories = ["Food", "Travel", "Shopping", "Bills"]
    expenses = [3500, 1200, 2500, 4000]

    income = 30000
    total_expenses = sum(expenses)

    days = [1, 5, 10, 15, 20, 25, 30]
    daily_expenses = [200, 450, 300, 800, 250, 600, 400]

    # Pie chart
    fig, ax = plt.subplots()
    ax.pie(expenses, labels=categories, autopct="%1.1f%%")
    ax.set_title("Expenses by Category")
    pie_path = output_folder / "category_expenses.png"
    fig.savefig(pie_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Bar chart
    fig, ax = plt.subplots()
    ax.bar(
        ["Income", "Expenses"],
        [income, total_expenses],
        color=["green", "red"]
    )
    ax.set_title("Income vs Expenses")
    ax.set_ylabel("Amount")
    bar_path = output_folder / "income_vs_expenses.png"
    fig.savefig(bar_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Line graph
    fig, ax = plt.subplots()
    ax.plot(days, daily_expenses, marker="o")
    ax.set_title("Daily Spending")
    ax.set_xlabel("Day of the Month")
    ax.set_ylabel("Amount Spent")
    line_path = output_folder / "daily_spending.png"
    fig.savefig(line_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "pie": str(pie_path),
        "bar": str(bar_path),
        "line": str(line_path),
    }


if __name__ == "__main__":
    print(generate_charts())