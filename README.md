# Python Project: Personal-Finance

Work split :
1. Gauresh - Streamlit
2. Jonathan - Graphs and Visualization
3. Abdullah - SQL & Back to Front Integration
4. Abhiram - General / Little bit of everything

## Run the app

1. Install and start MySQL on Ubuntu/Debian:

```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl enable --now mysql
```

2. Create the application database and user:

```bash
sudo mysql
```

Run this SQL in the MySQL prompt, replacing `choose_a_password` with a real
password:

```sql
CREATE DATABASE personal_finance;
CREATE USER 'finance_app'@'localhost' IDENTIFIED BY 'choose_a_password';
GRANT ALL PRIVILEGES ON personal_finance.* TO 'finance_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

3. Update `.streamlit/secrets.toml` with the same MySQL credentials:

```toml
[mysql]
host = "localhost"
port = 3306
database = "personal_finance"
user = "finance_app"
password = "choose_a_password"
```

4. Install the Python dependencies:

```bash
pip install -r requirements.txt
```

5. Start the app:

```bash
streamlit run app.py
```

The app creates the MySQL `users` table automatically and seeds a `test` user
with the password `password`. Users can sign up with a username and password
from the login page. Successful logins are remembered for 30 days.

The previous SQLite `users.db` file is no longer used, and its data is not
migrated.
