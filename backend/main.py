"""
main.py
FastAPI backend for the FUFA Disc Golf Scorecard App.
"""

from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scorecard_parser import parse_scorecard, validate_round
from sheets_client import get_all_rounds, write_round
from scoring_rules import process_round


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🥏  FUFA Scorecard API starting up")
    yield
    print("🥏  FUFA Scorecard API shutting down")


app = FastAPI(
    title="FUFA Disc Golf Scorecard API",
    description="Parses UDisc scorecard images and writes data to Google Sheets",
    version="1.0.0",
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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"status": "ok", "message": "FUFA Scorecard API is running 🥏"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/parse-scorecard")
async def parse_scorecard_endpoint(
    file: UploadFile = File(...),
):
    """
    Upload a UDisc scorecard image (JPEG or PNG).
    Returns structured JSON with all round data extracted by Claude Vision.
    """
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Use JPEG, PNG, or WebP.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 20MB)")

    try:
        parsed = parse_scorecard(image_bytes, media_type=content_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

    warnings = validate_round(parsed)

    return {
        "success": True,
        "data": parsed,
        "warnings": warnings,
    }


@app.post("/write-to-sheet")
async def write_to_sheet_endpoint(request: WriteRequest):
    """
    Write previously parsed scorecard data to Google Sheets.
    Set overwrite=true to replace existing rows for same date/course/player.
    """
    try:
        result = write_round(request.parsed_data, overwrite=request.overwrite)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sheet write failed: {str(e)}")

    return {
        "success": True,
        **result,
    }


@app.post("/process-round")
async def process_round_endpoint(request: WriteRequest):
    """
    Phase 2: Process round data to determine winner, points, tiebreakers.
    Accepts the same parsed_data format as /write-to-sheet.
    """
    try:
        result = process_round(request.parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return {
        "success": True,
        "winner": result.winner,
        "tiebreaker_used": result.tiebreaker_used,
        "tiebreaker_description": result.tiebreaker_description,
        "points_awarded": result.points_awarded,
        "players": [
            {
                "name": p.name,
                "total": p.total,
                "plus_minus": p.plus_minus,
                "has_ace": p.has_ace,
            }
            for p in result.players
        ],
    }


@app.get("/rounds")
async def get_rounds():
    """Fetch all rounds from Google Sheets."""
    try:
        rounds = get_all_rounds()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "rounds": rounds, "count": len(rounds)}
