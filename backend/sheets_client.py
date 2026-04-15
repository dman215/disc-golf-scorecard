"""
sheets_client.py
Google Sheets integration for FUFA disc golf league data.
Manages tabs: Rounds, Reference, Dashboard, GameResults
"""

import os
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TAB_ROUNDS = "Rounds"
TAB_REFERENCE = "Reference"
TAB_DASHBOARD = "Dashboard"
TAB_GAME_RESULTS = "GameResults"

ROUNDS_HEADERS = [
    "Date", "Course", "Tees", "Player",
    "H1","H2","H3","H4","H5","H6","H7","H8","H9",
    "H10","H11","H12","H13","H14","H15","H16","H17","H18",
    "Total", "+/- Par", "Par", "Has_Ace", "Ace_Holes", "DNP_Holes",
    "Temperature_F", "Wind_MPH", "Wind_Direction", "Skies", "Location", "Time",
]

REFERENCE_HEADERS = [
    "Player", "Strokes_of_Honor",
    "H_5th_Last", "H_4th_Last", "H_3rd_Last", "H_2nd_Last", "H_Last",
]

DASHBOARD_GAME_HEADERS = [
    "Last_Game_Date", "Course", "Temp_F",
    "Wind_MPH", "Wind_Direction", "Skies",
]

DASHBOARD_PLAYER_HEADERS = [
    "Player", "Last_Raw_Score", "Last_Adj_Score", "Last_Place", "Last_Champ_Pts",
    "H_5th_Last", "H_4th_Last", "H_3rd_Last", "H_2nd_Last", "H_Last",
    "Next_Game_Handicap", "Games_Played", "Mulligans_YTD", "Metal_Hits_YTD",
    "Champ_Pts_YTD", "Best_Half_Plus_One_Pts",
]

GAME_RESULTS_HEADERS = [
    "Date", "Course", "Multiplier", "Player",
    "Raw_Score", "Running_Handicap", "Strokes_of_Honor",
    "Prev_Placement_Pts", "New_Player_Bonus", "Adjusted_Score",
    "Single_Game_Handicap", "Placement", "Champ_Pts_Raw", "Champ_Pts_Earned",
    "Tiebreaker_Used", "Mulligan_Used", "Mulligan_Type", "Metal_Hits", "Arrival_Order",
    "Updated_H5", "Updated_H4", "Updated_H3", "Updated_H2", "Updated_H1",
]


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_sheet_client():
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "../credentials.json")
    creds_path = Path(creds_path).resolve()
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Google credentials not found at {creds_path}. See GOOGLE_SETUP.md."
        )
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return gspread.authorize(creds)


def get_spreadsheet():
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID not set in environment")
    gc = get_sheet_client()
    return gc.open_by_key(sheet_id)


def get_or_create_worksheet(spreadsheet, tab_name: str, headers: list[str]):
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=500, cols=len(headers) + 5)
        ws.append_row(headers, value_input_option="RAW")
        ws.format("1:1", {"textFormat": {"bold": True}})
    return ws


def _get_all_records_safe(ws) -> list[dict]:
    """
    Read worksheet rows as dicts even when the sheet has blank/duplicate header cells.
    """
    values = ws.get_all_values()
    if not values:
        return []

    raw_headers = values[0]
    seen: dict[str, int] = {}
    headers: list[str] = []
    for idx, header in enumerate(raw_headers):
        key = (header or "").strip() or f"__col_{idx + 1}"
        count = seen.get(key, 0) + 1
        seen[key] = count
        headers.append(key if count == 1 else f"{key}_{count}")

    records: list[dict] = []
    for row in values[1:]:
        if not any(cell.strip() for cell in row):
            continue
        padded = row + [""] * (len(headers) - len(row))
        records.append({headers[i]: padded[i] for i in range(len(headers))})

    return records


# ---------------------------------------------------------------------------
# Reference tab
# ---------------------------------------------------------------------------

def get_reference_data() -> list[dict]:
    """Read all player reference rows."""
    spreadsheet = get_spreadsheet()
    ws = get_or_create_worksheet(spreadsheet, TAB_REFERENCE, REFERENCE_HEADERS)
    return _get_all_records_safe(ws)


def get_player_reference(player_name: str) -> dict | None:
    """Get reference row for a single player (case-insensitive)."""
    for p in get_reference_data():
        if p.get("Player", "").strip().lower() == player_name.strip().lower():
            return p
    return None


def get_reference_handicap_history(player_name: str) -> list[int]:
    """
    Return handicap history from Reference tab for a player, oldest -> newest.
    Empty/missing cells are ignored.
    """
    ref = get_player_reference(player_name)
    if not ref:
        return []

    values: list[int] = []
    for key in ("H_5th_Last", "H_4th_Last", "H_3rd_Last", "H_2nd_Last", "H_Last"):
        raw = ref.get(key, "")
        if raw in ("", None):
            continue
        try:
            values.append(int(raw))
        except (TypeError, ValueError):
            continue
    return values


def get_player_game_handicaps_before(player_name: str, before_date: str) -> list[int]:
    """
    Return this player's Single_Game_Handicap values for rounds before before_date.
    Results are sorted chronologically; ties keep sheet order.
    """
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(TAB_GAME_RESULTS)
        _ensure_game_results_headers(ws)
        records = _get_all_records_safe(ws)
    except gspread.WorksheetNotFound:
        return []

    try:
        cutoff = datetime.strptime(before_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        cutoff = None

    dated: list[tuple[datetime.date, int, int]] = []
    for idx, row in enumerate(records):
        if row.get("Player", "").strip().lower() != player_name.strip().lower():
            continue

        date_raw = str(row.get("Date", "")).strip()
        try:
            row_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
        except ValueError:
            continue

        if cutoff and row_date >= cutoff:
            continue

        try:
            handicap = int(row.get("Single_Game_Handicap", 0) or 0)
        except (TypeError, ValueError):
            continue

        dated.append((row_date, idx, handicap))

    dated.sort(key=lambda x: (x[0], x[1]))
    return [h for _, _, h in dated]


def update_reference_after_round(player_name: str, updated_last_5: list[int]):
    """Roll player's last-5 handicap history forward in the Reference tab."""
    spreadsheet = get_spreadsheet()
    ws = get_or_create_worksheet(spreadsheet, TAB_REFERENCE, REFERENCE_HEADERS)
    all_values = ws.get_all_values()

    if not all_values:
        raise ValueError("Reference tab is empty")

    headers = all_values[0]
    try:
        player_col = headers.index("Player")
        h5_col = headers.index("H_5th_Last")
    except ValueError:
        raise ValueError("Reference tab missing expected headers")

    history = list(updated_last_5)
    while len(history) < 5:
        history.insert(0, 0)
    history = history[-5:]

    for i, row in enumerate(all_values[1:], start=2):
        if len(row) > player_col and row[player_col].strip().lower() == player_name.strip().lower():
            for j, val in enumerate(history):
                ws.update_cell(i, h5_col + 1 + j, val)
            return

    raise ValueError(f"Player '{player_name}' not found in Reference tab")


# ---------------------------------------------------------------------------
# Rounds tab (raw scorecard data)
# ---------------------------------------------------------------------------

def round_exists(ws, date: str, course: str, player: str) -> bool:
    for row in ws.get_all_values()[1:]:
        if len(row) >= 4 and row[0] == date and row[1] == course and row[3] == player:
            return True
    return False


def _ensure_rounds_headers(ws):
    """Ensure required Rounds headers exist (for older sheets)."""
    header_row = ws.row_values(1)
    if not header_row:
        required_cols = len(ROUNDS_HEADERS)
        if ws.col_count < required_cols:
            ws.add_cols(required_cols - ws.col_count)
        ws.append_row(ROUNDS_HEADERS, value_input_option="RAW")
        ws.format("1:1", {"textFormat": {"bold": True}})
        return

    missing = [h for h in ROUNDS_HEADERS if h not in header_row]
    if not missing:
        return

    next_col = len(header_row) + 1
    required_cols = next_col + len(missing) - 1
    if ws.col_count < required_cols:
        ws.add_cols(required_cols - ws.col_count)

    for header in missing:
        ws.update_cell(1, next_col, header)
        next_col += 1


def _ensure_game_results_headers(ws):
    """Ensure required GameResults headers exist (for older sheets)."""
    header_row = ws.row_values(1)
    if not header_row:
        required_cols = len(GAME_RESULTS_HEADERS)
        if ws.col_count < required_cols:
            ws.add_cols(required_cols - ws.col_count)
        ws.append_row(GAME_RESULTS_HEADERS, value_input_option="RAW")
        ws.format("1:1", {"textFormat": {"bold": True}})
        return

    missing = [h for h in GAME_RESULTS_HEADERS if h not in header_row]
    if not missing:
        return

    next_col = len(header_row) + 1
    required_cols = next_col + len(missing) - 1
    if ws.col_count < required_cols:
        ws.add_cols(required_cols - ws.col_count)
    for header in missing:
        ws.update_cell(1, next_col, header)
        next_col += 1


def _round_datetime_exists(ws, date: str, round_time: str) -> bool:
    def _norm(value: str) -> str:
        return " ".join((value or "").strip().lower().split())

    all_values = ws.get_all_values()
    if not all_values:
        return False

    headers = all_values[0]
    try:
        date_col = headers.index("Date")
        time_col = headers.index("Time")
    except ValueError:
        return False

    normalized_date = _norm(date)
    normalized_time = _norm(round_time)
    for row in all_values[1:]:
        row_date = _norm(row[date_col]) if len(row) > date_col else ""
        row_time = _norm(row[time_col]) if len(row) > time_col else ""
        if row_date == normalized_date and row_time == normalized_time:
            return True
    return False


def _delete_round_datetime_rows(ws, date: str, round_time: str):
    def _norm(value: str) -> str:
        return " ".join((value or "").strip().lower().split())

    all_values = ws.get_all_values()
    if not all_values:
        return

    headers = all_values[0]
    try:
        date_col = headers.index("Date")
        time_col = headers.index("Time")
    except ValueError:
        return

    normalized_date = _norm(date)
    normalized_time = _norm(round_time)
    to_delete = []
    for i, row in enumerate(all_values[1:], start=2):
        row_date = _norm(row[date_col]) if len(row) > date_col else ""
        row_time = _norm(row[time_col]) if len(row) > time_col else ""
        if row_date == normalized_date and row_time == normalized_time:
            to_delete.append(i)

    for row_idx in reversed(to_delete):
        ws.delete_rows(row_idx)


def write_round(parsed_data: dict, overwrite: bool = False) -> dict:
    """Write parsed scorecard to the Rounds tab."""
    spreadsheet = get_spreadsheet()
    ws = get_or_create_worksheet(spreadsheet, TAB_ROUNDS, ROUNDS_HEADERS)
    _ensure_rounds_headers(ws)

    date = parsed_data.get("date", "")
    round_time = parsed_data.get("time", "")
    course = parsed_data.get("course", "")
    tees = parsed_data.get("tees", "")
    par_total = parsed_data.get("par_total", "")
    temperature = parsed_data.get("temperature_f", "")
    wind_mph = parsed_data.get("wind_mph", "")
    wind_dir = parsed_data.get("wind_direction", "")
    skies = parsed_data.get("skies", "")
    location = parsed_data.get("location", "")

    rows_written = 0
    rows_skipped = 0
    warnings = []

    players = parsed_data.get("players", [])
    if date and round_time:
        if not overwrite and _round_datetime_exists(ws, date, round_time):
            return {
                "rows_written": 0,
                "rows_skipped": len(players),
                "warnings": [
                    f"Duplicate round detected for {date} at {round_time}. Enable overwrite to replace it."
                ],
                "duplicate_round": True,
                "sheet_url": f"https://docs.google.com/spreadsheets/d/{os.getenv('GOOGLE_SHEET_ID')}",
            }
        if overwrite:
            _delete_round_datetime_rows(ws, date, round_time)

    for player in players:
        name = player.get("name", "Unknown")
        scores = player.get("scores", [None] * 18)
        total = player.get("total", "")
        plus_minus = player.get("plus_minus", "")
        aces = player.get("aces", [])
        dnp_holes = player.get("dnp_holes", [])

        while len(scores) < 18:
            scores.append(None)
        scores = scores[:18]

        row = [
            date, course, tees, name,
            *[s if s is not None else "" for s in scores],
            total, plus_minus, par_total,
            1 if aces else 0,
            ",".join(str(a) for a in aces) if aces else "",
            ",".join(str(h) for h in dnp_holes) if dnp_holes else "",
            temperature, wind_mph, wind_dir, skies, location, round_time,
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        rows_written += 1

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return {
        "rows_written": rows_written,
        "rows_skipped": rows_skipped,
        "warnings": warnings,
        "duplicate_round": False,
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}",
    }


def _delete_matching_rows(ws, date: str, course: str, player: str):
    all_values = ws.get_all_values()
    to_delete = [
        i + 2 for i, row in enumerate(all_values[1:])
        if len(row) >= 4 and row[0] == date and row[1] == course and row[3] == player
    ]
    for row_idx in reversed(to_delete):
        ws.delete_rows(row_idx)


def get_all_rounds() -> list[dict]:
    spreadsheet = get_spreadsheet()
    ws = get_or_create_worksheet(spreadsheet, TAB_ROUNDS, ROUNDS_HEADERS)
    return _get_all_records_safe(ws)


# ---------------------------------------------------------------------------
# GameResults tab (processed scoring data — permanent record)
# ---------------------------------------------------------------------------

def write_game_results(round_summary, game_inputs: dict):
    """
    Append one row per player to GameResults tab.

    Args:
        round_summary: RoundSummary from scoring_rules.process_round()
        game_inputs: {player_name: PlayerGameInput}
    """
    spreadsheet = get_spreadsheet()
    ws = get_or_create_worksheet(spreadsheet, TAB_GAME_RESULTS, GAME_RESULTS_HEADERS)
    _ensure_game_results_headers(ws)

    for p in round_summary.players:
        inp = game_inputs.get(p.name)
        history = list(p.updated_last_5)
        while len(history) < 5:
            history.insert(0, "")

        row = [
            round_summary.date,
            round_summary.course,
            round_summary.multiplier,
            p.name,
            p.raw_score,
            p.running_handicap,
            p.strokes_of_honor,
            p.prev_placement_pts,
            p.new_player_bonus,
            p.adjusted_score,
            p.single_game_handicap,
            p.placement,
            p.championship_pts_raw,
            p.championship_pts_earned,
            1 if p.tiebreaker_used else 0,
            1 if (inp and inp.mulligan_used) else 0,
            getattr(inp, "mulligan_type", "no") if inp else "no",
            inp.metal_hits if inp else 0,
            inp.arrival_order if inp else 0,
            *history[-5:],
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")


def get_all_game_results() -> list[dict]:
    """Fetch all GameResults rows as records."""
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(TAB_GAME_RESULTS)
    except gspread.WorksheetNotFound:
        return []
    _ensure_game_results_headers(ws)
    return _get_all_records_safe(ws)


def replace_game_results(rows: list[list]):
    """
    Replace GameResults tab with header + provided rows.
    Each row must match GAME_RESULTS_HEADERS order.
    """
    spreadsheet = get_spreadsheet()
    ws = get_or_create_worksheet(spreadsheet, TAB_GAME_RESULTS, GAME_RESULTS_HEADERS)
    ws.clear()
    if ws.col_count < len(GAME_RESULTS_HEADERS):
        ws.add_cols(len(GAME_RESULTS_HEADERS) - ws.col_count)
    ws.append_row(GAME_RESULTS_HEADERS, value_input_option="RAW")
    ws.format("1:1", {"textFormat": {"bold": True}})
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")


def get_season_stats() -> dict:
    """
    Read GameResults to build YTD stats per player.
    Returns {player_name: {games_played, mulligans_ytd, va_mulligans_ytd, metal_hits_ytd, all_champ_pts, last_placement}}
    """
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(TAB_GAME_RESULTS)
        _ensure_game_results_headers(ws)
        records = _get_all_records_safe(ws)
    except gspread.WorksheetNotFound:
        return {}

    stats: dict[str, dict] = {}
    for row in records:
        name = row.get("Player", "")
        if not name:
            continue
        if name not in stats:
            stats[name] = {
                "games_played": 0,
                "mulligans_ytd": 0,
                "va_mulligans_ytd": 0,
                "metal_hits_ytd": 0,
                "all_champ_pts": [],
                "last_placement": 0,
            }
        stats[name]["games_played"] += 1
        stats[name]["mulligans_ytd"] += int(row.get("Mulligan_Used", 0) or 0)
        if str(row.get("Mulligan_Type", "")).strip().lower() == "va":
            stats[name]["va_mulligans_ytd"] += 1
        stats[name]["metal_hits_ytd"] += int(row.get("Metal_Hits", 0) or 0)
        pts = row.get("Champ_Pts_Earned", 0)
        if pts:
            stats[name]["all_champ_pts"].append(float(pts))
        stats[name]["last_placement"] = int(row.get("Placement", 0) or 0)

    return stats


# ---------------------------------------------------------------------------
# Dashboard tab
# ---------------------------------------------------------------------------

def write_dashboard(round_summary, player_season_stats: dict):
    """
    Rewrite the Dashboard tab with latest game info + YTD stats.

    Args:
        round_summary: RoundSummary from scoring_rules.process_round()
        player_season_stats: output from get_season_stats()
    """
    from scoring_rules import compute_best_half_plus_one, compute_running_handicap

    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(TAB_DASHBOARD)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=TAB_DASHBOARD, rows=200, cols=30)

    # Game header
    ws.append_row(DASHBOARD_GAME_HEADERS, value_input_option="RAW")
    ws.format("1:1", {"textFormat": {"bold": True}})
    ws.append_row([
        round_summary.date,
        round_summary.course,
        round_summary.temperature_f,
        round_summary.wind_mph,
        round_summary.wind_direction,
        round_summary.skies,
    ])

    ws.append_row([])  # spacer

    # Player detail headers
    ws.append_row(DASHBOARD_PLAYER_HEADERS, value_input_option="RAW")
    ws.format("4:4", {"textFormat": {"bold": True}})

    for p in sorted(round_summary.players, key=lambda x: x.placement):
        stats = player_season_stats.get(p.name, {})
        games_played = stats.get("games_played", 0)
        all_champ_pts = stats.get("all_champ_pts", [])

        history = list(p.updated_last_5)
        while len(history) < 5:
            history.insert(0, "")
        history = history[-5:]

        next_hc = compute_running_handicap(p.updated_last_5, games_played)
        best_half = compute_best_half_plus_one(all_champ_pts)

        row = [
            p.name,
            p.raw_score,
            p.adjusted_score,
            p.placement,
            p.championship_pts_earned,
            *history,
            next_hc,
            games_played,
            stats.get("mulligans_ytd", 0),
            stats.get("metal_hits_ytd", 0),
            sum(all_champ_pts),
            best_half,
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
