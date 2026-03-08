/* ============================================================
   app.js — AI Šachmatai frontend logic
   ============================================================ */

(function () {
  'use strict';

  // ── Socket.IO ──────────────────────────────────────────────
  var socket = io();

  // ── chess.js game (tracks position for status bar) ─────────
  var game = new Chess();

  // ── chessboard.js board ────────────────────────────────────
  var boardConfig = {
    position: 'start',
    draggable: false,
    pieceTheme: '/static/img/chesspieces/wikipedia/{piece}.png',
  };
  var board = ChessBoard('chess-board', boardConfig);

  // ── DOM references ─────────────────────────────────────────
  var startBtn        = document.getElementById('start-btn');
  var newGameBtn      = document.getElementById('new-game-btn');
  var statusBar       = document.getElementById('status-bar');
  var overlay         = document.getElementById('game-over-overlay');
  var overlayResult   = document.getElementById('game-over-result');
  var overlayReason   = document.getElementById('game-over-reason');
  var whiteModelSelect = document.getElementById('white-model-select');
  var blackModelSelect = document.getElementById('black-model-select');
  var leaderboardBody  = document.getElementById('leaderboard-body');

  var logPanels = {
    teisejas: document.getElementById('teisejas-log'),
    balti_ai: document.getElementById('balti-ai-log'),
    juodi_ai: document.getElementById('juodi-ai-log'),
  };

  // Track the currently highlighted squares so we can remove them
  var highlightedSquares = [];

  // ── Helpers ────────────────────────────────────────────────

  function timestamp() {
    var now = new Date();
    var hh = String(now.getHours()).padStart(2, '0');
    var mm = String(now.getMinutes()).padStart(2, '0');
    var ss = String(now.getSeconds()).padStart(2, '0');
    return hh + ':' + mm + ':' + ss;
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }

  function appendLog(panelId, text) {
    var container = logPanels[panelId];
    if (!container) return;

    var entry = document.createElement('p');
    entry.className = 'log-entry';

    var ts = document.createElement('span');
    ts.className = 'log-timestamp';
    ts.textContent = '[' + timestamp() + ']';

    var msg = document.createTextNode(' ' + text);

    entry.appendChild(ts);
    entry.appendChild(msg);
    container.appendChild(entry);

    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
  }

  function updateStatus() {
    var turn = game.turn() === 'w' ? '⬜ Baltieji' : '⬛ Juodieji';
    var moveCount = Math.ceil(game.history().length / 2);
    var extra = '';
    if (game.in_check()) extra = ' ♦ Šachas!';
    if (game.in_checkmate()) extra = ' ✗ Šachmatas!';
    if (game.in_stalemate()) extra = ' = Patas';
    statusBar.textContent = turn + ' ėjimas #' + (moveCount + 1) + extra;
  }

  function removeHighlights() {
    highlightedSquares.forEach(function (sq) {
      var el = document.querySelector('.square-' + sq);
      if (el) {
        el.classList.remove('highlight-from', 'highlight-to');
      }
    });
    highlightedSquares = [];
  }

  function highlightMove(fromSq, toSq) {
    removeHighlights();
    var fromEl = document.querySelector('.square-' + fromSq);
    var toEl   = document.querySelector('.square-' + toSq);
    if (fromEl) { fromEl.classList.add('highlight-from'); highlightedSquares.push(fromSq); }
    if (toEl)   { toEl.classList.add('highlight-to');   highlightedSquares.push(toSq);   }
  }

  // ── Socket.IO event handlers ───────────────────────────────

  socket.on('board_update', function (data) {
    // Load the new FEN into chess.js (for status tracking)
    game.load(data.fen);

    // Animate board to new position
    board.position(data.fen, true);

    // Highlight last move squares
    if (data.last_move) {
      // Small delay so the animation starts before highlighting
      setTimeout(function () {
        highlightMove(data.last_move.from, data.last_move.to);
      }, 50);
    } else {
      removeHighlights();
    }

    updateStatus();
  });

  socket.on('log_update', function (data) {
    appendLog(data.langas, data.zinute);
  });

  socket.on('game_over', function (data) {
    var resultText = data.result || '';
    var reasonText = data.reason || '';

    overlayResult.textContent = resultText;
    overlayReason.textContent = reasonText;
    overlay.classList.remove('hidden');

    startBtn.disabled = false;
    startBtn.textContent = 'Naujas zaidimas';
    whiteModelSelect.disabled = false;
    blackModelSelect.disabled = false;
    statusBar.textContent = 'Zaidimas baigtas: ' + resultText;
  });

  socket.on('leaderboard_update', function (players) {
    if (!leaderboardBody) return;
    leaderboardBody.innerHTML = '';
    players.forEach(function (p, index) {
      var rank = index + 1;
      var winPct = p.win_pct !== null && p.win_pct !== undefined ? p.win_pct.toFixed(1) + '%' : '&mdash;';
      var winPctClass = '';
      if (p.win_pct !== null && p.win_pct !== undefined) {
        if (p.win_pct > 60) winPctClass = 'win-pct-high';
        else if (p.win_pct >= 40) winPctClass = 'win-pct-mid';
        else winPctClass = 'win-pct-low';
      }
      var tr = document.createElement('tr');
      if (rank === 1) tr.classList.add('rank-first');
      tr.innerHTML =
        '<td class="rank-cell">' + rank + '</td>' +
        '<td class="name-cell">' + escapeHtml(p.name) + '</td>' +
        '<td class="elo-cell">' + p.elo + '</td>' +
        '<td>' + (p.games || '&mdash;') + '</td>' +
        '<td class="wins-cell">' + (p.wins || 0) + '</td>' +
        '<td class="losses-cell">' + (p.losses || 0) + '</td>' +
        '<td>' + (p.draws || 0) + '</td>' +
        '<td class="' + winPctClass + '">' + winPct + '</td>';
      leaderboardBody.appendChild(tr);
    });
  });

  socket.on('connect', function () {
    socket.emit('request_leaderboard');
  });

  // ── Button handlers ────────────────────────────────────────

  function startGame() {
    // Reset board and game state
    game.reset();
    board.start(false);
    removeHighlights();
    statusBar.textContent = 'Zaidimas pradedamas...';

    // Clear all log panels
    Object.values(logPanels).forEach(function (panel) {
      panel.innerHTML = '';
    });

    // Hide game-over overlay
    overlay.classList.add('hidden');

    // Disable start button and model selectors while game is running
    startBtn.disabled = true;
    startBtn.textContent = 'Zaidimas vyksta...';
    whiteModelSelect.disabled = true;
    blackModelSelect.disabled = true;

    // Notify server with selected models
    socket.emit('start_game', {
      white_model: whiteModelSelect.value,
      black_model: blackModelSelect.value,
    });
  }

  startBtn.addEventListener('click', startGame);
  newGameBtn.addEventListener('click', function () {
    overlay.classList.add('hidden');
    whiteModelSelect.disabled = false;
    blackModelSelect.disabled = false;
    startGame();
  });

  // ── Initial status ─────────────────────────────────────────
  updateStatus();

})();
