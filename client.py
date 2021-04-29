import socket
import json

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000
MAX_DATA_LENGTH = 1024


CHOOSE_OPCODE = """
---------------- MENU ----------------

CHOOSE THE WANTED OPERATION:
1) OPEN ACCOUNT
2) CHECK BALANCE
3) DEPOSIT
4) WITHDRAW
enter your choice(1-4): 
"""

IDENTIFY = "please identify using your account number: "
NAME = "please enter your name: "
AMOUNT = "enter the amount of money for the transaction: "


def upload_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))

    print("client is up")
    return client_socket


def main():
    client_socket = upload_client()

    while True:
        opcode = int(input(CHOOSE_OPCODE)) - 1

        if opcode == 0:
            name = input(NAME)
            parameters = [name]

        elif opcode == 1:
            account = int(input(IDENTIFY))
            parameters = [account]

        elif opcode == 2 or opcode == 3:
            account = int(input(IDENTIFY))
            amount = int(input(AMOUNT))
            parameters = [account, amount]

        else:
            break

        request = {
            "opcode": opcode,
            "parameters": parameters
        }

        client_socket.send(json.dumps(request).encode())

        response = client_socket.recv(1024)

        if response:
            response = response.decode()
            print(response)
        else:
            print("disconnected")
            break


if __name__ == '__main__':
    main()
