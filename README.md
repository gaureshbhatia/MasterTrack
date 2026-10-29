# MasterTrack: Personal Finance Tracker

MasterTrack is a personal finance web app built with **Python**, **Streamlit** and **SQLite3**. Users create an account, set a monthly budget, log their daily expenses in INR, and see how much of the budget they have spent through a progress bar and charts.

## Team and Work Split

| Member | Responsibility |
| --- | --- |
| Gauresh | Streamlit (front end) |
| Jonathan | Graphs and visualization |
| Abdullah | SQL and back-end to front-end integration |
| Abhiram | General support, a little bit of everything |

## Features

- **Sign up and log in**: accounts are stored in the local database with hashed passwords, and logins are remembered for 30 days using a cookie.
- **Monthly budget**: set or update a budget for the current calendar month. A new month starts with no budget set, and the app asks the user to set one.
- **Expense tracking**: save expenses in INR (positive amounts, up to two decimal places) under one of 11 categories.
- **Monthly spending view**: a table of the current calendar month's expenses, newest first.
- **Budget progress bar**: an image showing how much of the monthly budget has been spent.
- **Data visualization**: line, bar and pie charts, shown once a budget is set and at least one expense exists. Placeholder images are shown until then.
- **Clear my spending data**: deletes the user's own expenses and budgets (with a confirmation step) without deleting the account.
- **Per-user data**: every user sees only their own expenses and budgets.

### Expense Categories

Food, Transport, Housing, Utilities, Education, Healthcare, Shopping, Entertainment, Travel, EMI/Loans, Misc

## Tech Stack

| Layer | Technology |
| --- | --- |
| Front end | [Streamlit](https://streamlit.io/) |
| Authentication | [streamlit-authenticator](https://github.com/mkhorasani/Streamlit-Authenticator) |
| Back end | Python 3 |
| Database | SQLite3 (built into Python) |
| Charts | Python visualization module (`visualization.py`, `budget_loading_bar.py`) |

## Project Structure

```
.
├── app.py                  # Streamlit app: login, signup, budget, expenses, charts
├── database.py             # SQLite connection, table creation and all queries
├── genkeys.py              # User sign-up logic (also a command-line tool to create users)
├── visualization.py        # Generates the line, bar and pie charts
├── budget_loading_bar.py   # Generates the budget progress bar image
├── requirements.txt        # Python dependencies
├── charts/                 # Generated chart images and placeholder images
├── .streamlit/secrets.toml # Auto-generated cookie key (not committed)
└── users.db                # Local SQLite database (auto-created, not committed)
```

## Database Schema

The app creates `users.db` automatically on first run with these tables:

| Table | Columns | Purpose |
| --- | --- | --- |
| `users` | `id`, `username` (unique), `password_hash` | Registered accounts |
| `expense_categories` | `id`, `name` (unique) | The 11 fixed expense categories |
| `expenses` | `id`, `user_id`, `amount`, `category_id`, `created_at` | One row per expense |
| `budgets` | `id`, `user_id`, `amount`, `month`, `year` | One budget per user per month |

Foreign keys are enabled. Deleting a user cascades to their expenses and budgets. Older category names (such as `Type 1` to `Type 4`, `Edu` and `Housing/Maintenance`) are migrated to the current categories automatically.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/gaureshbhatia/Python-Project-Personal-Finance.git
cd Python-Project-Personal-Finance
```

### 2. Install the dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

Open the local URL that Streamlit prints (usually `http://localhost:8501`), click **Create account**, and log in.

On first run the app creates the database and generates a secure cookie key in `.streamlit/secrets.toml`. No manual setup is needed.

### Optional: create a user from the terminal

```bash
python genkeys.py
```

This asks for a username and password (hidden while typing) and adds the user to the database.

## How It Works

1. **Startup**: `initialize_database()` creates the tables and seeds the categories. The saved users are loaded into `streamlit-authenticator`.
2. **Login**: the user logs in and the session is remembered through a cookie for 30 days.
3. **Budget**: a month with no budget is stored internally as `-1`, which triggers the "set a budget" prompt. A saved budget can be `0` or higher and can be updated any time during the month.
4. **Expenses**: the amount is validated with Python's `Decimal` and saved with the user ID and category ID.
5. **Monthly view**: expenses are filtered by calendar-month boundaries (not a rolling 30 days). The month resets the first time the user opens the app in a new month, based on the server's local date and time.
6. **Charts**: images are generated into `charts/current session/` and deleted when the user logs out. Placeholder images from `charts/visualization_test_user/` are shown when there is not enough data.

## Resetting the Data

`users.db` is local to the project and ignored by Git. To reset all users, expenses and budgets, delete `users.db`. It is recreated with the default schema the next time the app starts. Data from the earlier MySQL version is not migrated.

## Future Improvements

- Income tracking alongside expenses
- Editing and deleting individual expenses
- Viewing spending history for previous months
- Exporting data to CSV
- Custom expense categories

## Authors

Gauresh, Jonathan, Abdullah and Abhiram
