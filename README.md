# Python Project: Personal-Finance

Work split :
1. Gauresh - Streamlit
2. Jonathan - Graphs and Visualization
3. Abdullah - SQL & Back to Front Integration
4. Abhiram - General / Little bit of everything

## Run the app

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. Replace `auth_cookie_key` with a long random secret.
3. Start the app:

```bash
streamlit run app.py
```

The app creates `users.db` automatically. Users can sign up with a username
and password from the login page. Successful logins are remembered for 30 days.
