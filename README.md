<p align="center">
  <h1 align="center">🏴‍☠️ Multi-Threaded Treasure Hunt</h1>
  <p align="center">
    A real-time, multiplayer treasure hunt game built with multi-threaded networking in Python.
    <br />
    Players compete to find a hidden treasure on a shared grid — guided only by distance clues.
    <br /><br />
    <a href="#-quick-start">Quick Start</a> · <a href="#-how-it-works">How It Works</a> · <a href="#%EF%B8%8F-architecture">Architecture</a> · <a href="#-key-implementation-details">Key Details</a>
  </p>
</p>

<br />

## ✨ Features

- **Real-time Multiplayer** — Multiple players connect and compete simultaneously
- **Multi-threaded Server** — Each client is handled on a dedicated thread for true concurrency
- **TCP + UDP Networking** — Reliable messaging over TCP, fast state broadcasts via UDP multicast
- **Browser-based UI** — Beautiful cyberpunk-themed web interface with canvas rendering
- **CLI Client** — Lightweight terminal client for direct play
- **Live Distance Clues** — Server calculates and sends proximity hints after every move
- **Pac-Man Wrapping** — Players wrap around the grid edges for continuous exploration

<br />

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- `flask` and `flask-socketio`

```bash
pip install flask flask-socketio
```

### Running the Game

**1 — Start the Game Server**

```bash
python3 -m server.server_main
```

The server will start listening for TCP connections on port `5001` and broadcasting game state via UDP multicast on `224.1.1.1:5003`.

**2 — Start the Web Gateway**

```bash
python3 web_gateway.py
```

This launches the Flask web server on [http://localhost:5002](http://localhost:5002).

**3 — Open your browser**, enter a username, and start hunting!

> You can also use the CLI client directly with `python3 -m client.client_main` — use `W/A/S/D` to move and `Q` to quit.

<br />

## 📂 Project Structure

```
multithreaded-treasure-hunt/
├── server/
│   ├── constants.py         # Network configuration (IPs, ports, multicast group)
│   ├── game_manager.py      # Core game logic (movement, treasure, win detection)
│   └── server_main.py       # Multi-threaded TCP/UDP server
├── client/
│   ├── client_main.py       # Terminal-based game client
│   └── network_thread.py    # Client-side networking (TCP + UDP listener)
├── templates/
│   └── index.html           # Browser UI template
├── static/
│   ├── app.js               # Frontend game logic and canvas rendering
│   └── style.css            # Cyberpunk-themed styling
└── web_gateway.py           # Flask-SocketIO bridge (browser ↔ game server)
```

<br />

## 🔍 How It Works

### The Game Loop

1. A **treasure** is randomly placed on a grid (range: -10 to 10 on both axes)
2. Players **join** and start at position `(0, 0)`
3. Each move sends a direction to the server → server updates position → sends back a **distance clue**
4. The first player to get **within 1 unit** of the treasure wins
5. All players are notified, and the game resets with a new treasure location

### Two Communication Channels

| Channel | Protocol | Purpose |
|---------|----------|---------|
| **Reliable** | TCP | Join/leave, move commands, clues, game over |
| **Fast Broadcast** | UDP Multicast | Real-time position updates to all clients |

<br />

## 🏗️ Architecture

The system consists of **three main components** that work together:

| Component | Role |
|-----------|------|
| **Game Server** | Manages game state, processes moves, broadcasts updates |
| **Web Gateway** | Bridges browser clients to the game server via Socket.IO |
| **Browser Client** | Renders the game canvas and handles user input |

The **Game Server** communicates with clients over TCP (reliable commands) and UDP multicast (fast position broadcasts). The **Web Gateway** acts as a translator — it receives Socket.IO events from the browserrontend and forwards them as TCP messages to the game server, while also listening on the UDP multicast group to push real-time updates back to the browser.

<br />

## 🔑 Key Implementation Details

### Multi-threaded Client Handling

Each connecting player gets their own thread, allowing the server to handle multiple players concurrently without blocking:

```python
def _accept_clients(self):
    while True:
        conn, addr = self.tcp_sock.accept()
        threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
```

Every accepted connection spawns a **daemon thread** running `_handle_client`, which manages the full lifecycle of that player — from the initial join message through movement processing to disconnect cleanup.

---

### Treasure Distance & Win Detection

After every move, the server calculates the Euclidean distance between the player and the treasure:

```python
dist = math.sqrt((px - self.treasure_x)**2 + (py - self.treasure_y)**2)
is_win = dist < 1.0  # Close enough to win
```

This distance is sent back as a **clue** — the only hint players get. When a player gets within 1 unit, the server broadcasts a `game_over` event to all connected clients.

---

### UDP Multicast Broadcasting

Position updates are broadcast to all listeners using UDP multicast, which is more efficient than sending individual TCP messages to each client:

```python
def _setup_udp_sender(self):
    self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ttl = struct.pack("b", 1)
    self.udp_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

def broadcast_udp(self, payload):
    msg = json.dumps(payload).encode()
    self.udp_sock.sendto(msg, MULTICAST_GROUP)
```

A single `sendto` call reaches every client subscribed to the multicast group `224.1.1.1:5003` — no need for the server to loop over connected clients.

---

### Web Gateway Bridge

The Flask-SocketIO gateway translates between **browser WebSockets** and the **game server's TCP protocol**, making the game accessible from any browser:

```python
@socketio.on("join_game")
def join_game(data):
    username = data["username"]
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect(("127.0.0.1", SERVER_PORT))
    tcp.sendall(json.dumps({"type": "join", "username": username}).encode())
```

When a browser user clicks "Join Game", the gateway opens a dedicated TCP connection to the game server on their behalf, maintaining a 1:1 mapping between browser sessions and server connections.

<br />

## 🎮 Controls

| Key | Action |
|-----|--------|
| `W` / `↑` | Move Up |
| `A` / `←` | Move Left |
| `S` / `↓` | Move Down |
| `D` / `→` | Move Right |

On-screen buttons are also available in the browser UI.

<br />

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Server | Python `socket`, `threading` |
| Protocol | TCP (reliable) + UDP Multicast (broadcast) |
| Web Gateway | Flask, Flask-SocketIO |
| Frontend | HTML5 Canvas, Vanilla JS, Socket.IO |
| Styling | Custom CSS with cyberpunk aesthetics |

<br />

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
