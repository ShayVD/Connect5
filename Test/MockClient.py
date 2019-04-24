import socket
import json
import queue


class MockClient(object):


    def __init__(self, host='127.0.0.1', port=80):
        """
        Initialises clients attributes.
        If a socket, host or port is not given then a new socket will be created, host will be local and port will be 80.
        Game board is represented as a 6x9 matrix (list of lists).

        :param sock: socket.socket, or None
        :param host: string, IP address
        :param port: int, port number
        """
        height = 6
        width = 9
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.game_over = True
        self.board = [[None] * width for _ in range(height)]
        self.name = None
        self.move = None
        self.stop = False
        self.replay = True
        """-----------"""
        self.msg_queue = queue.Queue()

    def connect(self):
        """
        Connect to given server using host IP address and port number.
        If connection is successful then True is returned, otherwise False.

        :return: connected, boolean
        """
        connected = False
        try:
            self.sock.connect((self.host, self.port))
            connected = True
        except socket.error as exc:
            print("socket.error : %s" % exc)
        return connected

    """------------------------"""

    def receive_messages(self, amount):
        for i in range(amount):
            msg = json.loads(self.sock.recv(1024).decode())
            self.msg_queue.put(msg)
