"""
sheets_client.py
Google Sheets integration for FUFA disc golf league data.
Uses a service account (credentials.json) — no OAuth flow needed.
"""

import os
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Google Sheet tab names
TAB_ROUNDS = "Rounds"
TAB_PLAYERS = "Players"

# Column headers for the Rounds tab
ROUNDS_HEADERS = [
    "Date",
    "Course",
    "Tees",
    "Player",
    "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9",
    "H10", "H11", "H12", "H13", "H14", "H15", "H16", "H17", "H18",
    "Total",
    "+/- Par",
    "Par",
    "Has_Ace",
    "Ace_Holes",
    "DNP_Holes",
    "Temperature_F",
    "Wind_MPH",
    "Wind_Direction",
    "Location",
]


def get_sheet_client():
    """Build and return an authenticated gspread client."""
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "../credentials.json")
    creds_path = Path(creds_path).resolve()

    if not creds_path.exists():
        raise FileNotFoundError(
            f"Google credentials not found at {creds_path}. "
            "See GOOGLE_SETUP.md for instructions."
        )

    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return gspread.authorize(creds)


def get_or_create_worksheet(spreadsheet, tab_name: str, headers: list[str]):
    """Get a worksheet by name, creating it with headers if it doesn't exist."""
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
        ws.append_row(headers, value_input_option="RAW")
        # Bold the header row
        ws.format("1:1", {"textFormat": {"bold": True}})
    return ws


def round_exists(ws, date: str, course: str, player: str) -> bool:
    """Check if a row for this date/course/player already exists."""
    existing = ws.get_all_values()
    for row in existing[1:]:  # skip header
        if len(row) >= 4 and row[0] == date and row[1] == course and row[3] == player:
            return True
    return False


def write_round(parsed_data: dict, overwrite: bool = False) -> dict:
    """
    Write a parsed round to the Google Sheet.

    Args:
        parsed_data: Output from scorecard_parser.parse_scorecard()
        overwrite: If True, delete existing rows for same date/course/player before writing

    Returns:
        Summary dict with rows_written, skipped, warnings
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID not set in environment")

    gc = get_sheet_client()
    spreadsheet = gc.open_by_key(sheet_id)
    ws = get_or_create_worksheet(spreadsheet, TAB_ROUNDS, ROUNDS_HEADERS)

    date = parsed_data.get("date", "")
    course = parsed_data.get("course", "")
    tees = parsed_data.get("tees", "")
    par_total = parsed_data.get("par_total", "")
    temperature = parsed_data.get("temperature_f", "")
    wind_mph = parsed_data.get("wind_mph", "")
    wind_dir = parsed_data.get("wind_direction", "")
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

        # Check for duplicate
        if not overwrite and round_exists(ws, date, course, name):
            rows_skipped += 1
            warnings.append(f"Skipped {name} — row already exists for {date} / {course}")
            continue

        # If overwrite, delete matching rows first
        if overwrite:
            _delete_matching_rows(ws, date, course, name)

        # Pad or trim scores to 18 holes
        while len(scores) < 18:
            scores.append(None)
        scores = scores[:18]

        row = [
            date,
            course,
            tees,
            name,
            *[s if s is not None else "" for s in scores],
            total,
            plus_minus,
            par_total,
            1 if aces else 0,
            ",".join(str(a) for a in aces) if aces else "",
            ",".join(str(h) for h in dnp_holes) if dnp_holes else "",
            temperature,
            wind_mph,
            wind_dir,
            location,
        ]

        ws.append_row(row, value_input_option="USER_ENTERED")
        rows_written += 1

    return {
        "rows_written": rows_written,
        "rows_skipped": rows_skipped,
        "warnings": warnings,
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}",
    }


def _delete_matching_rows(ws, date: str, course: str, player: str):
    """Delete all rows matching date + course + player."""
    all_values = ws.get_all_values()
    rows_to_delete = []
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) >= 4 and row[0] == date and row[1] == course and row[3] == player:
            rows_to_delete.append(i)
    # Delete in reverse order to preserve row indices
    for row_idx in reversed(rows_to_delete):
        ws.delete_rows(row_idx)


def get_all_rounds() -> list[dict]:
    """Fetch all round rows from the sheet as a list of dicts."""
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    gc = get_sheet_client()
    spreadsheet = gc.open_by_key(sheet_id)
    ws = get_or_create_worksheet(spreadsheet, TAB_ROUNDS, ROUNDS_HEADERS)
    return ws.get_all_records()
