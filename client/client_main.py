from client.network_thread import NetworkThread
from client.network_thread import NetworkThread
import threading
import time
import sys
import os

class GameClient:
    def __init__(self):
        self.players = {}
        self.clue = None
        self.running = True
        self.my_pos = {"x": 0, "y": 0} # Local estimation, server is truth

    def add_player(self, username):
        print(f"\n[+] Player joined: {username}")
        self.players[username] = {"x": 0, "y": 0}

    def remove_player(self, username):
        print(f"\n[-] Player left: {username}")
        self.players.pop(username, None)

    def update_player_state(self, msg):
        username = msg["username"]
        if username in self.players:
            self.players[username]["x"] = msg["x"]
            self.players[username]["y"] = msg["y"]
        elif username == self.username:
             self.my_pos["x"] = msg["x"]
             self.my_pos["y"] = msg["y"]

    def update_clue(self, distance):
        self.clue = distance
        print(f"\n[!] Clue: You are {distance:.2f} units away from the treasure.")

    def game_over(self, winner):
        print(f"\n\n*** GAME OVER ***\nWinner: {winner}")
        self.running = False
        print("Press Enter to exit...")

    def start(self):
        self.username = input("Enter username: ")
        self.net = NetworkThread(self.username, self)
        self.net.start()
        
        print(f"Welcome {self.username}! Use W/A/S/D to move. Q to quit.")
        
        try:
            while self.running:
                cmd = input("> ").strip().lower()
                if not self.running: break
                
                if cmd == 'w':
                    self.net.send_move(0, 1)
                elif cmd == 's':
                    self.net.send_move(0, -1)
                elif cmd == 'a':
                    self.net.send_move(-1, 0)
                elif cmd == 'd':
                    self.net.send_move(1, 0)
                elif cmd == 'q':
                    break
                else:
                    print("Unknown command. Use W/A/S/D.")
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.net.stop()
            print("Client stopped.")

if __name__ == "__main__":
    client = GameClient()
    client.start()
