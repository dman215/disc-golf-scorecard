"""
scorecard_parser.py
Parses UDisc scorecard images using Claude Vision.
Returns structured round data ready for Google Sheets.
"""

import base64
import json
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

PARSE_PROMPT = """You are parsing a UDisc disc golf scorecard image for the FUFA league season tracker.

Extract ALL data from this scorecard image and return it as a single JSON object.

The scorecard format is:
- Top: Course name and tee configuration (e.g. "Red Tees", "Short to Short")
- Header rows: Hole numbers (1-18), distances (feet), par values per hole
- Player rows: Player name followed by their score on each hole, then a final score like "+5 (62)"
- Bottom footer: Date, time, location, temperature, wind speed/direction
- Blue circled numbers = Aces (hole-in-one) — these are very rare and important to flag
- Some players may be missing scores on early holes (DNP / did not play those holes)

Return ONLY valid JSON, no markdown, no explanation. Use this exact structure:

{
  "course": "Course Name",
  "tees": "Tee Configuration",
  "date": "YYYY-MM-DD",
  "time": "HH:MM AM/PM",
  "location": "City, State",
  "temperature_f": 47,
  "wind_mph": 14,
  "wind_direction": "SE",
  "total_holes": 18,
  "par_total": 57,
  "hole_pars": [3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 4, 3, 3, 3, 4],
  "hole_distances": [356, 234, 229, 231, 171, 185, 278, 214, 227, 361, 295, 263, 229, 336, 211, 327, 184, 369],
  "players": [
    {
      "name": "PlayerName",
      "scores": [3, 3, 5, 3, 3, 3, 4, 4, 3, 4, 3, 3, 4, 4, 3, 3, 2, 5],
      "total": 62,
      "plus_minus": 5,
      "aces": [17],
      "dnp_holes": []
    }
  ]
}

Notes:
- "scores" array must have exactly one entry per hole (1–18 in order)
- If a player did not play a hole, use null for that hole's score and add the hole number (1-indexed) to "dnp_holes"
- "aces" is a list of hole numbers (1-indexed) where the player got an ace (blue circle)
- "plus_minus" is the number shown before the parenthetical total — positive means over par
- "total" is the raw stroke count in parentheses
- Parse the date carefully from the footer (e.g. "Mar 15 at 10:23 AM" → use current year if year not shown)
- If year is not in the footer, assume 2026
"""


def encode_image(image_bytes: bytes) -> str:
    """Convert image bytes to base64 string."""
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def parse_scorecard(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """
    Send a scorecard image to Claude Vision and return structured round data.
    
    Args:
        image_bytes: Raw image file bytes
        media_type: MIME type of the image (image/jpeg, image/png, etc.)
    
    Returns:
        Parsed round data as a dictionary
    
    Raises:
        ValueError: If Claude returns unparseable JSON
        anthropic.APIError: On API failures
    """
    image_data = encode_image(image_bytes)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": PARSE_PROMPT,
                    },
                ],
            }
        ],
    )

    raw_text = message.content[0].text.strip()

    # Strip any accidental markdown fences
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude returned invalid JSON: {e}\n\nRaw response:\n{raw_text}"
        ) from e

    return parsed


def validate_round(data: dict) -> list[str]:
    """
    Validate parsed round data and return a list of warnings.
    Empty list = all good.
    """
    warnings = []

    if not data.get("course"):
        warnings.append("Missing course name")

    if not data.get("date"):
        warnings.append("Missing date")

    players = data.get("players", [])
    if not players:
        warnings.append("No players found")

    for player in players:
        name = player.get("name", "Unknown")
        scores = player.get("scores", [])
        dnp = player.get("dnp_holes", [])

        played_holes = [s for s in scores if s is not None]
        if not played_holes:
            warnings.append(f"{name}: no scores found")
            continue

        # Verify total matches sum of scores
        claimed_total = player.get("total")
        computed_total = sum(s for s in scores if s is not None)
        if claimed_total and abs(claimed_total - computed_total) > 1:
            warnings.append(
                f"{name}: claimed total {claimed_total} doesn't match computed {computed_total}"
            )

        # Verify +/- matches
        par_total = data.get("par_total", 0)
        hole_pars = data.get("hole_pars", [])
        if hole_pars and dnp:
            # For DNP holes, don't count those pars
            played_par = sum(
                p for i, p in enumerate(hole_pars) if (i + 1) not in dnp
            )
        else:
            played_par = par_total

        claimed_pm = player.get("plus_minus")
        computed_pm = computed_total - played_par
        if claimed_pm is not None and abs(claimed_pm - computed_pm) > 1:
            warnings.append(
                f"{name}: claimed +/- {claimed_pm} doesn't match computed {computed_pm}"
            )

    return warnings


if __name__ == "__main__":
    # Quick test — pass an image path as argument
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scorecard_parser.py <image_path>")
        sys.exit(1)

    img_path = Path(sys.argv[1])
    img_bytes = img_path.read_bytes()
    suffix = img_path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"

    print(f"Parsing {img_path.name}...")
    result = parse_scorecard(img_bytes, mime)
    warnings = validate_round(result)

    print(json.dumps(result, indent=2))
    if warnings:
        print("\n⚠️  Warnings:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\n✅ Validation passed")
