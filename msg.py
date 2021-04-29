
class Msg:
    def __init__(self, sock, content):
        self.content = content
        self.sock = sock

    def get_sock(self):
        return self.sock

    def get_content(self):
        return self.content
