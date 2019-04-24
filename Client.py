import socket
import json
import sys


class Client(object):


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

    def start(self):
        """
        Starts client-side of the game. User must enter their name and the client attempts to join server.
        If a connection cannot be made the user can try again. If not the client will close.
        After a game has ended the users can decide if they want to play again or not.
        """
        print("Connect-5 client started")
        self.name = input("Please enter your name: ")
        while not self.stop:
            print("Connecting to server...")
            if self.connect():
                print("Connected!")
                self.send_handshake()
                while self.replay:
                    self.game()
                    if not self.stop:
                        if self.try_again("Would you like to play again? (y/n)"):
                            self.send_handshake(replay=True)
                        else:
                            self.send_quit()
                            self.replay = False
                            self.stop = True
            else:
                print("Could not connect to server...")
                if not self.try_again():
                    self.stop = True
        self.sock.close()

    def game(self):
        """
        Main game loop. Board is printed each loop and the user is asked to enter a move or wait for their turn.
        """
        self.game_over = False
        self.receive()
        while not self.game_over:
            self.print_board()
            if self.move:
                col = None
                while not self.check_move(col):
                    col = input("It's your turn, please enter a column between 1-9 (or 0 to quit): ")
                    try:
                        col = int(col) - 1
                    except ValueError:
                        print("Please enter a number...")
                self.send_move(col)
                self.receive()
            else:
                print("Waiting for opponent to make their move...")
                self.receive()
        self.print_board()

    def process(self, msg):
        """
        Processes message received from server. Message must be in JSON format or an exception is raised.
        There are three message types;
        'HELLO': Tells the client if they have to wait for a second player, and when to make their first move.
        'MOVE' : Updates the clients board and if it is the clients turn to make a move or not.
        'OVER' : Lets the client know the game is over and who the winner is.

        :param msg: JSON file
        """
        try:
            msg = json.loads(msg)
            if msg['type'] == 'HELLO':
                if msg['wait']:
                    print("Waiting for opponent to respond...")
                    self.receive()
                else:
                    print("Game is beginning!")
                    if msg['move']:
                        print("You are making the first move.")
                        self.move = True
                    else:
                        print("Your opponent is making their move.")
                        self.move = False
                        self.receive()
            elif msg['type'] == 'MOVE':
                row = int(msg['row'])
                col = int(msg['col'])
                self.board[row][col] = msg['tile']
                self.move = msg['move']
            elif msg['type'] == 'OVER':
                winner = msg['name']
                if msg['final']:
                    self.stop = True
                    self.replay = False
                    print("Unable to play again, your opponent has left.")
                else:
                    if msg['quit']:
                        if winner == self.name:
                            print("Your opponent has quit!")
                    else:
                        row = int(msg['row'])
                        col = int(msg['col'])
                        self.board[row][col] = msg['tile']
                    print("Game over!")
                    print("%s is the winner!" % winner)
                self.game_over = True
            else:
                print("JSON held no data...")
        except ValueError:
            raise ValueError

    def check_move(self, move):
        """
        Check input from user. Must be an int between 0 and 9 entered.
        0 means the user wants to quit; 1-9 is the column a tile is to be placed in.
        User must confirm if they wish to quit.

        :param move: int, column to place tile (0 to quit game)
        :return: accept, boolean, True if valid move has been made
        """
        accept = False
        if move is not None:
            if move < -1 or move > 8:
                print("Enter a number between 0-9...")
            elif move == -1:
                confirm = ""
                while confirm != "y" and confirm != "n":
                    confirm = input("Are you sure you want to quit? (y/n)")
                if confirm  == "y":
                    accept = True
            elif self.board[0][move] is None:
                accept = True
            else:
                print("Column %i is full..." % move)
        return accept

    @staticmethod
    def try_again(msg=None):
        """
        Ask the user if they want to try again, or use the msg if provided.

        :param msg: string, message for the user to answer y/n to
        :return: boolean, True if y, False if n
        """
        again = ""
        while again != "y" and again != "n":
            if msg is None:
                again = input("Would you like to try again? (y/n)")
            else:
                again = input(msg)
        if again == "y":
            return True
        return False

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

    def receive(self):
        """
        Receives message and updates client accordingly.
        """
        msg = self.sock.recv(1024).decode()
        self.process(msg)

    def send(self, msg):
        """
        Turn msg into JSON and encode before sending to server.

        :param msg: {}
        """
        self.sock.send(json.dumps(msg).encode())

    def send_handshake(self, replay=False):
        """
        Send initial message to server with users name.
        """
        msg = {'type':'HELLO', 'name':self.name, 'replay':replay}
        self.send(msg)

    def send_quit(self):
        msg = {'type':'OVER', 'name':self.name, 'quit':False}
        self.send(msg)

    def send_move(self, move):
        """
        Sends users move to the game server.
        Two types of messages 'MOVE' to update board and 'OVER' to quit game.

        :param move: int, -1 ro 8
        """
        msg = {}
        if move == -1:
            msg['type'] = 'OVER'
            msg['quit'] = True
        else:
            msg['type'] = 'MOVE'
            msg['col'] = move
        self.send(msg)

    def print_board(self):
        """
        Prints game board.
        """
        for row in range(6):
            print("")
            for col in range(9):
                if self.board[row][col] is None:
                    print("[ ]", end="")
                else:
                    print("[%s]" % self.board[row][col], end="")
        print("")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        c = Client()
        c.start()
    elif len(sys.argv) == 2:
        c = Client(host=sys.argv[1])
        c.start()
    elif len(sys.argv) == 3:
        c = Client(host=sys.argv[1], port=int(sys.argv[2]))
        c.start()
    else:
        print("Too many arguments provided.")

