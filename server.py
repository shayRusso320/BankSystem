import socket
import select
from msg import *
from database import *
import json
import math

SERVER_IP = '127.0.0.1'
PORT = 5000
DATABASE = "data.db"

INVALID_INPUT = "invalid input"
MISSING_COMPONENTS = "not all components exist in message"
UNMATCHING_PASSWORDS = "password doesn't match with password in DB"
ACCOUNT_NOT_FOUND = "account is not found"
UNMATCHING_PARAMETERS = "PARAMETERS DON'T MATCH FUNCTION"

SUCCESSFUL_SIGNIN = "Signed in Successfully"
COMPLETED_TRANSACTION = "TRANSACTION COMPLETED SUCCESSFULLY"


class Server:
    def __init__(self):
        self.serv = Server.upload_server()  # create the server socket
        self.atms = []
        self.messages_to_send = []
        self.data = connect()
        create_table(self.data)

    # ------ SERVER FUNCTIONS ------
    @staticmethod
    def main():
        server = Server()

        while True:
            rlist, wlist, xlist = select.select([server.serv] + server.atms, server.atms, [])

            for sender_socket in rlist:

                # if receiving a new connection
                if sender_socket is server.serv:
                    (new_socket, address) = sender_socket.accept()
                    server.add_ATM(new_socket)

                # handling message from ATM
                else:
                    # receiving data
                    data = ""
                    try:
                        data = sender_socket.recv(1024)
                    except ConnectionResetError or ConnectionAbortedError:
                        server.remove_ATM(sender_socket)
                        break

                    # extracting information
                    request = json.loads(data.decode())
                    opcode = request["opcode"]

                    # sign up
                    if opcode == 0:
                        try:
                            password = request["password"]
                            name = request["name"]
                        except KeyError:
                            server.add_msg(sender_socket, False, MISSING_COMPONENTS)
                            continue

                        # validating info
                        try:
                            valid_password = check_password(password)
                            valid_name = check_name(name)
                        except ValueError:
                            server.add_msg(sender_socket, False, INVALID_INPUT)
                            continue

                        if valid_password and valid_name:
                            server.open_account(sender_socket, name, password)
                        else:
                            server.add_msg(sender_socket, False, INVALID_INPUT)

                    # sign in
                    elif opcode == 1:
                        # extracting info
                        try:
                            account = request["account"]
                            password = request["password"]
                        except KeyError:
                            server.add_msg(sender_socket, False, MISSING_COMPONENTS)
                            continue

                        # validating info
                        try:
                            acc_valid = check_positive_integer(int(account))
                            password_valid = check_password(password)
                        except ValueError:
                            server.add_msg(sender_socket, False, INVALID_INPUT)
                            continue

                        if acc_valid and password_valid:
                            # matching password inserted with the stored password
                            try:
                                stored_password = get_account_password(server.data, account)
                            except TypeError:
                                server.add_msg(sender_socket, False, ACCOUNT_NOT_FOUND)
                                continue

                            if password == stored_password:
                                server.add_msg(sender_socket, True, SUCCESSFUL_SIGNIN)
                            else:
                                server.add_msg(sender_socket, False, UNMATCHING_PASSWORDS)
                        else:
                            server.add_msg(sender_socket, False, INVALID_INPUT)

                    elif opcode == 2:
                        # extracting info
                        try:
                            function = request["function"]
                        except KeyError:
                            server.add_msg(sender_socket, False, MISSING_COMPONENTS)
                            continue

                        # validating info
                        is_valid = validate_function_number(int(function))
                        if is_valid:
                            server.add_msg(sender_socket, True, Server.OPERATIONS_REQUIREMENTS[function])
                        else:
                            server.add_msg(sender_socket, False, INVALID_INPUT)

                    # execute operation
                    elif opcode == 3:
                        # extracting info
                        try:
                            account = request["account"]
                            password = request["password"]
                            function = request["function"]
                            parameters = request["parameters"]
                        except KeyError:
                            server.add_msg(sender_socket, False, MISSING_COMPONENTS)
                            continue

                        # validate info
                        try:
                            account_valid = check_positive_integer(int(account))
                            password_valid = check_password(password)
                            function_valid = validate_function_number(int(function))
                            parameters_valid = validate_operation(function, parameters)
                        except ValueError:
                            server.add_msg(sender_socket, False, INVALID_INPUT)

                        if account_valid and password_valid and function_valid and parameters_valid:
                            # test if malicious code trying to mimic the ATM client by sending hand-made packets
                            try:
                                stored_password = get_account_password(server.data, account)
                            except TypeError:
                                server.remove_ATM(sender_socket)
                                continue
                            if password != stored_password:
                                server.remove_ATM(sender_socket)
                                continue

                            if validate_operation(function, parameters):  # handling user's requests
                                server.execute_operation(function, sender_socket, account, parameters)

                            else:
                                server.add_msg(sender_socket, False, UNMATCHING_PARAMETERS)
                        else:
                            server.add_msg(sender_socket, False, INVALID_INPUT)

            server.send_waiting_messages(wlist)

    @staticmethod
    def upload_server():
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SERVER_IP, PORT))
        print("server is up")

        server_socket.listen(5)

        return server_socket

    def execute_operation(self, function, ATM_socket, account, parameters):
        return Server.OPERATIONS[function](self, ATM_socket, *([account] + parameters))

    def send_waiting_messages(self, wlist):
        for msg in self.messages_to_send:

            if msg.get_sock() in wlist:  # if the socket ready to listen
                msg.get_sock().send(msg.get_content().encode())
                self.messages_to_send.remove(msg)

    def add_msg(self, receiver, is_successful, content):
        msg = {
            "completed": is_successful,
            "content": content
        }
        new_msg = Msg(receiver, json.dumps(msg))
        self.messages_to_send.append(new_msg)

    def add_ATM(self, new_socket):
        self.atms.append(new_socket)
        print("new ATM connected")

    def remove_ATM(self, removed_socket):
        self.atms.remove(removed_socket)
        removed_socket.close()
        print("ATM disconnected")

    # ------ BANK FUNCTIONS ------

    def open_account(self, ATM_socket, name, password):
        account_number = add_account(self.data, password, name)
        self.add_msg(ATM_socket, True, f"NEW ACCOUNT IS NOW ACTIVE, YOUR ACCOUNT NUMBER IS: {account_number}")

    def check_balance(self, ATM_socket, account):
        balance = check_balance_database(self.data, account)
        self.add_msg(ATM_socket, True, f"YOUR BALANCE IS: {balance}")

    def deposit(self, ATM_socket, account, amount):
        deposit_database(self.data, account, amount)
        self.add_msg(ATM_socket, True, COMPLETED_TRANSACTION)

    def withdraw(self, ATM_socket, account, amount):
        balance = check_balance_database(self.data, account)

        if amount > balance:
            self.add_msg(ATM_socket, False, "Tried withdrawing more money than balance in account")

        else:
            withdraw_database(self.data, account, amount)
            self.add_msg(ATM_socket, True, COMPLETED_TRANSACTION)

    OPERATIONS = [check_balance, deposit, withdraw]

    # need to get rid of
    OPERATIONS_REQUIREMENTS = [
        [],
        ["amount"],
        ["amount"]
    ]


# validation function


def validate_function_number(number):
    return isinstance(number, int) and 0 <= number < len(Server.OPERATIONS)


def validate_parameters_list(response):
    if "parameters" in response:
        if isinstance(response["parameters"], list):
            return True
    return False


def check_name(name):
    return all(x.isalpha() or x.isspace() for x in name)


def check_positive_integer(num):
    return isinstance(num, int) and num > 0


def check_positive_float(amount):
    return isinstance(amount, (int, float)) and amount > 0


def check_password(password):
    return password.isnumeric() and len(password) == 4


VALIDATE_FUNCTIONS = {
    "name": check_name,
    "account number": check_positive_integer,
    "amount": check_positive_float,
    "password": check_password
}


def validate_operation(function, parameters):
    requirements = Server.OPERATIONS_REQUIREMENTS[function]

    if len(parameters) != len(requirements):
        return False

    for index in range(len(requirements)):
        try:
            if requirements[index] == "account number":
                parameters[index] = int(parameters[index])

            if requirements[index] == "amount":
                parameters[index] = float(parameters[index])

        except ValueError:
            return False

        if not VALIDATE_FUNCTIONS[requirements[index]](parameters[index]):
            return False

    return True


if __name__ == '__main__':
    Server.main()
