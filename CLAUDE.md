# FUFA Disc Golf League — Scorecard App

## Project Purpose
This app parses UDisc scorecard images using Claude Vision, extracts structured round data, and writes it to a Google Sheet for the FUFA disc golf league's 2026 season tracking.

## Architecture
- **Backend**: Python + FastAPI (`/backend`)
- **Frontend**: React + Vite (`/frontend`)
- **AI**: Anthropic Claude claude-sonnet-4-20250514 vision for scorecard parsing
- **Storage**: Google Sheets via gspread

## Running Locally
```bash
# Terminal 1 — Backend
cd backend
poetry install
poetry run uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Environment Variables (backend/.env)
```
ANTHROPIC_API_KEY=your_key_here
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CREDENTIALS_PATH=../credentials.json
```

## UDisc Scorecard Format (from real images)
- Header: Course name, tee config (e.g. "Red Tees", "Short to Short")
- Row 1: Hole numbers 1–18
- Row 2: Distances in feet per hole
- Row 3: Par per hole
- Player rows: Name + score per hole + "+N (total)" at end
- Blue circled scores = Aces (hole-in-one)
- Orange/dark highlighted scores = bogeys/doubles
- Footer: Date, time, location, temperature, wind

## Google Sheet Structure
### Tab: "Rounds"
| Date | Course | Tees | Player | H1 | H2 | ... | H18 | Total | +/- Par | Has_Ace |
|------|--------|------|--------|----|----|-----|-----|-------|---------|---------|

### Tab: "Players" (future)
| Player | Rounds_Played | Avg_Score | Best_Round | Season_Points | Handicap |

## Key Business Rules (Phase 2)
- Season points awarded per round finish position
- Handicap system TBD (get rules from Derek)
- Tiebreaker rules TBD (get rules from Derek)
- Ace = special recognition/tracking

## Known Players (FUFA League 2026)
Toby, Eric, Derek, Sean, Jon, Mike, Mark, Charlie, Phil
(not all play every round)

## File Map
- `backend/main.py` — FastAPI routes
- `backend/scorecard_parser.py` — Claude Vision parsing logic
- `backend/sheets_client.py` — Google Sheets read/write
- `backend/scoring_rules.py` — Phase 2: points, handicaps, winners
- `frontend/src/App.jsx` — Root component
- `frontend/src/components/ImageUploader.jsx` — drag/drop upload
- `frontend/src/components/ScorecardTable.jsx` — editable parsed data
- `frontend/src/components/SubmitPanel.jsx` — confirm & write to sheet
