/* ============================================================
   app.js — AI Šachmatai frontend logic
   ============================================================ */

(function () {
  'use strict';

  // ── Splash overlay ────────────────────────────────────────
  var splashOverlay = document.getElementById('splash-overlay');
  var splashBtn     = document.getElementById('splash-enter-btn');

  if (splashOverlay && splashBtn) {
    splashBtn.addEventListener('click', function () {
      splashOverlay.classList.add('hidden');
    });
  }

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
  var startBtn      = document.getElementById('start-btn');
  var newGameBtn    = document.getElementById('new-game-btn');
  var statusBar     = document.getElementById('status-bar');
  var overlay       = document.getElementById('game-over-overlay');
  var overlayResult = document.getElementById('game-over-result');
  var overlayReason = document.getElementById('game-over-reason');

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
    startBtn.textContent = '↺ Naujas žaidimas';
    statusBar.textContent = 'Žaidimas baigtas: ' + resultText;
  });

  // ── Button handlers ────────────────────────────────────────

  function startGame() {
    // Reset board and game state
    game.reset();
    board.start(false);
    removeHighlights();
    statusBar.textContent = 'Žaidimas pradedamas…';

    // Clear all log panels
    Object.values(logPanels).forEach(function (panel) {
      panel.innerHTML = '';
    });

    // Hide game-over overlay
    overlay.classList.add('hidden');

    // Disable start button while game is running
    startBtn.disabled = true;
    startBtn.textContent = '▶ Žaidimas vyksta…';

    // Notify server
    socket.emit('start_game');
  }

  startBtn.addEventListener('click', startGame);
  newGameBtn.addEventListener('click', function () {
    overlay.classList.add('hidden');
    startGame();
  });

  // ── Initial status ─────────────────────────────────────────
  updateStatus();

})();
