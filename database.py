import sqlite3

CREATE_TABLE = "CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, password TEXT, name TEXT, balance REAL)"
INSERT_ACCOUNT = "INSERT INTO accounts (password, name, balance) VALUES (?, ?, ?)"

CHECK_BALANCE = "SELECT balance FROM accounts WHERE id = ?"
GET_LAST_INDEX = "SELECT id FROM accounts ORDER BY id DESC LIMIT 1"
CHECK_ID_EXISTS = "SELECT EXISTS(SELECT 1 FROM accounts WHERE id = ?);"
GET_PASSWORD = "SELECT password FROM accounts WHERE id = ?;"

UPDATE_BALANCE = "UPDATE accounts SET balance = (SELECT balance FROM accounts WHERE id = ?) + ? WHERE id = ?"


def connect():
    return sqlite3.connect("data.db")


def create_table(connection):
    with connection:
        connection.execute(CREATE_TABLE)


def add_account(connection, password, name):
    with connection:
        connection.execute(INSERT_ACCOUNT, (password, name, 0))
        return connection.execute(GET_LAST_INDEX).fetchone()[0]


def check_balance_database(connection, account_number):
    with connection:
        return connection.execute(CHECK_BALANCE, (account_number, )).fetchone()[0]


def withdraw_database(connection, account_number, amount):
    with connection:
        connection.execute(UPDATE_BALANCE, (account_number, -amount, account_number))


def deposit_database(connection, account_number, amount):
    with connection:
        connection.execute(UPDATE_BALANCE, (account_number, amount, account_number))


def is_id_exists(connection, account_number):
    with connection:
        return connection.execute(CHECK_ID_EXISTS, (account_number, )).fetchone()[0] == 1


def get_account_password(connection, account_number):
    with connection:
        return connection.execute(GET_PASSWORD, (account_number, )).fetchone()[0]


def show_all(connection):
    with connection:
        print(connection.execute("SELECT * FROM accounts").fetchall())

