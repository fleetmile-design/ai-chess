# -*- coding: utf-8 -*-
"""
ai_player.py — AI player module for the AI Chess application.

Provides the gauti_ai_ejima() function that returns a chosen chess move and
Lithuanian-language thinking text for a given board position.

The default implementation is a MOCK that works without any API keys.
Commented-out sections show how to integrate OpenAI or Google Gemini APIs.
"""

import json
import random

# ---------------------------------------------------------------------------
# System-prompt template (do not modify the structure)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """You are an elite AI Chess Grandmaster playing a competitive match against another AI.
You will be provided with the current board state in FEN format and a list of all strictly legal moves.

Current FEN: {fen}
Your playing color: {color}
Legal moves you can choose from (in UCI format): {legal_moves}

Your tasks:
1. Analyze the board deeply. Identify threats, opportunities, and positional advantages.
2. Select the absolute best legal move ONLY from the provided "Legal moves" list.
3. Explain your thought process clearly and analytically in Lithuanian.

CRITICAL REQUIREMENT:
You MUST respond ONLY with a valid JSON object. Do not include any markdown formatting (like ```json), greetings, or any conversational text outside the JSON structure.

Required JSON structure:
{{
  "mastymas": "Tavo detali situacijos analizė ir paaiškinimas, kodėl renkiesi šį ėjimą (Lietuvių kalba).",
  "ejimas": "your_chosen_move_here"
}}"""

# ---------------------------------------------------------------------------
# Lithuanian placeholder thinking phrases for the mock AI
# ---------------------------------------------------------------------------
_MOCK_THINKING_PHRASES = [
    "Analizuoju poziciją. Pasirinktas ėjimas atrodo stipriausias šioje situacijoje, "
    "nes gerina mano figūrų išsidėstymą ir kontroliuoja centrinę zoną.",
    "Apsvarstęs visas galimybes, pasirenkau šį ėjimą — jis kuria spaudimą priešininko "
    "pozicijai ir atveria kelius mano aktyviai žaidybai.",
    "Pozicija yra subalansuota, tačiau šis ėjimas suteikia man laikiną iniciatyvą. "
    "Svarbu netrikdyti koordinacijos tarp figūrų.",
    "Strategiškai šis ėjimas gerina mano įtvirtintų figūrų poziciją ir riboja "
    "priešininko galimybes kitame ėjime.",
    "Matau galimybę sustiprinti centro kontrolę. Šis ėjimas yra logiškas tolesnei "
    "žaidimo eigai ir saugo mano karaliaus saugumą.",
    "Atliekant šį ėjimą siekiama aktyvinti mano bokštą ir sukurti grėsmes "
    "priešininko silpnosioms pėstininkų struktūroms.",
    "Šis ėjimas yra orientuotas į ilgalaikę strateginę naudą — gyvybingas "
    "erdvės užgrobimas centro sektoriuje.",
    "Priešininko pozicijoje matau silpnąją vietą. Šiuo ėjimu skverbiuosi "
    "į jo stovyklą, kol dar nevėlu.",
]


def gauti_ai_ejima(model_name: str, fen: str, player_color: str, legal_moves: list) -> dict:
    """
    Returns an AI-chosen chess move for the given position.

    Parameters
    ----------
    model_name   : str   – Model identifier, e.g. "mock", "gpt-4o", "gemini-1.5-pro".
    fen          : str   – Current board state in FEN notation.
    player_color : str   – "white" or "black".
    legal_moves  : list  – List of legal moves in UCI format (e.g. ["e2e4", "d2d4", ...]).

    Returns
    -------
    dict with keys:
        "mastymas" – AI's reasoning in Lithuanian.
        "ejimas"   – Chosen move in UCI format.
    """
    if not legal_moves:
        return {"mastymas": "Nėra legalių ėjimų.", "ejimas": ""}

    model_lower = model_name.lower()

    if model_lower == "mock":
        return _mock_ai(fen, player_color, legal_moves)

    # ------------------------------------------------------------------
    # OpenAI integration (commented out — requires OPENAI_API_KEY)
    # ------------------------------------------------------------------
    # elif model_lower.startswith("gpt"):
    #     return _openai_ai(model_name, fen, player_color, legal_moves)

    # ------------------------------------------------------------------
    # Google Gemini integration (commented out — requires GEMINI_API_KEY)
    # ------------------------------------------------------------------
    # elif model_lower.startswith("gemini"):
    #     return _gemini_ai(model_name, fen, player_color, legal_moves)

    # Fallback to mock if model is unknown
    return _mock_ai(fen, player_color, legal_moves)


# ---------------------------------------------------------------------------
# Mock AI (no API key required)
# ---------------------------------------------------------------------------

def _mock_ai(fen: str, player_color: str, legal_moves: list) -> dict:
    """Simulated AI: picks a random legal move with placeholder Lithuanian text."""
    chosen_move = random.choice(legal_moves)
    thinking = random.choice(_MOCK_THINKING_PHRASES)
    return {"mastymas": thinking, "ejimas": chosen_move}


# ---------------------------------------------------------------------------
# OpenAI integration (commented out)
# ---------------------------------------------------------------------------
# import os
# import requests
#
# def _openai_ai(model_name: str, fen: str, player_color: str, legal_moves: list) -> dict:
#     """Calls the OpenAI Chat Completions API."""
#     api_key = os.getenv("OPENAI_API_KEY", "")
#     prompt = SYSTEM_PROMPT_TEMPLATE.format(
#         fen=fen,
#         color=player_color,
#         legal_moves=", ".join(legal_moves),
#     )
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json",
#     }
#     payload = {
#         "model": model_name,
#         "messages": [{"role": "user", "content": prompt}],
#         "temperature": 0.7,
#     }
#     response = requests.post(
#         "https://api.openai.com/v1/chat/completions",
#         headers=headers,
#         json=payload,
#         timeout=30,
#     )
#     response.raise_for_status()
#     content = response.json()["choices"][0]["message"]["content"]
#     return json.loads(content)


# ---------------------------------------------------------------------------
# Google Gemini integration (commented out)
# ---------------------------------------------------------------------------
# import os
# import requests
#
# def _gemini_ai(model_name: str, fen: str, player_color: str, legal_moves: list) -> dict:
#     """Calls the Google Gemini GenerateContent API."""
#     api_key = os.getenv("GEMINI_API_KEY", "")
#     prompt = SYSTEM_PROMPT_TEMPLATE.format(
#         fen=fen,
#         color=player_color,
#         legal_moves=", ".join(legal_moves),
#     )
#     url = (
#         f"https://generativelanguage.googleapis.com/v1beta/models/"
#         f"{model_name}:generateContent?key={api_key}"
#     )
#     payload = {
#         "contents": [{"parts": [{"text": prompt}]}],
#         "generationConfig": {"temperature": 0.7},
#     }
#     response = requests.post(url, json=payload, timeout=30)
#     response.raise_for_status()
#     text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
#     return json.loads(text)
