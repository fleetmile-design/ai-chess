# -*- coding: utf-8 -*-
"""
elo_manager.py — ELO Rating & Statistics Module for the AI Chess tournament.

Manages player ratings, match history, and leaderboard data using a JSON file
for persistent storage. All file I/O is thread-safe via a threading.Lock().
"""

import json
import os
import threading
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_FILE = os.getenv("TOURNAMENT_DATA_FILE", "tournament_data.json")
K_FACTOR = float(os.getenv("ELO_K_FACTOR", "32"))
DEFAULT_ELO = float(os.getenv("DEFAULT_ELO", "1200"))

# Known models auto-registered on first load
_KNOWN_MODELS = [
    ("mock", "Mock AI"),
    ("gpt-4o", "GPT-4o"),
    ("gpt-4o-mini", "GPT-4o Mini"),
    ("gemini-2.0-flash", "Gemini 2.0 Flash"),
    ("gemini-1.5-pro", "Gemini 1.5 Pro"),
    ("claude-3-5-sonnet", "Claude 3.5 Sonnet"),
    ("llama-3", "Llama 3"),
]

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_lock = threading.Lock()
_data: dict = {"players": {}, "matches": []}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _empty_player(name: str) -> dict:
    return {
        "name": name,
        "elo": int(DEFAULT_ELO),
        "games": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "history": [],
    }


def _expected_score(player_elo: float, opponent_elo: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((opponent_elo - player_elo) / 400.0))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_data() -> None:
    """Load tournament data from JSON file. Creates the file if it is missing."""
    global _data
    with _lock:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as fh:
                    _data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                _data = {"players": {}, "matches": []}
        else:
            _data = {"players": {}, "matches": []}

        # Ensure top-level keys exist
        _data.setdefault("players", {})
        _data.setdefault("matches", [])

        # Auto-register known models
        for model_id, display_name in _KNOWN_MODELS:
            if model_id not in _data["players"]:
                _data["players"][model_id] = _empty_player(display_name)

        _save_locked()


def save_data() -> None:
    """Persist current tournament data to the JSON file (thread-safe)."""
    with _lock:
        _save_locked()


def _save_locked() -> None:
    """Internal save — must be called while holding _lock."""
    with open(DATA_FILE, "w", encoding="utf-8") as fh:
        json.dump(_data, fh, ensure_ascii=False, indent=2)


def get_or_create_player(model_name: str) -> dict:
    """Return a player dict by model name, creating it (ELO 1200) if new."""
    with _lock:
        if model_name not in _data["players"]:
            _data["players"][model_name] = _empty_player(model_name)
            _save_locked()
        return _data["players"][model_name]


def update_elo(white_model: str, black_model: str, result: str) -> dict:
    """
    Update ELO ratings after a game.

    Parameters
    ----------
    white_model : str  — Model name for the white player.
    black_model : str  — Model name for the black player.
    result      : str  — "1-0" (white wins), "0-1" (black wins),
                         "1/2-1/2" (draw), or "error" (no rating change).

    Returns
    -------
    dict with old/new ELO for both players:
        {
            "white": {"old_elo": ..., "new_elo": ..., "change": ...},
            "black": {"old_elo": ..., "new_elo": ..., "change": ...},
        }
    """
    with _lock:
        # Ensure both players exist
        if white_model not in _data["players"]:
            _data["players"][white_model] = _empty_player(white_model)
        if black_model not in _data["players"]:
            _data["players"][black_model] = _empty_player(black_model)

        wp = _data["players"][white_model]
        bp = _data["players"][black_model]

        old_white_elo = wp["elo"]
        old_black_elo = bp["elo"]

        if result == "error":
            # No rating change on error; still record the match
            change_white = 0
            change_black = 0
            actual_white = None
            actual_black = None
        else:
            if result == "1-0":
                actual_white, actual_black = 1.0, 0.0
            elif result == "0-1":
                actual_white, actual_black = 0.0, 1.0
            else:  # draw / 1/2-1/2
                actual_white, actual_black = 0.5, 0.5

            exp_white = _expected_score(old_white_elo, old_black_elo)
            exp_black = _expected_score(old_black_elo, old_white_elo)

            change_white = round(K_FACTOR * (actual_white - exp_white))
            change_black = round(K_FACTOR * (actual_black - exp_black))

            wp["elo"] = max(100, old_white_elo + change_white)
            bp["elo"] = max(100, old_black_elo + change_black)

        # Update game counters
        wp["games"] += 1
        bp["games"] += 1

        if result == "1-0":
            wp["wins"] += 1
            bp["losses"] += 1
        elif result == "0-1":
            wp["losses"] += 1
            bp["wins"] += 1
        elif result == "1/2-1/2":
            wp["draws"] += 1
            bp["draws"] += 1

        # History entries
        ts = datetime.now(timezone.utc).isoformat()
        wp["history"].append({
            "opponent": black_model,
            "result": result,
            "elo_change": change_white,
            "timestamp": ts,
        })
        bp["history"].append({
            "opponent": white_model,
            "result": result,
            "elo_change": change_black,
            "timestamp": ts,
        })

        # Match log
        _data["matches"].append({
            "white": white_model,
            "black": black_model,
            "result": result,
            "white_elo_before": old_white_elo,
            "black_elo_before": old_black_elo,
            "white_elo_after": wp["elo"],
            "black_elo_after": bp["elo"],
            "timestamp": ts,
        })

        _save_locked()

        return {
            "white": {
                "old_elo": old_white_elo,
                "new_elo": wp["elo"],
                "change": change_white,
            },
            "black": {
                "old_elo": old_black_elo,
                "new_elo": bp["elo"],
                "change": change_black,
            },
        }


def get_leaderboard() -> list:
    """Return all players sorted by ELO descending."""
    with _lock:
        players = []
        for model_id, p in _data["players"].items():
            games = p.get("games", 0)
            wins = p.get("wins", 0)
            win_pct = round(wins / games * 100, 1) if games > 0 else None
            players.append({
                "model_id": model_id,
                "name": p.get("name", model_id),
                "elo": p.get("elo", int(DEFAULT_ELO)),
                "games": games,
                "wins": wins,
                "losses": p.get("losses", 0),
                "draws": p.get("draws", 0),
                "win_pct": win_pct,
            })
        players.sort(key=lambda x: x["elo"], reverse=True)
        return players


def get_match_history(limit: int = 20) -> list:
    """Return the last ``limit`` matches."""
    with _lock:
        return list(_data["matches"][-limit:])


# ---------------------------------------------------------------------------
# Initialise on import
# ---------------------------------------------------------------------------
load_data()
