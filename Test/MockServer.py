import socket
import json
import threading
import queue


class MockServer(object):

    def __init__(self, host='127.0.0.1', port=80):
        """
        Initialises servers attributes.
        If a socket, host or port is not given then a new socket will be created, host will be local and port will be 80.
        Game board is represented as a 6x9 matrix (list of lists).

        :param sock:
        :param host:
        :param port:
        """
        height = 6
        width = 9
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.players = []
        self.game_over = True
        self.replay = False
        self.board = [[None] * width for _ in range(height)]
        """---------------------"""
        self.msg_queue = queue.Queue()

    def connect(self):
        """
        Bind the servers IP address and port number, and start listening.

        :return: boolean, True if no errors occur, otherwise False
        """
        connected = False
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen(2)
            connected = True
        except socket.error as exc:
            print("socket.error: %s" % exc)
        return connected

    """---------------------------------------------MOCK SPECIFIC FUNCTIONS------------------------------------------"""

    def start_thread(self, func, args=None):
        thread = threading.Thread(target=func, args=args)
        thread.start()

    def receive_messages(self, amount):
        clientsocket, address = self.sock.accept()
        self.players += [[clientsocket, address]]
        for i in range(amount):
            msg = json.loads(clientsocket.recv(1024).decode())
            self.msg_queue.put(msg)

    def connect_to_client(self):
        clientsocket, address = self.sock.accept()
        self.players += [[clientsocket, address]]

    def send_message(self, msg, player1=True):
        if player1:
            self.players[0][0].send(json.dumps(msg).encode())
        else:
            self.players[1][0].send(json.dumps(msg).encode())

    def quit(self):
        for i in range(len(self.players)):
            self.players[i][0].close()
        self.sock.close()
