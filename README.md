# Python Project: Personal-Finance

Work split :
1. Gauresh - Streamlit
2. Jonathan - Graphs and Visualization
3. Abdullah - SQL & Back to Front Integration
4. Abhiram - General / Little bit of everything

## Run the app

1. Install the Python dependencies:

```bash
pip install -r requirements.txt
```

2. Start the app:

```bash
streamlit run app.py
```

The app creates a local SQLite `users.db` database with the `users`,
`expense_categories`, and `expenses` tables automatically. It seeds a `test`
user with the password `password` and these
stable expense category mappings:

| Category ID | Category name |
| --- | --- |
| 1 | Type 1 |
| 2 | Type 2 |
| 3 | Type 3 |
| 4 | Type 4 |

Users can sign up with a username and password from the login page. Successful
logins are remembered for 30 days. After logging in, users can save positive
INR expenses with up to two decimal places. Each expense stores the logged-in
user ID and category ID, while the `expense_categories` table explains which
category name each ID represents. The authenticated main page shows the
user's expenses for the current calendar month; broader history and
visualizations will be added later.

Each user also has a separate monthly budget. A new calendar month starts
with an unset budget represented internally by `-1`; the app asks whether to
set a budget. A saved budget can be zero or greater and can be updated during
the month. The month reset occurs when the user first opens the app in the
new month, using the server's local date and time.

The database file is local to the project and is ignored by Git. Delete
`users.db` to reset all local users, expenses, and budgets; it will be recreated
with the default schema and test user the next time the app starts. Existing
MySQL data is not migrated.
