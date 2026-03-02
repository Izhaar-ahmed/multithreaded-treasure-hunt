from server.constants import *

class GameManager:
    def __init__(self):
        self.players = {}
        self.treasure_x = 0
        self.treasure_y = 0
        self._spawn_treasure()

    def _spawn_treasure(self):
        import random
        # Spawn treasure within a reasonable range, e.g., -10 to 10
        self.treasure_x = random.randint(-10, 10)
        self.treasure_y = random.randint(-10, 10)
        print(f"DEBUG: Treasure spawned at ({self.treasure_x}, {self.treasure_y})")

    def reset_game(self):
        self._spawn_treasure()

    def add_player(self, username):
        self.players[username] = {"x": 0, "y": 0}

    def remove_player(self, username):
        if username in self.players:
            del self.players[username]

    def process_move(self, username, dx, dy):
        if username not in self.players:
            return None

        # Update position
        self.players[username]["x"] += dx
        self.players[username]["y"] += dy
        
        # World Wrapping (Pac-Man style)
        # Grid is roughly -15 to 15 based on client 600px / 20px scale
        LIMIT = 15
        if self.players[username]["x"] > LIMIT:
            self.players[username]["x"] = -LIMIT
        elif self.players[username]["x"] < -LIMIT:
            self.players[username]["x"] = LIMIT
            
        if self.players[username]["y"] > LIMIT:
            self.players[username]["y"] = -LIMIT
        elif self.players[username]["y"] < -LIMIT:
            self.players[username]["y"] = LIMIT
        
        px = self.players[username]["x"]
        py = self.players[username]["y"]

        # Calculate distance to treasure
        import math
        dist = math.sqrt((px - self.treasure_x)**2 + (py - self.treasure_y)**2)
        
        # Check win condition
        is_win = dist < 1.0  # Close enough to win

        return {
            "x": px,
            "y": py,
            "distance": dist,
            "is_win": is_win
        }

    def get_all_players(self):
        return self.players
