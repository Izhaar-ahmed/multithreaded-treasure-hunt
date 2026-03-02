import socket
import struct
import threading
import json

from server.constants import SERVER_IP, SERVER_PORT, MULTICAST_GROUP, MULTICAST_GROUP_IP, MULTICAST_PORT
from server.game_manager import GameManager

class Server:
    def __init__(self):
        self.clients = {}  # username → socket
        self.lock = threading.Lock()
        self.game_manager = GameManager()

        self.tcp_sock = None
        self.udp_sock = None

    # -----------------------------------
    def start(self):
        print("Server starting...")

        self._setup_tcp_listener()
        self._setup_udp_sender()

        threading.Thread(target=self._accept_clients, daemon=True).start()

        print("Server running.")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("Server shutting down.")

    # -----------------------------------
    def _setup_tcp_listener(self):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind((SERVER_IP, SERVER_PORT))
        self.tcp_sock.listen()

    # -----------------------------------
    def _accept_clients(self):
        while True:
            conn, addr = self.tcp_sock.accept()
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    # -----------------------------------
    def _handle_client(self, conn):
        username = None
        try:
            data = conn.recv(1024)
            msg = json.loads(data.decode())

            if msg["type"] == "join":
                username = msg["username"]

                with self.lock:
                    self.clients[username] = conn
                
                self.game_manager.add_player(username)

                # Send full state to the new player
                all_players = self.game_manager.get_all_players()
                conn.sendall(json.dumps({"type": "full_state", "players": all_players}).encode())

                # notify others
                self._broadcast_tcp({"type": "player_joined", "username": username})

            # listening loop
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                
                msg = json.loads(data.decode())
                
                if msg["type"] == "move":
                    dx = msg["dx"]
                    dy = msg["dy"]
                    
                    result = self.game_manager.process_move(username, dx, dy)
                    if result:
                        # Send clue back to player
                        clue_msg = {"type": "clue", "distance": result["distance"]}
                        conn.sendall(json.dumps(clue_msg).encode())
                        
                        # Broadcast new position via UDP
                        update_msg = {
                            "type": "state_update",
                            "username": username,
                            "x": result["x"],
                            "y": result["y"]
                        }
                        self.broadcast_udp(update_msg)
                        
                        if result["is_win"]:
                            self._broadcast_tcp({"type": "game_over", "winner": username})
                            print(f"Game Over! Winner: {username}")
                            self.game_manager.reset_game()

        except Exception as e:
            print(f"Error handling client {username}: {e}")

        if username:
            with self.lock:
                self.clients.pop(username, None)
            self.game_manager.remove_player(username)

            self._broadcast_tcp({"type": "player_left", "username": username})

        try:
            conn.close()
        except:
            pass

    # -----------------------------------
    def _setup_udp_sender(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack("b", 1)
        self.udp_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    # -----------------------------------
    def _broadcast_tcp(self, payload):
        msg = json.dumps(payload).encode()
        for username, conn in list(self.clients.items()):
            try:
                conn.sendall(msg)
            except:
                pass

    # -----------------------------------
    def broadcast_udp(self, payload):
        msg = json.dumps(payload).encode()
        self.udp_sock.sendto(msg, MULTICAST_GROUP)


if __name__ == "__main__":
    Server().start()
