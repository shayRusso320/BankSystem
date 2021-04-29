import socket
import json

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000
MAX_DATA_LENGTH = 1024


CHOOSE_FUNCTION = """
---------------- MENU ----------------

CHOOSE THE WANTED OPERATION:
1) OPEN ACCOUNT
2) CHECK BALANCE
3) DEPOSIT
4) WITHDRAW
enter your choice(1-4): 
"""

HAS_ACCOUNT = "DO YOU HAVE AN ACCOUNT?\n enter 1 for yes or 0 for no:"
GET_INPUT = "please enter {0}: "
OPERATION_FAILED = "OPERATION FAILED :("
OPERATION_COMPLETED = "OPERATION WAS COMPLETED"
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
#         boolean for validating the function numebr input and the requirements for the function
def get_function_requirements(client_socket):
    function = int(input(CHOOSE_FUNCTION)) - 1

    request = {"opcode": 0, "function": function}
    client_socket.send(json.dumps(request).encode())
    response = json.loads(client_socket.recv(MAX_DATA_LENGTH).decode())
    response["function"] = function

    return response


def main():
    client_socket = upload_client()

    while True:
        is_valid_function = False
        requirements = []
        function = -1

        # asking user for a function number until user inserts a valid function number
        while not is_valid_function:
            response = get_function_requirements(client_socket)
            is_valid_function = response["validation"]
            requirements = response["requirements"]
            function = response["function"]

        # asking user for the parameters required
        parameters = []
        for req in requirements:
            parameters.append(input(GET_INPUT.format(req)))

        # sending operation to server
        operation = {
            "opcode": 1,
            "function": function,
            "parameters": parameters
        }
        client_socket.send(json.dumps(operation).encode())
        response = client_socket.recv(MAX_DATA_LENGTH)

        # handling answer from server
        if response:
            print("response" + str(response))
            response = json.loads(response.decode())

            print(OPERATION_COMPLETED if response["completed"] else OPERATION_FAILED)
            print(response["content"])

        # in case communication with server is shutdown
        else:
            print(DISCONNECTED)
            break


if __name__ == '__main__':
    main()
