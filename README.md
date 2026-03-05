# AI Šachmatai — Gyvas mačas 🎭♟

> **Lietuviškai** | **English below**

---

## 🇱🇹 Aprašymas

**AI Šachmatai** — tai realiuoju laiku veikianti šachmatų programa, kurioje du dirbtinio intelekto žaidėjai žaidžia vienas prieš kitą. Vartotojas stebi gyvą partiją naršyklėje, matydamas lentą, AI minčių srautą ir teisėjo žurnalą.

Programa naudoja:
- **Python** (Flask + Flask-SocketIO) kaip serverio pusę (Teisėjas / Referee).
- **python-chess** legalių ėjimų skaičiavimui ir žaidimo būsenos valdymui.
- **chessboard.js** ir **chess.js** interaktyviai šachmatų lentai naršyklėje.
- **Socket.IO** (WebSockets) realiojo laiko komunikacijai tarp serverio ir naršyklės.

---

## 🇬🇧 Description

**AI Chess — Live Match** is a real-time chess application where two AI players compete against each other. The user watches the live game in the browser, seeing the board, each AI's stream of thought, and a referee log.

The app uses:
- **Python** (Flask + Flask-SocketIO) as the backend (the Referee / Teisėjas).
- **python-chess** for legal move generation and game-state management.
- **chessboard.js** and **chess.js** for the interactive chess board in the browser.
- **Socket.IO** (WebSockets) for real-time communication between server and browser.

---

## 🚀 Setup & Running

### 1. Clone and install dependencies

```bash
git clone https://github.com/fleetmile-design/ai-chess.git
cd ai-chess
pip install -r requirements.txt
```

### 2. Configure environment (optional)

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

| Variable         | Default | Description                                      |
|-----------------|---------|--------------------------------------------------|
| `AI_MODEL_WHITE` | `mock`  | Model for White AI (`mock`, `gpt-4o`, `gemini-1.5-pro`, …) |
| `AI_MODEL_BLACK` | `mock`  | Model for Black AI                               |
| `MOVE_DELAY`     | `2`     | Seconds to pause between moves                   |
| `OPENAI_API_KEY` | —       | Required if using an OpenAI model                |
| `GEMINI_API_KEY` | —       | Required if using a Gemini model                 |

> **No API keys needed for the mock AI** — the app works out of the box.

### 3. Run the server

```bash
python server.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser and click **"Pradėti žaidimą"** (Start Game).

---

## 🤖 Using Real AI Models

The `ai_player.py` file contains commented-out integration examples for:

- **OpenAI** (e.g. `gpt-4o`): set `AI_MODEL_WHITE=gpt-4o` and `OPENAI_API_KEY=...` in `.env`.
- **Google Gemini** (e.g. `gemini-1.5-pro`): set `AI_MODEL_WHITE=gemini-1.5-pro` and `GEMINI_API_KEY=...` in `.env`.

Uncomment the relevant function in `ai_player.py` and set the corresponding model name and API key.

---

## 🖥️ UI Layout

```
┌─────────────────────────────────────────────────────────┐
│            ♟ AI Šachmatai — Gyvas mačas ♟               │  ← Header
├──────────────┬──────────────────────┬───────────────────┤
│  ⬜ Baltasis │   [▶ Start button]   │  ⬛ Juodasis      │
│    AI log    │                      │    AI log          │
│              │   [Chess Board]      │                    │
│  Scrolling   │                      │  Scrolling         │
│  terminal    │   [Status bar]       │  terminal          │
│  log panel   │                      │  log panel         │
│   (blue      │                      │   (grey            │
│   accent)    │                      │   accent)          │
├──────────────┴──────────────────────┴───────────────────┤
│  ⚖️ Teisėjas — Žaidimo žurnalas (referee log, gold)      │
└─────────────────────────────────────────────────────────┘
```

- **Left panel** — White AI's thinking stream (light blue accent).
- **Center** — Live chess board (animated moves), Start button, status bar showing whose turn, move number, check indicator.
- **Right panel** — Black AI's thinking stream (grey accent).
- **Bottom (full width)** — Referee/Judge log with game events, move validation messages, and game-over announcement (gold accent).

All log panels auto-scroll to the latest entry and include timestamps.

---

## 📁 Project Structure

```
ai-chess/
├── server.py          # Flask + Socket.IO server, Referee (Teisėjas) logic
├── ai_player.py       # AI API integration (mock + commented OpenAI/Gemini)
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── templates/
│   └── index.html     # Main HTML page
└── static/
    ├── css/
    │   └── style.css  # CSS Grid layout and styling
    └── js/
        └── app.js     # Socket.IO handlers, board init, log rendering
```