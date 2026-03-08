# -*- coding: utf-8 -*-
"""
server.py — Main Flask + Socket.IO server for the AI Chess application.

Run:
    pip install -r requirements.txt
    python server.py

The server:
  - Serves the HTML frontend via Flask.
  - Manages a game loop in a background thread.
  - Communicates real-time updates to the browser via Socket.IO (WebSockets).
"""

import os
import time
import threading

import chess
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit

from ai_player import gauti_ai_ejima
import elo_manager

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

AI_MODEL_WHITE = os.getenv("AI_MODEL_WHITE", "mock")
AI_MODEL_BLACK = os.getenv("AI_MODEL_BLACK", "mock")
MOVE_DELAY = float(os.getenv("MOVE_DELAY", "2"))

# ---------------------------------------------------------------------------
# Flask / Socket.IO initialisation
# ---------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "ai-chess-secret")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------------------------------------------------------------------
# Global game state
# ---------------------------------------------------------------------------
_game_lock = threading.Lock()
_game_running = False


# ---------------------------------------------------------------------------
# Helper: emit a log message to one of the three panels
# ---------------------------------------------------------------------------
def _log(langas: str, zinute: str) -> None:
    """Emit a log_update event to the given panel."""
    socketio.emit("log_update", {"langas": langas, "zinute": zinute})


# ---------------------------------------------------------------------------
# Game loop (runs in a background thread)
# ---------------------------------------------------------------------------
def _game_loop(white_model: str, black_model: str) -> None:
    global _game_running

    board = chess.Board()
    move_number = 0

    _log("teisejas", "Teisejas: zaidimas pradetas. Pradine pozicija nustatyta.")
    socketio.emit("board_update", {"fen": board.fen(), "last_move": None})

    while not board.is_game_over():
        with _game_lock:
            if not _game_running:
                _log("teisejas", "Teisejas: zaidimas sustabdytas.")
                return

        # Determine whose turn it is
        if board.turn == chess.WHITE:
            player_color = "white"
            model_name = white_model
            langas = "balti_ai"
            color_lt = "Baltieji"
        else:
            player_color = "black"
            model_name = black_model
            langas = "juodi_ai"
            color_lt = "Juodieji"

        move_number += 1
        legal_moves_uci = [m.uci() for m in board.legal_moves]

        _log(
            "teisejas",
            "Ejimas #" + str(move_number) + " -- " + color_lt + " galvoja... (" + str(len(legal_moves_uci)) + " legalus ejimiai)",
        )

        # Allow up to 3 attempts per turn
        chosen_move_uci = None
        for attempt in range(1, 4):
            try:
                result = gauti_ai_ejima(model_name, board.fen(), player_color, legal_moves_uci)
                mastymas = result.get("mastymas", "")
                ejimas = result.get("ejimas", "").strip()
            except Exception as exc:  # noqa: BLE001
                _log("teisejas", "Klaida gaunant AI atsakyma (" + str(attempt) + "/3): " + str(exc))
                continue

            # Log AI thinking to its own panel
            _log(langas, "Mastymas: " + mastymas)
            _log(langas, "Pasirinktas ejimas: " + ejimas)

            # Validate the move
            try:
                move = chess.Move.from_uci(ejimas)
            except chess.InvalidMoveError:
                _log("teisejas", "Neteisetas ejimas (bandymas " + str(attempt) + "/3): '" + ejimas + "' - netinkamas UCI formatas.")
                continue

            if move in board.legal_moves:
                chosen_move_uci = ejimas
                break
            else:
                _log(
                    "teisejas",
                    "Neteisetas ejimas (bandymas " + str(attempt) + "/3): '" + ejimas + "' nera tarp legaliu ejimu.",
                )

        if chosen_move_uci is None:
            _log("teisejas", color_lt + " nepateike teiseto ejimo po 3 bandymu. Zaidimas nutraukiamas.")
            socketio.emit("game_over", {"result": "error", "reason": color_lt + " nepateike teiseto ejimo."})
            # Update ELO for error result
            elo_result = elo_manager.update_elo(white_model, black_model, "error")
            socketio.emit("leaderboard_update", elo_manager.get_leaderboard())
            break

        # Push the move
        move_obj = chess.Move.from_uci(chosen_move_uci)
        san_move = board.san(move_obj)
        board.push(move_obj)

        from_sq = chosen_move_uci[:2]
        to_sq = chosen_move_uci[2:4]

        _log("teisejas", color_lt + ": " + san_move + " (" + chosen_move_uci + ")")
        socketio.emit(
            "board_update",
            {
                "fen": board.fen(),
                "last_move": {"from": from_sq, "to": to_sq},
            },
        )

        # Brief pause between moves
        time.sleep(MOVE_DELAY)

    # Game over
    if board.is_game_over():
        result = board.result()
        if board.is_checkmate():
            winner = "Baltieji" if board.turn == chess.BLACK else "Juodieji"
            reason = "Sachmatas! " + winner + " laimi."
        elif board.is_stalemate():
            reason = "Patas - lygiosios."
        elif board.is_insufficient_material():
            reason = "Nepakanka medzagos - lygiosios."
        elif board.is_seventyfive_moves():
            reason = "75 ejimu taisykle - lygiosios."
        elif board.is_fivefold_repetition():
            reason = "Penkeriopa pozicijos kartotine - lygiosios."
        else:
            reason = "Zaidimas baigtas."

        _log("teisejas", "Zaidimas baigtas: " + result + " - " + reason)
        socketio.emit("game_over", {"result": result, "reason": reason})

        # Update ELO ratings and broadcast leaderboard
        elo_result = elo_manager.update_elo(white_model, black_model, result)
        w_change = elo_result["white"]["change"]
        b_change = elo_result["black"]["change"]
        w_sign = "+" if w_change >= 0 else ""
        b_sign = "+" if b_change >= 0 else ""
        _log(
            "teisejas",
            "ELO: " + white_model + " " + w_sign + str(w_change)
            + " (" + str(elo_result["white"]["new_elo"]) + ") | "
            + black_model + " " + b_sign + str(b_change)
            + " (" + str(elo_result["black"]["new_elo"]) + ")",
        )
        socketio.emit("leaderboard_update", elo_manager.get_leaderboard())

    with _game_lock:
        _game_running = False


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/leaderboard")
def api_leaderboard():
    return jsonify(elo_manager.get_leaderboard())


# ---------------------------------------------------------------------------
# Socket.IO events
# ---------------------------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    emit("leaderboard_update", elo_manager.get_leaderboard())


@socketio.on("request_leaderboard")
def handle_request_leaderboard():
    emit("leaderboard_update", elo_manager.get_leaderboard())


@socketio.on("start_game")
def handle_start_game(data=None):
    global _game_running

    if data is None:
        data = {}

    white_model = data.get("white_model") or AI_MODEL_WHITE
    black_model = data.get("black_model") or AI_MODEL_BLACK

    with _game_lock:
        if _game_running:
            emit("log_update", {"langas": "teisejas", "zinute": "Zaidimas jau vyksta!"})
            return
        _game_running = True

    thread = threading.Thread(target=_game_loop, args=(white_model, black_model), daemon=True)
    thread.start()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
