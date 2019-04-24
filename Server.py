import socket
import json
import threading
import sys


class Server(object):

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
        self.sock = self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.players = []
        self.game_over = True
        self.replay = False
        self.board = [[None] * width for _ in range(height)]

    def start(self):
        """
        Start 5 in a row server.
        Two connections will be accepted, and for each a thread will begin that accepts and processes messages.
        """
        if self.connect():
            print("Connect-5 server started!")
            print("Waiting for players to join...")
            for player in range(2):
                clientsocket, address = self.sock.accept()
                thread = threading.Thread(target=self.main, args=(player, clientsocket, address))
                thread.start()
        else:
            print("Could not start server...")

    def main(self, player, clientsocket, address):
        """
        The main loop that accepts and processes messages from each client.

        :param player:          int, 0 for the first player, 1 for the second
        :param clientsocket:    socket.socket, clients socket object
        :param address:         string, clients address
        """
        self.client_setup(player, clientsocket, address)
        while not self.game_over:
            msg = clientsocket.recv(1024).decode()
            self.process(msg, player)

    def client_setup(self, player, clientsocket, address):
        """
        Saves clients data, assigns 'X' tile if first player and 'O' if second player.
        Initial handshake messages are sent out to the clients.

        :param player:          int, 0 for the first player, 1 for the second
        :param clientsocket:    socket.socket, clients socket object
        :param address:         string, clients address
        """
        if player == 0:
            self.players += [[clientsocket, address, 'X']]
            print("Player one has joined!")
            self.send_handshake(player=player, wait=True, move=False)
            self.game_over = False
        else:
            self.players += [[clientsocket, address, 'O']]
            print("Player two has joined!")
            self.send_handshake(player=player, wait=False, move=False)
            self.send_handshake(player=not player, wait=False, move=True)

    def process(self, msg, player):
        """
        Processes messages received from the clients. Messages must be in JSON format.
        There are three message types;
        'HELLO': The initial handshake message
        'MOVE' : Update to the game board
        'OVER' : Quitting message

        :param msg:     JSON file
        :param player:  int, 0 for first player, 1 for second
        """
        print("Player: ", player, "Message: ", msg)
        try:
            msg = json.loads(msg)
            if msg['type'] == 'HELLO':
                if msg['replay']:
                    # If the other player has not left yet
                    if len(self.players) == 2:
                        # If the other player said they want to play again already
                        if self.replay:
                            # Tell player to wait for other player to make move
                            self.send_handshake(player=player, wait=False, move=False)
                            # Tell other player to make their move
                            self.send_handshake(player=not player, wait=False, move=True)
                            self.replay = False
                        # If the other player has not responded yet
                        else:
                            # Tell player to wait for other players reply
                            self.send_handshake(player=player, wait=True, move=False)
                            self.game_over = False
                            self.replay = True
                    # The other player has left
                    else:
                        # Tell player to quit
                        self.send_quit(player=0, name="", quit=False, final=True)
                        self.remove_player(0)
                else:
                    self.players[player] += [msg['name']]
            elif msg['type'] == 'MOVE':
                column = int(msg['col'])
                row = self.update_board(column, player)
                tile = self.players[player][2]
                # If a winner has been found
                if self.check_for_winner(tile):
                    name = self.players[player][3]
                    self.send_quit(player=0, name=name, quit=False, final=False, row=row, column=column, tile=tile)
                    self.send_quit(player=1, name=name, quit=False, final=False, row=row, column=column, tile=tile)
                # Otherwise update clients on new piece and which players move it is
                else:
                    self.send_update(player=player, move=False, row=row, column=column, tile=tile)
                    self.send_update(player=not player, move=True, row=row, column=column, tile=tile)
            elif msg['type'] == 'OVER':
                # If player has quit
                if msg['quit']:
                    # Advise players that game is over
                    name = self.players[not player][3]
                    self.send_quit(player=0, name=name, quit=True, final=False)
                    self.send_quit(player=1, name=name, quit=True, final=False)
                    #self.game_over = True
                # If player does not want to play again
                else:
                    self.remove_player(player)
                    if self.replay:
                        self.send_quit(player=0, name="", quit=False, final=True)
                        self.remove_player(0)
                    self.game_over = True
        except ValueError:
            print("Received data is not in JSON format...")
            self.game_over = True

    def update_board(self, column, player):
        """
        Puts the given players tile in the given column at the lowest possible row.
        The row is then returned to send to the clients.

        :param column: int, 0 to 8
        :param player: int, 0 or 1
        :return: row, 0 to 5
        """
        if self.board[0][column] is None:
            for row in range(6):
                if row == 5:
                    self.board[row][column] = self.players[player][2]
                    return row
                elif self.board[row+1][column] is not None:
                    self.board[row][column] = self.players[player][2]
                    return row
        else:
            print("Row is full...")

    def remove_player(self, index):
        """
        Close clients socket and remove players data.

        :param index: int, 0 for first player, 1 for second player
        """
        if len(self.players) == 1:
            index = 0
        sock = self.players[index][0]
        sock.close()
        self.players.pop(index)

    def check_for_winner(self, tile):
        """
        Check the board and see if the given tile has 5 in a row.

        :param tile: string, 'X' or 'O'
        :return: boolean, True if 5 in a row, False otherwise
        """
        # Check horizontal
        for row in range(6):
            for col in range(9-4):
                if self.board[row][col] == tile and self.board[row][col+1] == tile and self.board[row][col+2] == tile \
                    and self.board[row][col+3] == tile and self.board[row][col+4] == tile:
                    return True
        # Check vertical
        for row in range(6-4):
            for col in range(9):
                if self.board[row][col] == tile and self.board[row+1][col] == tile and self.board[row+2][col] == tile \
                    and self.board[row+3][col] == tile and self.board[row+4][col] == tile:
                    return True
        # Check rising diagonal
        for row in range(4, 6):
            for col in range(9-4):
                if self.board[row][col] == tile and self.board[row-1][col+1] == tile and self.board[row-2][col+2] == tile \
                    and self.board[row-3][col+3] == tile and self.board[row-4][col+4] == tile:
                    return True
        # Check falling diagonal
        for row in range(6-4):
            for col in range(9-4):
                if self.board[row][col] == tile and self.board[row+1][col+1] == tile and self.board[row+2][col+2] == tile \
                    and self.board[row+3][col+3] == tile and self.board[row+4][col+4] == tile:
                    return True
        return False

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

    def send(self, msg, player):
        """
        Turn msg into JSON and encode before sending to the given player.

        :param msg:     {}
        :param player:  int, 0 for player 1, 1 for player 2
        """
        self.players[player][0].send(json.dumps(msg).encode())

    def send_handshake(self, player, wait, move):
        """
        Creates and sends handshake message to the given player.

        :param player:  int, 0 or 1
        :param wait:    boolean, True if the player must wait for another player
        :param move:    boolean, True if its the players turn next
        """
        msg = {'type':'HELLO', 'wait':wait, 'move':move}
        self.send(msg, player)

    def send_update(self, player, move, row, column, tile):
        """
        Creates and sends update message to the given player.

        :param player:  int, 0 or 1
        :param move:    boolean, True if its the players turn
        :param row:     int, 0 to 5
        :param column:  int, 0 to 8
        :param tile:    string, 'X' or 'O'
        """
        msg = {'type':'MOVE', 'move':move, 'row':row, 'col':column, 'tile':tile}
        self.send(msg, player)

    def send_quit(self, player, name, quit, final, row=None, column=None, tile=None):
        """
        Creates and sends quitting message to the given player.

        :param player:  int, 0 or 1
        :param name:    string, winning players name
        :param quit:    boolean, True if the game was quit by a player mid game
        :param final:   boolean, True if this is the final message to the client
        :param row:     int, 0 to 5 (or None)
        :param column:  int, 0 to 8 (or None)
        :param tile:    string, 'X' or 'O' (or None)
        """
        msg = {'type':'OVER', 'name':name, 'quit':quit, 'final':final, 'row':row, 'col':column, 'tile':tile}
        self.send(msg, player)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        s = Server()
        s.start()
    elif len(sys.argv) == 2:
        s = Server(host=sys.argv[1])
        s.start()
    elif len(sys.argv) == 3:
        s = Server(host=sys.argv[1], port=int(sys.argv[2]))
        s.start()
    else:
        print("Too many arguments provided.")
