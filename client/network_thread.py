import socket
import struct
import threading
import json

from server.constants import MULTICAST_GROUP, MULTICAST_GROUP_IP, MULTICAST_PORT, SERVER_IP, SERVER_PORT


class NetworkThread(threading.Thread):
    def __init__(self, username, game):
        super().__init__(daemon=True)
        self.username = username
        self.game = game

        self.tcp_sock = None
        self.udp_sock = None
        self.running = True

    def run(self):
        self._setup_tcp()
        self._setup_udp()
        self._send_join()

        while self.running:
            self._recv_tcp()
            self._recv_udp()

        self._cleanup()

    # -----------------------------
    # TCP SETUP
    # -----------------------------
    def _setup_tcp(self):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((SERVER_IP, SERVER_PORT))
        self.tcp_sock.settimeout(0.01)

    # -----------------------------
    # UDP MULTICAST SETUP
    # -----------------------------
    def _setup_udp(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except:
            pass  # Windows

        # IMPORTANT: bind to all interfaces
        self.udp_sock.bind(("", MULTICAST_PORT))

        # Join multicast group
        mreq = socket.inet_aton(MULTICAST_GROUP_IP) + socket.inet_aton("0.0.0.0")
        self.udp_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.udp_sock.settimeout(0.01)

    # -----------------------------
    # SEND JOIN
    # -----------------------------
    def _send_join(self):
        msg = {"type": "join", "username": self.username}
        self.tcp_sock.sendall(json.dumps(msg).encode())

    # -----------------------------
    # SEND MOVE
    # -----------------------------
    def send_move(self, dx, dy):
        msg = {"type": "move", "dx": dx, "dy": dy}
        try:
            self.tcp_sock.sendall(json.dumps(msg).encode())
        except:
            pass

    # -----------------------------
    # RECEIVE TCP
    # -----------------------------
    def _recv_tcp(self):
        try:
            data = self.tcp_sock.recv(1024)
            if not data:
                return

            msg = json.loads(data.decode())

            if msg["type"] == "player_joined":
                self.game.add_player(msg["username"])

            elif msg["type"] == "player_left":
                self.game.remove_player(msg["username"])
            
            elif msg["type"] == "clue":
                self.game.update_clue(msg["distance"])
            
            elif msg["type"] == "game_over":
                self.game.game_over(msg["winner"])

        except:
            pass

    # -----------------------------
    # RECEIVE UDP
    # -----------------------------
    def _recv_udp(self):
        try:
            data, _ = self.udp_sock.recvfrom(2048)
            msg = json.loads(data.decode())

            if msg["type"] == "state_update":
                self.game.update_player_state(msg)

        except:
            pass

    # -----------------------------
    # CLEANUP
    # -----------------------------
    def stop(self):
        self.running = False

    def _cleanup(self):
        try:
            self.tcp_sock.close()
        except:
            pass

        try:
            self.udp_sock.close()
        except:
            pass
