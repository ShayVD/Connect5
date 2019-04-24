import json
import unittest
from Client import Client
from Test.MockServer import MockServer


class ClientTest(unittest.TestCase):

    def test_init(self):
        host = 'localhost'
        port = 80
        client = Client(host=host, port=port)
        self.assertEqual(client.host, host)
        self.assertEqual(client.port, port)
        self.assertEqual(client.game_over, True)
        self.assertEqual(client.board, [[None] * 9 for _ in range(6)])
        self.assertEqual(client.name, None)
        self.assertEqual(client.move, None)
        self.assertEqual(client.stop, False)
        self.assertEqual(client.replay, True)
        client.sock.close()

    def test_process_HELLO(self):
        client = Client()
        msg = json.dumps({'type':'HELLO', 'wait':False, 'move':True})
        client.process(msg)
        self.assertEqual(client.move, True)
        client.sock.close()

    def test_process_MOVE(self):
        client = Client()
        row = 5
        col = 3
        tile = 'X'
        msg = json.dumps({'type':'MOVE', 'row':row, 'col':col, 'tile':tile, 'move':True})
        client.process(msg)
        self.assertEqual(client.board[row][col], tile)
        self.assertEqual(client.move, True)
        client.sock.close()

    def test_process_OVER1(self):
        client = Client()
        winner = "James"
        final = True
        msg = json.dumps({'type':'OVER', 'name':winner, 'final':final})
        client.process(msg)
        self.assertEqual(client.stop, True)
        self.assertEqual(client.replay, False)
        self.assertEqual(client.game_over, True)
        client.sock.close()

    def test_process_OVER2(self):
        client = Client()
        winner = "James"
        final = False
        quit = True
        msg = json.dumps({'type':'OVER', 'name':winner, 'final':final, 'quit':quit})
        client.process(msg)
        self.assertEqual(client.game_over, True)
        client.sock.close()

    def test_process_OVER3(self):
        client = Client()
        winner = "James"
        final = False
        quit = False
        row = 5
        col = 3
        tile = 'X'
        msg = json.dumps({'type':'OVER', 'name':winner, 'final':final, 'quit':quit,
                          'row':row, 'col':col, 'tile':tile})
        client.process(msg)
        self.assertEqual(client.board[row][col], tile)
        self.assertEqual(client.game_over, True)
        client.sock.close()

    def test_process_fail(self):
        client = Client()
        msg = "string"
        self.assertRaises(ValueError, client.process, msg)
        client.sock.close()

    def test_connect(self):
        server = MockServer()
        server.connect()
        client = Client()
        self.assertEqual(client.connect(), True)
        client.sock.close()
        server.quit()

    def test_connect_fail(self):
        client = Client()
        self.assertEqual(client.connect(), False)
        client.sock.close()

    def test_send_move_minus1(self):
        server = MockServer()
        server.connect()
        server.start_thread(server.receive_messages, [1])
        client = Client()
        client.connect()
        client.send_move(-1)
        msg = server.msg_queue.get()
        while msg is None:
            msg = server.msg_queue.get()
        self.assertEqual(msg['type'], 'OVER')
        self.assertEqual(msg['quit'], True)
        client.sock.close()
        server.quit()

    def test_send_move_1_to_9(self):
        server = MockServer()
        server.connect()
        server.start_thread(server.receive_messages, [9])
        client = Client()
        client.connect()
        for i in range(1,10):
            client.send_move(i)
            msg = server.msg_queue.get()
            while msg is None:
                msg = server.msg_queue.get()
            self.assertEqual(msg['type'], 'MOVE')
            self.assertEqual(msg['col'], i)
        client.sock.close()
        server.quit()

    def test_check_move_None(self):
        client = Client()
        self.assertEqual(client.check_move(None), False)
        client.sock.close()

    def test_check_move_0_to_8(self):
        client = Client()
        for i in range(9):
            self.assertEqual(client.check_move(i), True)
        client.sock.close()

    def test_check_move_lt_minus1_and_gt_8(self):
        client = Client()
        self.assertEqual(client.check_move(-2), False)
        self.assertEqual(client.check_move(9), False)
        client.sock.close()

    def test_send_handshake(self):
        server = MockServer()
        server.connect()
        server.start_thread(server.receive_messages, [1])
        client = Client()
        client.name = 'James'
        client.connect()
        client.send_handshake(True)
        msg = server.msg_queue.get()
        while msg is None:
            msg = server.msg_queue.get()
        self.assertEqual(msg['type'], 'HELLO')
        self.assertEqual(msg['name'], 'James')
        self.assertEqual(msg['replay'], True)
        client.sock.close()
        server.quit()

    def test_send_quit(self):
        server = MockServer()
        server.connect()
        server.start_thread(server.receive_messages, [1])
        client = Client()
        client.name = 'James'
        client.connect()
        client.send_quit()
        msg = server.msg_queue.get()
        while msg is None:
            msg = server.msg_queue.get()
        self.assertEqual(msg['type'], 'OVER')
        self.assertEqual(msg['name'], 'James')
        self.assertEqual(msg['quit'], False)
        client.sock.close()
        server.quit()

    def test_send_move1(self):
        server = MockServer()
        server.connect()
        server.start_thread(server.receive_messages, [1])
        client = Client()
        client.connect()
        client.send_move(2)
        msg = server.msg_queue.get()
        while msg is None:
            msg = server.msg_queue.get()
        self.assertEqual(msg['type'], 'MOVE')
        self.assertEqual(msg['col'], 2)
        client.sock.close()
        server.quit()

    def test_send_move2(self):
        server = MockServer()
        server.connect()
        server.start_thread(server.receive_messages, [1])
        client = Client()
        client.connect()
        client.send_move(-1)
        msg = server.msg_queue.get()
        while msg is None:
            msg = server.msg_queue.get()
        self.assertEqual(msg['type'], 'OVER')
        self.assertEqual(msg['quit'], True)
        client.sock.close()
        server.quit()


def main():
    unittest.main()

if __name__ == "__main__":
    main()
