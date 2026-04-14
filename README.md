# 🥏 FUFA Disc Golf League — Scorecard App

Upload a UDisc scorecard screenshot → Claude reads it → data goes into Google Sheets.

## Quick Start

### Prerequisites
- Python 3.12+ (via pyenv)
- Poetry 2.0
- Node.js 18+
- Anthropic API key (console.anthropic.com)
- Google credentials (see GOOGLE_SETUP.md)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
poetry install

# Copy and fill in env file
cp .env .env.local  # or just edit .env directly
# Set ANTHROPIC_API_KEY and GOOGLE_SHEET_ID

# Start API server
poetry run uvicorn main:app --reload --port 8000
# → API docs at http://localhost:8000/docs
```

### 2. Frontend Setup

```bash
cd frontend

npm install
npm run dev
# → App at http://localhost:5173
```

### 3. Google Sheets
See [GOOGLE_SETUP.md](./GOOGLE_SETUP.md) for step-by-step Google Cloud setup.

---

## How It Works

1. **Upload**: Drop a UDisc scorecard screenshot into the app
2. **Parse**: Claude Vision reads every hole score, player name, course info, ace indicators
3. **Review**: Inspect the parsed data in an editable table — fix any errors
4. **Submit**: One click writes all player rows to Google Sheets

---

## Google Sheet Structure

The app auto-creates a `Rounds` tab with these columns:

| Date | Course | Tees | Player | H1–H18 | Total | +/- Par | Par | Has_Ace | Ace_Holes | ... |

---

## Testing the Parser Directly

```bash
cd backend
poetry run python scorecard_parser.py /path/to/scorecard.jpg
```

---

## Project Structure

```
disc-golf-scorecard/
├── CLAUDE.md                 ← Context for Claude Code in Cursor
├── GOOGLE_SETUP.md           ← Google Cloud setup guide
├── credentials.json          ← Your service account key (gitignored)
├── backend/
│   ├── main.py               ← FastAPI routes
│   ├── scorecard_parser.py   ← Claude Vision parsing
│   ├── sheets_client.py      ← Google Sheets integration
│   ├── scoring_rules.py      ← Phase 2: winner/points/handicaps
│   ├── pyproject.toml
│   └── .env
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── components/
    │       ├── ImageUploader.jsx
    │       └── ScorecardTable.jsx
    └── package.json
```

---

## Phase 2 Roadmap

- [ ] Winner determination with FUFA tiebreaker rules
- [ ] Season points leaderboard
- [ ] Handicap calculation
- [ ] Ace tracking / hall of fame
- [ ] Season standings dashboard
- [ ] Historical round browser
