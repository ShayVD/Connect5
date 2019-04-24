import threading
import time
import unittest
from Server import Server
from Test.MockClient import MockClient


class ServerTest(unittest.TestCase):

    def test_init(self):
        host = 'localhost'
        port = 80
        server = Server(host=host, port=port)
        self.assertEqual(server.host, host)
        self.assertEqual(server.port, port)
        self.assertEqual(server.players, [])
        self.assertEqual(server.game_over, True)
        self.assertEqual(server.replay, False)
        self.assertEqual(server.board, [[None] * 9 for _ in range(6)])
        server.sock.close()

    def test_update_board(self):
        server = Server()
        server.players = [[None, None, 'X']]
        col = 8
        row = server.update_board(col, 0)
        self.assertEqual(row, 5)
        self.assertEqual(server.board[5][col], 'X')
        server.sock.close()

    def test_remove_player(self):
        server = Server()
        client = MockClient()
        server.connect()
        self.start_thread(self.accept_client, [server])
        client.connect()
        while len(server.players) == 0:
            time.sleep(1)
        self.assertEqual(len(server.players), 1)
        server.remove_player(0)
        self.assertEqual(server.players, [])
        client.sock.close()
        server.sock.close()

    def test_check_for_winner_horizontal(self):
        server = Server()
        tile = 'X'
        server.board[3][4] = tile
        server.board[3][5] = tile
        server.board[3][6] = tile
        server.board[3][7] = tile
        server.board[3][8] = tile
        self.assertEqual(server.check_for_winner(tile), True)
        server.sock.close()

    def test_check_for_winner_vertical(self):
        server = Server()
        tile = 'X'
        server.board[5][8] = tile
        server.board[4][8] = tile
        server.board[3][8] = tile
        server.board[2][8] = tile
        server.board[1][8] = tile
        self.assertEqual(server.check_for_winner(tile), True)
        server.sock.close()

    def test_check_for_winner_falling_diagonal(self):
        server = Server()
        tile = 'X'
        server.board[1][4] = tile
        server.board[2][5] = tile
        server.board[3][6] = tile
        server.board[4][7] = tile
        server.board[5][8] = tile
        self.assertEqual(server.check_for_winner(tile), True)
        server.sock.close()

    def test_check_for_winner_rising_diagonal(self):
        server = Server()
        tile = 'X'
        server.board[0][8] = tile
        server.board[1][7] = tile
        server.board[2][6] = tile
        server.board[3][5] = tile
        server.board[4][4] = tile
        self.assertEqual(server.check_for_winner(tile), True)
        server.sock.close()

    def test_connect(self):
        server = Server()
        self.assertEqual(server.connect(), True)
        server.sock.close()

    def test_connect_fail(self):
        server = Server()
        server.host = "string"
        self.assertEqual(server.connect(), False)
        server.sock.close()

    def test_handshake(self):
        server = Server()
        client = MockClient()
        server.connect()
        self.start_thread(self.accept_client, [server])
        client.connect()
        while len(server.players) == 0:
            time.sleep(1)
        self.start_thread(client.receive_messages, [1])
        server.send_handshake(player=0, wait=True, move=False)
        msg = client.msg_queue.get()
        while msg is None:
            msg = client.msg_queue.get()
        self.assertEqual(msg['type'], 'HELLO')
        self.assertEqual(msg['wait'], True)
        self.assertEqual(msg['move'], False)
        client.sock.close()
        server.players[0][0].close()
        server.sock.close()

    def test_update(self):
        server = Server()
        client = MockClient()
        server.connect()
        self.start_thread(self.accept_client, [server])
        client.connect()
        while len(server.players) == 0:
            time.sleep(1)
        self.start_thread(client.receive_messages, [1])
        server.send_update(player=0, move=True, row=1, column=5, tile='O')
        msg = client.msg_queue.get()
        while msg is None:
            msg = client.msg_queue.get()
        self.assertEqual(msg['type'], 'MOVE')
        self.assertEqual(msg['move'], True)
        self.assertEqual(msg['row'], 1)
        self.assertEqual(msg['col'], 5)
        self.assertEqual(msg['tile'], 'O')
        client.sock.close()
        server.players[0][0].close()
        server.sock.close()

    def test_quit(self):
        server = Server()
        client = MockClient()
        server.connect()
        self.start_thread(self.accept_client, [server])
        client.connect()
        while len(server.players) == 0:
            time.sleep(1)
        self.start_thread(client.receive_messages, [1])
        server.send_quit(player=0, name='James', quit=False, final=True, column=2, row=3, tile='X')
        msg = client.msg_queue.get()
        while msg is None:
            msg = client.msg_queue.get()
        self.assertEqual(msg['type'], 'OVER')
        self.assertEqual(msg['name'], 'James')
        self.assertEqual(msg['quit'], False)
        self.assertEqual(msg['final'], True)
        self.assertEqual(msg['row'], 3)
        self.assertEqual(msg['col'], 2)
        self.assertEqual(msg['tile'], 'X')
        client.sock.close()
        server.players[0][0].close()
        server.sock.close()

    """-------------HELPER FUNCTIONS-------------------------"""
        
    def start_thread(self, func, args=None):
        thread = threading.Thread(target=func, args=args)
        thread.start()
    
    def accept_client(self, server):
        clientsocket, address = server.sock.accept()
        server.players = [[clientsocket, address, 'X']]


def main():
    unittest.main()

if __name__ == "__main__":
    main()
