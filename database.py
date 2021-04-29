import sqlite3

CREATE_TABLE = "CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, name TEXT, balance REAL)"
INSERT_ACCOUNT = "INSERT INTO accounts (name, balance) VALUES (?, ?)"

CHECK_BALANCE = "SELECT balance FROM accounts WHERE id = ?"
UPDATE_BALANCE = "UPDATE accounts SET balance = (SELECT balance FROM accounts WHERE id = ?) + ? WHERE id = ?"


def connect():
    return sqlite3.connect("data.db")


def create_table(connection):
    with connection:
        connection.execute(CREATE_TABLE)


def add_account(connection, name):
    with connection:
        connection.execute(INSERT_ACCOUNT, (name, 0))


def check_balance_database(connection, account_number):
    with connection:
        return connection.execute(CHECK_BALANCE, (account_number, )).fetchone()[0]


def withdraw_database(connection, account_number, amount):
    with connection:
        connection.execute(UPDATE_BALANCE, (account_number, -amount, account_number))


def deposit_database(connection, account_number, amount):
    with connection:
        connection.execute(UPDATE_BALANCE, (account_number, amount, account_number))


