"""
main.py
FastAPI backend for the FUFA Disc Golf Scorecard App.
Phase 2: Full scoring engine, handicaps, championship points, dashboard.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scorecard_parser import parse_scorecard, validate_round
from sheets_client import (
    get_all_rounds,
    get_reference_data,
    get_player_reference,
    get_season_stats,
    update_reference_after_round,
    write_dashboard,
    write_game_results,
    write_round,
)
from scoring_rules import (
    PlayerGameInput,
    process_round,
    compute_best_half_plus_one,
    determine_season_winner,
    update_strokes_of_honor,
    preview_next_handicap,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🥏  FUFA Scorecard API starting up")
    yield


app = FastAPI(
    title="FUFA Disc Golf League API",
    description="Scorecard parsing, handicaps, championship points",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class WriteRequest(BaseModel):
    parsed_data: dict
    overwrite: bool = False


class PlayerInput(BaseModel):
    name: str
    mulligan_used: bool = False
    metal_hits: int = 0
    arrival_order: int = 0
    new_players_brought: int = 0


class ProcessRoundRequest(BaseModel):
    parsed_data: dict           # from /parse-scorecard
    multiplier: float = 1.0    # championship point multiplier
    players: list[PlayerInput]  # tiebreaker + bonus inputs per player


# ---------------------------------------------------------------------------
# Phase 1 routes (scorecard upload + raw sheet write)
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"status": "ok", "message": "FUFA Scorecard API v2 🥏"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/parse-scorecard")
async def parse_scorecard_endpoint(file: UploadFile = File(...)):
    """Upload a UDisc scorecard image. Returns structured JSON."""
    content_type = file.content_type or ""
    if content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(400, f"Unsupported file type: {content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 20MB)")

    try:
        parsed = parse_scorecard(image_bytes, media_type=content_type)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Parsing failed: {e}")

    warnings = validate_round(parsed)
    return {"success": True, "data": parsed, "warnings": warnings}


@app.post("/write-to-sheet")
async def write_to_sheet_endpoint(request: WriteRequest):
    """Write parsed scorecard data to the Rounds tab (raw data only)."""
    try:
        result = write_round(request.parsed_data, overwrite=request.overwrite)
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Sheet write failed: {e}")

    return {"success": True, **result}


@app.get("/rounds")
async def get_rounds():
    """Fetch all raw rounds from Google Sheets."""
    try:
        rounds = get_all_rounds()
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"success": True, "rounds": rounds, "count": len(rounds)}


# ---------------------------------------------------------------------------
# Phase 2 routes (scoring engine)
# ---------------------------------------------------------------------------

@app.post("/process-round")
async def process_round_endpoint(request: ProcessRoundRequest):
    """
    Full FUFA scoring pipeline for a completed round.

    - Reads player reference data (handicap history, strokes of honor)
    - Computes adjusted scores and placements
    - Resolves tiebreakers
    - Awards championship points
    - Writes to GameResults tab
    - Updates Reference tab with new last-5 history
    - Rewrites Dashboard tab
    """
    parsed = request.parsed_data
    multiplier = request.multiplier

    # Build lookup of player inputs from request
    player_input_map = {p.name: p for p in request.players}

    # Build PlayerGameInput list for scoring engine
    game_inputs: list[PlayerGameInput] = []
    missing_refs = []

    # Get season stats for placement history
    season_stats = get_season_stats()

    for player_data in parsed.get("players", []):
        name = player_data.get("name", "")
        raw_score = player_data.get("total", 0)

        # Load from Reference tab
        ref = get_player_reference(name)
        if not ref:
            missing_refs.append(name)
            # Use defaults for new players
            ref = {
                "Strokes_of_Honor": 0,
                "H_5th_Last": 0, "H_4th_Last": 0,
                "H_3rd_Last": 0, "H_2nd_Last": 0, "H_Last": 0,
            }

        last_5 = [
            int(ref.get("H_5th_Last") or 0),
            int(ref.get("H_4th_Last") or 0),
            int(ref.get("H_3rd_Last") or 0),
            int(ref.get("H_2nd_Last") or 0),
            int(ref.get("H_Last") or 0),
        ]

        player_stats = season_stats.get(name, {})
        games_played = player_stats.get("games_played", 0)
        last_placement = player_stats.get("last_placement", 0)

        inp = player_input_map.get(name, PlayerInput(name=name))

        game_inputs.append(PlayerGameInput(
            name=name,
            raw_score=raw_score,
            games_played=games_played,
            last_5_handicaps=last_5,
            strokes_of_honor=int(ref.get("Strokes_of_Honor") or 0),
            prev_placement=last_placement,
            new_players_brought=inp.new_players_brought,
            mulligan_used=inp.mulligan_used,
            metal_hits=inp.metal_hits,
            arrival_order=inp.arrival_order,
        ))

    # Run scoring engine
    try:
        summary = process_round(
            players=game_inputs,
            date=parsed.get("date", ""),
            course=parsed.get("course", ""),
            tees=parsed.get("tees", ""),
            location=parsed.get("location", ""),
            temperature_f=parsed.get("temperature_f", 0),
            wind_mph=parsed.get("wind_mph", 0),
            wind_direction=parsed.get("wind_direction", ""),
            skies=parsed.get("skies", ""),
            multiplier=multiplier,
        )
    except Exception as e:
        raise HTTPException(500, f"Scoring engine error: {e}")

    # Write to GameResults tab
    try:
        game_input_map = {gi.name: gi for gi in game_inputs}
        write_game_results(summary, game_input_map)
    except Exception as e:
        raise HTTPException(500, f"Failed writing game results: {e}")

    # Update Reference tab with new last-5 for each player
    ref_errors = []
    for result in summary.players:
        try:
            update_reference_after_round(result.name, result.updated_last_5)
        except Exception as e:
            ref_errors.append(f"{result.name}: {e}")

    # Refresh season stats and write Dashboard
    try:
        updated_stats = get_season_stats()
        write_dashboard(summary, updated_stats)
    except Exception as e:
        ref_errors.append(f"Dashboard update failed: {e}")

    return {
        "success": True,
        "date": summary.date,
        "course": summary.course,
        "multiplier": summary.multiplier,
        "round_low": summary.round_low,
        "tiebreaker_notes": summary.tiebreaker_notes,
        "missing_refs": missing_refs,
        "ref_errors": ref_errors,
        "results": [
            {
                "name": p.name,
                "raw_score": p.raw_score,
                "running_handicap": p.running_handicap,
                "strokes_of_honor": p.strokes_of_honor,
                "prev_placement_pts": p.prev_placement_pts,
                "new_player_bonus": p.new_player_bonus,
                "adjusted_score": p.adjusted_score,
                "single_game_handicap": p.single_game_handicap,
                "placement": p.placement,
                "championship_pts_raw": p.championship_pts_raw,
                "championship_pts_earned": p.championship_pts_earned,
                "tiebreaker_used": p.tiebreaker_used,
                "updated_last_5": p.updated_last_5,
            }
            for p in summary.players
        ],
    }


@app.get("/reference")
async def get_reference():
    """Get all player reference data (handicap history, strokes of honor)."""
    try:
        data = get_reference_data()
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"success": True, "players": data}


@app.get("/standings")
async def get_standings():
    """
    Compute current season standings using best half+1 championship points formula.
    """
    try:
        stats = get_season_stats()
    except Exception as e:
        raise HTTPException(500, str(e))

    standings = []
    for name, data in stats.items():
        all_pts = data.get("all_champ_pts", [])
        best = compute_best_half_plus_one(all_pts)
        standings.append({
            "player": name,
            "games_played": data["games_played"],
            "champ_pts_ytd": sum(all_pts),
            "best_half_plus_one": best,
            "all_results": sorted(all_pts, reverse=True),
        })

    standings.sort(key=lambda x: x["best_half_plus_one"], reverse=True)
    for i, s in enumerate(standings):
        s["position"] = i + 1

    return {"success": True, "standings": standings}


@app.get("/handicap-preview/{player_name}")
async def handicap_preview(player_name: str):
    """Preview a player's handicap situation going into their next game."""
    ref = get_player_reference(player_name)
    if not ref:
        raise HTTPException(404, f"Player '{player_name}' not found in Reference tab")

    stats = get_season_stats()
    player_stats = stats.get(player_name, {})

    last_5 = [
        int(ref.get("H_5th_Last") or 0),
        int(ref.get("H_4th_Last") or 0),
        int(ref.get("H_3rd_Last") or 0),
        int(ref.get("H_2nd_Last") or 0),
        int(ref.get("H_Last") or 0),
    ]

    preview = preview_next_handicap(
        last_5=last_5,
        games_played=player_stats.get("games_played", 0),
        prev_placement=player_stats.get("last_placement", 0),
        strokes_of_honor=int(ref.get("Strokes_of_Honor") or 0),
    )

    return {"success": True, "player": player_name, **preview}
