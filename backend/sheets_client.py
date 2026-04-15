"""
sheets_client.py
Google Sheets integration for FUFA disc golf league data.
Manages tabs: Rounds, Reference, Dashboard, GameResults
"""

import os
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
    "Temperature_F", "Wind_MPH", "Wind_Direction", "Skies", "Location",
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
    "Tiebreaker_Used", "Mulligan_Used", "Metal_Hits", "Arrival_Order",
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


# ---------------------------------------------------------------------------
# Reference tab
# ---------------------------------------------------------------------------

def get_reference_data() -> list[dict]:
    """Read all player reference rows."""
    spreadsheet = get_spreadsheet()
    ws = get_or_create_worksheet(spreadsheet, TAB_REFERENCE, REFERENCE_HEADERS)
    return ws.get_all_records()


def get_player_reference(player_name: str) -> dict | None:
    """Get reference row for a single player (case-insensitive)."""
    for p in get_reference_data():
        if p.get("Player", "").strip().lower() == player_name.strip().lower():
            return p
    return None


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


def write_round(parsed_data: dict, overwrite: bool = False) -> dict:
    """Write parsed scorecard to the Rounds tab."""
    spreadsheet = get_spreadsheet()
    ws = get_or_create_worksheet(spreadsheet, TAB_ROUNDS, ROUNDS_HEADERS)

    date = parsed_data.get("date", "")
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

    for player in parsed_data.get("players", []):
        name = player.get("name", "Unknown")
        scores = player.get("scores", [None] * 18)
        total = player.get("total", "")
        plus_minus = player.get("plus_minus", "")
        aces = player.get("aces", [])
        dnp_holes = player.get("dnp_holes", [])

        if not overwrite and round_exists(ws, date, course, name):
            rows_skipped += 1
            warnings.append(f"Skipped {name} — already exists for {date} / {course}")
            continue

        if overwrite:
            _delete_matching_rows(ws, date, course, name)

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
            temperature, wind_mph, wind_dir, skies, location,
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        rows_written += 1

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    return {
        "rows_written": rows_written,
        "rows_skipped": rows_skipped,
        "warnings": warnings,
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
    return ws.get_all_records()


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
            inp.metal_hits if inp else 0,
            inp.arrival_order if inp else 0,
            *history[-5:],
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")


def get_season_stats() -> dict:
    """
    Read GameResults to build YTD stats per player.
    Returns {player_name: {games_played, mulligans_ytd, metal_hits_ytd, all_champ_pts, last_placement}}
    """
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(TAB_GAME_RESULTS)
        records = ws.get_all_records()
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
                "metal_hits_ytd": 0,
                "all_champ_pts": [],
                "last_placement": 0,
            }
        stats[name]["games_played"] += 1
        stats[name]["mulligans_ytd"] += int(row.get("Mulligan_Used", 0) or 0)
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
