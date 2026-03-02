# web_gateway.py (updated for JSON protocol)

import socket
import struct
import threading
import time
import json
from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from server.constants import SERVER_IP, SERVER_PORT, MULTICAST_GROUP, MULTICAST_GROUP_IP, MULTICAST_PORT

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

@app.route("/")
def index():
    return render_template("index.html")

# -----------------------------
# UDP MULTICAST LISTENER
# -----------------------------
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except Exception:
        pass

    sock.bind(("", MULTICAST_PORT))

    mreq = socket.inet_aton(MULTICAST_GROUP_IP) + socket.inet_aton("0.0.0.0")
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"[Gateway] Listening to multicast on {MULTICAST_GROUP_IP}:{MULTICAST_PORT}")

    while True:
        try:
            data, _ = sock.recvfrom(2048)
            msg = json.loads(data.decode())
            socketio.emit("multicast", msg)
        except:
            continue

threading.Thread(target=udp_listener, daemon=True).start()

# -----------------------------
# SOCKET.IO HANDLERS
# -----------------------------
clients = {} # sid -> tcp_socket
clients_lock = threading.Lock()

@socketio.on("connect")
def handle_connect():
    print("[Gateway] Browser connected")

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"[Gateway] Browser disconnected: {sid}")
    if sid in clients:
        try:
            clients[sid].close()
        except:
            pass
        del clients[sid]

@socketio.on("join_game")
def join_game(data):
    username = data["username"]
    sid = request.sid

    try:
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.connect(("127.0.0.1", SERVER_PORT))
        
        # Send JSON join message
        join_msg = {"type": "join", "username": username}
        tcp.sendall(json.dumps(join_msg).encode())
        
    except Exception as e:
        emit("join_response", {"ok": False, "error": str(e)})
        return

    with clients_lock:
        clients[sid] = tcp
        
    emit("join_response", {"ok": True, "username": username})

    def tcp_reader():
        while True:
            try:
                data = tcp.recv(2048)
                if not data:
                    break
                
                # Handle multiple JSON objects in one buffer if necessary, 
                # but for now assume one message per packet or simple concatenation
                # A robust parser would buffer and split by JSON boundaries.
                # For simplicity, we'll try to decode directly.
                try:
                    msg = json.loads(data.decode())
                    socketio.emit("server_msg", msg, to=sid)
                except json.JSONDecodeError:
                    # Fallback for multiple messages or partial reads (simplified)
                    pass
                    
            except:
                break
        
        # Cleanup on loop exit
        with clients_lock:
            if sid in clients:
                del clients[sid]
        socketio.emit("server_msg", {"type": "disconnect"}, to=sid)

    threading.Thread(target=tcp_reader, daemon=True).start()

@socketio.on("move")
def move(data):
    sid = request.sid
    dx = data.get("dx", 0)
    dy = data.get("dy", 0)

    with clients_lock:
        if sid not in clients:
            emit("action_response", {"ok": False, "error": "Not connected"})
            return
        tcp = clients[sid]

    try:
        move_msg = {"type": "move", "dx": dx, "dy": dy}
        tcp.sendall(json.dumps(move_msg).encode())
    except:
        emit("action_response", {"ok": False, "error": "Send failed"})

# -----------------------------
# START SERVER
# -----------------------------
if __name__ == "__main__":
    print("[Gateway] Starting Flask-SocketIO gateway...")
    socketio.run(
        app,
        host="0.0.0.0",
        port=5002,
        debug=True,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )
