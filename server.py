import socket
import select
from msg import *
from database import *
import json

SERVER_IP = '127.0.0.1'
PORT = 5000
DATABASE = "data.db"


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
                data = data.decode()
                print("received data: " + str(data))

                data = json.loads(data)
                opcode = data["opcode"]
                parameters = data["parameters"]
                print(parameters)
                print(type(parameters))

                # handling user's requests
                server.execute_operation(opcode, sender_socket, parameters)

        server.send_waiting_messages(wlist)


class Server:
    def __init__(self):
        self.serv = Server.upload_server()  # create the server socket
        self.atms = []
        self.messages_to_send = []
        self.data = connect()
        create_table(self.data)

    # ------ SERVER FUNCTIONS ------

    @staticmethod
    def upload_server():
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SERVER_IP, PORT))
        print("server is up")

        server_socket.listen(5)

        return server_socket

    def execute_operation(self, opcode, ATM_socket, parameters):
        operations = [Server.open_account, Server.check_balance, Server.deposit, Server.withdraw]
        operations[opcode](self, ATM_socket, *parameters)

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

    def open_account(self, ATM_socket, name):
        add_account(self.data, name)
        self.add_msg(ATM_socket, f"NEW ACCOUNT IS NOW ACTIVE")

    def check_balance(self, ATM_socket, account):
        balance = check_balance_database(self.data, account)
        self.add_msg(ATM_socket, f"YOUR BALANCE IS: {balance}")

    def deposit(self, ATM_socket, account, amount):
        deposit_database(self.data, account, amount)
        self.add_msg(ATM_socket, f"TRANSACTION COMPLETED SUCCESSFULLY")

    def withdraw(self, ATM_socket, account, amount):
        withdraw_database(self.data, account, amount)
        self.add_msg(ATM_socket, f"TRANSACTION COMPLETED SUCCESSFULLY")


if __name__ == '__main__':
    main()
