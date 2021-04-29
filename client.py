import socket
import json

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000
MAX_DATA_LENGTH = 1024


CHOOSE_FUNCTION = """
---------------- MENU ----------------

CHOOSE THE WANTED OPERATION:
0) DISCONNECT FROM ACCOUNT
1) CHECK BALANCE
2) DEPOSIT
3) WITHDRAW
enter your choice(1-3): 
"""

HAS_ACCOUNT = "\n\nDO YOU HAVE AN ACCOUNT?\n enter 1 for yes or 0 for no:"
GET_INPUT = "please enter {0}: "
OPERATION_FAILED = "OPERATION FAILED :("
OPERATION_COMPLETED = "OPERATION WAS COMPLETED"
SIGN_IN_SUCCESS = "SIGNED IN SUCCESSFULLY!"
SIGN_IN_FAILURE = "failure in signing in"
SIGN_UP_SUCCESS = "SIGNED IN SUCCESSFULLY!"
SIGN_UP_FAILURE = "failure in signing in"
DISCONNECTED = "THE ATM IS DISCONNECTED FROM BANK"


# uploading client and connecting to server
def upload_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))

    print("client is up")
    return client_socket


# function for validating function number input and getting the requirements from server
# gets: client_socket for contacting server
# return: a dict containing the function number chosen,
#         boolean for validating the function number input and the requirements for the function
def get_function_requirements(client_socket):
    function = int(input(CHOOSE_FUNCTION)) - 1

    if function == -1:
        return None

    request = {"opcode": 2, "function": function}
    client_socket.send(json.dumps(request).encode())
    response = json.loads(client_socket.recv(MAX_DATA_LENGTH).decode())
    response["function"] = function

    return response


def handle_response(client_socket, success_msg, failure_msg):
    response = client_socket.recv(MAX_DATA_LENGTH)
    if response:
        response = json.loads(response.decode())

        if response["completed"]:
            print(success_msg)
            return response

        else:
            print(failure_msg)
            print(response["content"])  # print cause for failure
            return False
    else:
        print(DISCONNECTED)  # server down


def main():
    client_socket = upload_client()

    while True:
        # ask user if he has an account
        try:
            has_account = int(input(HAS_ACCOUNT))
        except ValueError:
            print("invalid input")
            continue

        if has_account != 0 and has_account != 1:
            print("invalid input")
            break
        has_account = has_account == 1

        # open new account
        if not has_account:
            try:
                name = input(GET_INPUT.format("name"))
                password = input(GET_INPUT.format("password"))
            except ValueError:
                print("invalid input")
                continue

            sign_up = {
                "opcode": 0,
                "name": name,
                "password": password
            }
            client_socket.send(json.dumps(sign_up).encode())

            response = handle_response(client_socket, SIGN_UP_SUCCESS, SIGN_UP_FAILURE)
            if response is None:
                break
            if response:
                print(response["content"])

        # register into account
        else:
            try:
                acc_num = input(GET_INPUT.format("account number"))
                password = input(GET_INPUT.format("password"))
            except ValueError:
                print("invalid input")
                continue

            register = {
                "opcode": 1,
                "account": acc_num,
                "password": password
            }
            client_socket.send(json.dumps(register).encode())

            response = handle_response(client_socket, SIGN_IN_SUCCESS, SIGN_IN_FAILURE)
            if response is None:
                break
            if not response:
                continue

            while True:
                if menu(client_socket, acc_num, password) is None:
                    break


def menu(client_socket, account, password):
    is_valid_function = False
    requirements = []
    function = -1

    # asking user for a function number until user inserts a valid function number
    while not is_valid_function:
        try:
            response = get_function_requirements(client_socket)
        except ValueError:
            print("invalid input")
            continue

        if response is None:
            return None

        if not response["completed"]:
            print("invalid input")
            continue

        is_valid_function = response["completed"]
        requirements = response["content"]
        function = response["function"]

    # asking user for the parameters required
    parameters = []
    try:
        for req in requirements:
            parameters.append(input(GET_INPUT.format(req)))
    except ValueError:
        print("invalid input")
        return False

    # sending operation to server
    operation = {
        "opcode": 3,
        "account": account,
        "password": password,
        "function": function,
        "parameters": parameters
    }
    client_socket.send(json.dumps(operation).encode())

    response = handle_response(client_socket, OPERATION_COMPLETED, OPERATION_FAILED)
    if response is None:
        return None
    if response:
        print(response["content"])
        return True
    else:
        return False


if __name__ == '__main__':
    main()
