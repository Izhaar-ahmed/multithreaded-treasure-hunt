const socket = io();

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const gameScreen = document.getElementById('game-screen');
const usernameInput = document.getElementById('username');
const joinBtn = document.getElementById('join-btn');
const playerNameSpan = document.getElementById('player-name');
const clueDisplay = document.getElementById('clue-display');
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const logContainer = document.getElementById('log-container');

// Game State
let myUsername = null;
let players = {}; // username -> {x, y}
const SCALE = 20; // pixels per unit
const OFFSET_X = canvas.width / 2;
const OFFSET_Y = canvas.height / 2;

// Join Game
joinBtn.addEventListener('click', () => {
    const username = usernameInput.value.trim();
    if (username) {
        socket.emit('join_game', { username: username });
    }
});

socket.on('join_response', (data) => {
    if (data.ok) {
        myUsername = data.username;
        playerNameSpan.textContent = myUsername;
        loginScreen.classList.add('hidden');
        gameScreen.classList.remove('hidden');
        log("Joined game as " + myUsername);
        draw();
    } else {
        alert("Failed to join: " + data.error);
    }
});

// Server Messages (TCP)
socket.on('server_msg', (msg) => {
    console.log("TCP:", msg);

    if (msg.type === 'full_state') {
        players = msg.players;
        updatePlayersList();
        draw();
    } else if (msg.type === 'player_joined') {
        log(`Player joined: ${msg.username}`);
        players[msg.username] = { x: 0, y: 0 };
        updatePlayersList();
    } else if (msg.type === 'player_left') {
        log(`Player left: ${msg.username}`);
        delete players[msg.username];
        updatePlayersList();
    } else if (msg.type === 'clue') {
        clueDisplay.textContent = `${msg.distance.toFixed(2)}m`;
        // Use Gold normally, Red if very close
        clueDisplay.style.color = msg.distance < 2 ? '#ff0055' : '#ffd700';
    } else if (msg.type === 'game_over') {
        showGameOver(msg.winner);
    } else if (msg.type === 'disconnect') {
        alert("Disconnected from server.");
        location.reload();
    }
    draw();
});

// Multicast Messages (UDP)
socket.on('multicast', (msg) => {
    // console.log("UDP:", msg);
    if (msg.type === 'state_update') {
        players[msg.username] = { x: msg.x, y: msg.y };
        draw();
    }
});

function updatePlayersList() {
    const list = document.getElementById('players-list');
    list.innerHTML = '';

    for (const username of Object.keys(players)) {
        const li = document.createElement('li');
        li.textContent = username;
        if (username === myUsername) {
            li.classList.add('self');
            li.textContent += ' (You)';
        }
        list.appendChild(li);
    }
}

// Controls
document.addEventListener('keydown', (e) => {
    if (loginScreen.classList.contains('hidden')) {
        if (!document.getElementById('game-over-modal').classList.contains('hidden')) {
            return; // Disable controls if game over modal is visible
        }

        let dx = 0, dy = 0;
        if (e.key === 'w' || e.key === 'W' || e.key === 'ArrowUp') dy = 1;
        else if (e.key === 's' || e.key === 'S' || e.key === 'ArrowDown') dy = -1;
        else if (e.key === 'a' || e.key === 'A' || e.key === 'ArrowLeft') dx = -1;
        else if (e.key === 'd' || e.key === 'D' || e.key === 'ArrowRight') dx = 1;

        if (dx !== 0 || dy !== 0) {
            socket.emit('move', { dx, dy });
        }
    }
});

document.querySelectorAll('#controls button').forEach(btn => {
    btn.addEventListener('click', () => {
        const dx = parseInt(btn.dataset.dx);
        const dy = parseInt(btn.dataset.dy);
        socket.emit('move', { dx, dy });
    });
});

// Rendering
function draw() {
    // Clear canvas
    ctx.fillStyle = '#050510';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw Grid Lines
    ctx.strokeStyle = '#2a2a40';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x <= canvas.width; x += SCALE) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
    }
    for (let y = 0; y <= canvas.height; y += SCALE) {
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
    }
    ctx.stroke();

    // Draw Origin
    ctx.fillStyle = '#2a2a40';
    ctx.fillRect(OFFSET_X - 2, OFFSET_Y - 2, 4, 4);

    // Draw Players
    for (const [username, pos] of Object.entries(players)) {
        // Center in cell: (x * SCALE) + (SCALE / 2)
        // Invert Y for cartesian coords
        const screenX = OFFSET_X + (pos.x * SCALE) + (SCALE / 2);
        const screenY = OFFSET_Y - (pos.y * SCALE) - (SCALE / 2);

        const isMe = username === myUsername;
        const color = isMe ? '#00f3ff' : '#ff0055';
        const glow = isMe ? 15 : 10;

        // Glow effect
        ctx.shadowBlur = glow;
        ctx.shadowColor = color;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(screenX, screenY, SCALE / 3, 0, Math.PI * 2);
        ctx.fill();

        // Reset glow for text
        ctx.shadowBlur = 0;

        ctx.fillStyle = '#e0e0e0';
        ctx.font = '10px "Orbitron", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(username, screenX, screenY - 15);
    }
}

function log(msg) {
    const div = document.createElement('div');
    div.textContent = msg;
    logContainer.prepend(div);
    if (logContainer.children.length > 5) {
        logContainer.lastChild.remove();
    }
}

// Game Over Logic
function showGameOver(winner) {
    const modal = document.getElementById('game-over-modal');
    const title = document.getElementById('game-over-title');
    const message = document.getElementById('game-over-message');

    modal.classList.remove('hidden');

    if (winner === myUsername) {
        title.textContent = "VICTORY!";
        title.className = "victory-title";
        message.textContent = "YOU FOUND THE TREASURE!";
    } else {
        title.textContent = "GAME OVER";
        title.className = "defeat-title";
        message.textContent = `${winner} found the treasure!`;
    }
}

document.getElementById('play-again-btn').addEventListener('click', () => {
    location.reload();
});
