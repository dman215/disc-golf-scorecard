"""
scoring_rules.py
Phase 2: Winner determination, handicap calculations, season points.

Rules to be defined by Derek — stubs are in place for all major features.
"""

from dataclasses import dataclass, field


@dataclass
class PlayerRound:
    name: str
    total: int
    plus_minus: int
    has_ace: bool = False
    dnp_holes: list[int] = field(default_factory=list)


@dataclass
class RoundResult:
    course: str
    date: str
    players: list[PlayerRound]
    winner: str = ""
    tiebreaker_used: bool = False
    tiebreaker_description: str = ""
    points_awarded: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# STUB: Points table — update with real FUFA rules
# ---------------------------------------------------------------------------
# Example: 1st place = 10 pts, 2nd = 8, 3rd = 6, etc.
# Adjust this dict to match your league's actual points system.
POINTS_TABLE = {
    1: 10,
    2: 8,
    3: 6,
    4: 4,
    5: 3,
    6: 2,
    7: 1,
    8: 1,
    9: 1,
}

ACE_BONUS_POINTS = 2  # Bonus points for hitting an ace — adjust as needed


def determine_winner(players: list[PlayerRound]) -> tuple[str, bool, str]:
    """
    Determine the round winner.

    Returns:
        (winner_name, tiebreaker_used, tiebreaker_description)

    TODO: Implement actual FUFA tiebreaker rules.
    Current stub: lowest total score wins, ties broken alphabetically (placeholder).
    """
    if not players:
        return ("", False, "")

    sorted_players = sorted(players, key=lambda p: p.total)
    lowest_score = sorted_players[0].total
    tied = [p for p in sorted_players if p.total == lowest_score]

    if len(tied) == 1:
        return (tied[0].name, False, "")

    # --- TIEBREAKER PLACEHOLDER ---
    # Replace this logic with the real FUFA tiebreaker rules.
    # Options to implement:
    #   - Back 9 score comparison
    #   - Hole-by-hole sudden death from hole 18 backwards
    #   - Most holes under par
    #   - Sudden death playoff hole
    tiebreaker_desc = f"TIE between {', '.join(p.name for p in tied)} — tiebreaker rules TBD"
    return (tied[0].name, True, tiebreaker_desc)


def calculate_handicap(player_rounds: list[dict]) -> float:
    """
    Calculate a player's handicap based on their round history.

    TODO: Implement FUFA handicap formula.
    Stub returns 0.0 — replace with real calculation.

    Common disc golf handicap approaches:
    - Average of best N rounds vs course par
    - PDGA-style differential system
    - Fixed percentage of average score above par
    """
    if not player_rounds:
        return 0.0

    # Placeholder: average +/- over all rounds
    scores = [r.get("+/- Par", 0) for r in player_rounds if r.get("+/- Par") != ""]
    if not scores:
        return 0.0

    return round(sum(scores) / len(scores), 1)


def award_points(round_result: RoundResult) -> dict[str, int]:
    """
    Award season points based on finish position.

    Returns dict of {player_name: points_earned}
    """
    players_sorted = sorted(round_result.players, key=lambda p: p.total)
    points = {}

    position = 1
    i = 0
    while i < len(players_sorted):
        # Find all players tied at this position
        current_score = players_sorted[i].total
        tied_group = [p for p in players_sorted if p.total == current_score]

        # Award averaged points for tied positions
        positions_in_group = list(range(position, position + len(tied_group)))
        avg_points = sum(POINTS_TABLE.get(p, 0) for p in positions_in_group) / len(tied_group)

        for player in tied_group:
            earned = round(avg_points)
            if player.has_ace:
                earned += ACE_BONUS_POINTS
            points[player.name] = earned

        position += len(tied_group)
        i += len(tied_group)

    return points


def process_round(round_data: dict) -> RoundResult:
    """
    Full round processing pipeline: parse players, determine winner, award points.

    Args:
        round_data: Output from scorecard_parser.parse_scorecard()

    Returns:
        RoundResult with winner, tiebreaker info, and points
    """
    player_rounds = [
        PlayerRound(
            name=p["name"],
            total=p.get("total", 0),
            plus_minus=p.get("plus_minus", 0),
            has_ace=bool(p.get("aces")),
            dnp_holes=p.get("dnp_holes", []),
        )
        for p in round_data.get("players", [])
    ]

    winner, tiebreaker_used, tiebreaker_desc = determine_winner(player_rounds)

    result = RoundResult(
        course=round_data.get("course", ""),
        date=round_data.get("date", ""),
        players=player_rounds,
        winner=winner,
        tiebreaker_used=tiebreaker_used,
        tiebreaker_description=tiebreaker_desc,
    )

    result.points_awarded = award_points(result)
    return result
