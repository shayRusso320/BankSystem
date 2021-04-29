import socket
import select
from msg import *
from database import *
import json
import math

SERVER_IP = '127.0.0.1'
PORT = 5000
DATABASE = "data.db"


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
                    request = data.decode()
                    print("received data: " + str(request))

                    request = json.loads(request)
                    opcode = request["opcode"]
                    function = request["function"]

                    # user asking for function number validation and function requirements
                    if opcode == 0:
                        is_valid = validate_function_number(function)
                        if is_valid:
                            response = {"validation": True, "requirements": Server.OPERATIONS_REQUIREMENTS[function]}
                        else:
                            response = {"validation": False, "requirements": None}
                        server.add_msg(sender_socket, json.dumps(response))

                    elif opcode == 1:
                        is_valid_function = validate_function_number(function)
                        is_valid_parameters = validate_parameters_list(request)

                        # malicious code, trying to mimic the ATM interface
                        if not is_valid_function or not is_valid_parameters:
                            server.remove_ATM(sender_socket)
                            break

                        parameters = request["parameters"]

                        if validate_operation(function, parameters):
                            if function != 0:
                                acc_num = int(parameters[0])
                                password = parameters[1]
                                print(type(acc_num))
                                print(type(password))
                                print(get_account_password(server.data, acc_num))
                                if password != get_account_password(server.data, acc_num):
                                    response = {
                                        "completed": False,
                                        "content": "PASSWORD DOESN'T MATCH"
                                    }
                                    server.add_msg(sender_socket, json.dumps(response))
                                    break

                            # handling user's requests
                            server.execute_operation(function, sender_socket, parameters)

                        else:
                            response = {
                                "completed": False,
                                "content": "PARAMETERS DON'T MATCH FUNCTION"
                            }
                            server.add_msg(sender_socket, json.dumps(response))

            server.send_waiting_messages(wlist)

    @staticmethod
    def upload_server():
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SERVER_IP, PORT))
        print("server is up")

        server_socket.listen(5)

        return server_socket

    def execute_operation(self, opcode, ATM_socket, parameters):
        Server.OPERATIONS[opcode](self, ATM_socket, *parameters)

    def send_waiting_messages(self, wlist):
        for msg in self.messages_to_send:

            if msg.get_sock() in wlist:  # if the socket ready to listen
                msg.get_sock().send(msg.get_content().encode())
                print("sent: " + str(msg.get_content()))
                self.messages_to_send.remove(msg)

    def add_msg(self, receiver, content):
        new_msg = Msg(receiver, content)
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
        response = {
            "completed": True,
            "content": f"NEW ACCOUNT IS NOW ACTIVE, YOUR ACCOUNT NUMBER IS: {account_number}"
        }
        self.add_msg(ATM_socket, json.dumps(response))

    def check_balance(self, ATM_socket, account):
        balance = check_balance_database(self.data, account)
        response = {
            "completed": True,
            "content": f"YOUR BALANCE IS: {balance}"
        }
        self.add_msg(ATM_socket, json.dumps(response))

    def deposit(self, ATM_socket, account, amount):
        deposit_database(self.data, account, amount)
        response = {
            "completed": True,
            "content": "TRANSACTION COMPLETED SUCCESSFULLY"
        }
        self.add_msg(ATM_socket, json.dumps(response))

    def withdraw(self, ATM_socket, account, amount):
        withdraw_database(self.data, account, amount)
        response = {
            "completed": True,
            "content": "TRANSACTION COMPLETED SUCCESSFULLY"
        }
        self.add_msg(ATM_socket, json.dumps(response))

    OPERATIONS = [open_account, check_balance, deposit, withdraw]
    OPERATIONS_REQUIREMENTS = [
        ["name", "password"],
        ["account number", "password"],
        ["account number", "password", "amount"],
        ["account number", "password", "amount"]
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
