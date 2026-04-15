"""
scoring_rules.py
FUFA Disc Golf League — Phase 2 scoring engine.

Rules implemented:
- Handicap: avg of last 5 played game differentials x 0.85, standard rounding
- Adjusted score: raw - running_handicap + strokes_of_honor + prev_placement_pts - new_player_bonus
- Tiebreakers: mulligan > metal hits > arrival order
- Championship points: 1st=9, 2nd=6, 3rd=4, 4th=3, 5th=2, 6th+=1 with multiplier
- Running championship points: best ceil(games_played/2)+1 results
- Season winner gets +1 stroke of honor for following year (stacks on consecutive wins)
"""

import math
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHAMPIONSHIP_POINTS = {
    1: 9,
    2: 6,
    3: 4,
    4: 3,
    5: 2,
}
CHAMPIONSHIP_POINTS_DEFAULT = 1  # 6th place and beyond

PLACEMENT_BONUS = {
    1: 3,
    2: 2,
    3: 1,
}  # Added to next game's adjusted score (hurts you — balancing mechanism)

HANDICAP_MULTIPLIER = 0.85
MIN_GAMES_FOR_HANDICAP = 3  # Handicap kicks in starting game 4


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PlayerGameInput:
    """Everything needed about a player going into a round."""
    name: str
    raw_score: int
    games_played: int                    # games played before this round
    last_5_handicaps: list[int]          # most recent last
    strokes_of_honor: int = 0           # positive = burden (adds to adjusted score)
    prev_placement: int = 0             # placement in last game played (0 = none)
    new_players_brought: int = 0        # new players brought to THIS game
    mulligan_used: bool = False
    metal_hits: int = 0
    arrival_order: int = 0              # 1 = first to arrive, higher = later


@dataclass
class PlayerGameResult:
    """Full result for a player after a round is processed."""
    name: str
    raw_score: int
    running_handicap: int
    strokes_of_honor: int
    prev_placement_pts: int
    new_player_bonus: int
    adjusted_score: int
    single_game_handicap: int           # raw_score - round_low
    placement: int
    championship_pts_raw: int
    championship_pts_earned: float
    tiebreaker_used: bool = False
    updated_last_5: list[int] = field(default_factory=list)


@dataclass
class RoundSummary:
    """Full round output."""
    date: str
    course: str
    tees: str
    location: str
    temperature_f: int
    wind_mph: int
    wind_direction: str
    skies: str
    multiplier: float
    round_low: int
    players: list[PlayerGameResult]
    tiebreaker_notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Handicap engine
# ---------------------------------------------------------------------------

def compute_running_handicap(last_5: list[int], games_played: int) -> int:
    """
    Compute running handicap from last 5 single-game differentials.

    Uses available history up to 5 games:
    - normally last 5
    - last 3 or 4 when fewer than 5 exist
    - falls back to any available history if fewer than 3 exist
    Then computes avg(history) * 0.85 with standard rounding.
    """
    values = [h for h in last_5 if h is not None]
    if not values:
        return 0

    history = values[-5:]
    avg = sum(history) / len(history)
    adjusted = avg * HANDICAP_MULTIPLIER
    return round(adjusted)


def compute_single_game_handicap(raw_score: int, round_low: int) -> int:
    """Single-game handicap = raw score minus round's lowest raw score."""
    return max(0, raw_score - round_low)


def update_last_5(last_5: list[int], new_value: int) -> list[int]:
    """Roll the last-5 history: drop oldest, append newest."""
    history = list(last_5) if last_5 else []
    history.append(new_value)
    return history[-5:]


# ---------------------------------------------------------------------------
# Adjusted score
# ---------------------------------------------------------------------------

def compute_adjusted_score(
    raw_score: int,
    running_handicap: int,
    strokes_of_honor: int,
    prev_placement: int,
    new_players_brought: int,
) -> tuple[int, int, int]:
    """
    Compute adjusted score used for placement.

    adjusted = raw - running_handicap + strokes_of_honor + placement_pts - new_player_bonus

    Returns:
        (adjusted_score, placement_pts_applied, new_player_bonus)
    """
    placement_pts = PLACEMENT_BONUS.get(prev_placement, 0)
    new_player_bonus = new_players_brought

    adjusted = (
        raw_score
        - running_handicap
        + strokes_of_honor
        + placement_pts
        - new_player_bonus
    )

    return adjusted, placement_pts, new_player_bonus


# ---------------------------------------------------------------------------
# Tiebreaker
# ---------------------------------------------------------------------------

def resolve_tiebreaker(
    tied_players: list[PlayerGameInput],
) -> tuple[list[str], list[str]]:
    """
    Resolve ties using FUFA rules in order:
    1. Did NOT use mulligan beats someone who DID
    2. More metal hits wins
    3. Earlier arrival (lower arrival_order) wins

    Returns:
        (ordered_names, tiebreaker_notes)
    """
    notes = []

    if len(tied_players) <= 1:
        return [p.name for p in tied_players], notes

    # Step 1: mulligan
    no_mulligan = [p for p in tied_players if not p.mulligan_used]
    used_mulligan = [p for p in tied_players if p.mulligan_used]
    if no_mulligan and used_mulligan:
        notes.append(
            f"Tiebreaker (mulligan): "
            f"{[p.name for p in no_mulligan]} beat "
            f"{[p.name for p in used_mulligan]}"
        )
        ordered_no_m, sub1 = resolve_tiebreaker(no_mulligan)
        ordered_m, sub2 = resolve_tiebreaker(used_mulligan)
        return ordered_no_m + ordered_m, notes + sub1 + sub2

    # Step 2: metal hits (more = better)
    max_hits = max(p.metal_hits for p in tied_players)
    most_hits = [p for p in tied_players if p.metal_hits == max_hits]
    fewer_hits = [p for p in tied_players if p.metal_hits < max_hits]
    if fewer_hits:
        notes.append(
            f"Tiebreaker (metal hits): "
            f"{[p.name for p in most_hits]} ({max_hits}) beat "
            f"{[p.name for p in fewer_hits]}"
        )
        ordered_most, sub1 = resolve_tiebreaker(most_hits)
        ordered_fewer, sub2 = resolve_tiebreaker(fewer_hits)
        return ordered_most + ordered_fewer, notes + sub1 + sub2

    # Step 3: arrival order (lower number = earlier = better)
    sorted_by_arrival = sorted(tied_players, key=lambda p: p.arrival_order)
    if len(set(p.arrival_order for p in tied_players)) > 1:
        notes.append(
            f"Tiebreaker (arrival order): "
            f"{[p.name for p in sorted_by_arrival]}"
        )
    return [p.name for p in sorted_by_arrival], notes


# ---------------------------------------------------------------------------
# Championship points
# ---------------------------------------------------------------------------

def award_championship_points(
    placement: int, multiplier: float = 1.0
) -> tuple[int, float]:
    """Returns (raw_points, points_after_multiplier)."""
    raw = CHAMPIONSHIP_POINTS.get(placement, CHAMPIONSHIP_POINTS_DEFAULT)
    earned = raw * multiplier
    return raw, earned


def compute_best_half_plus_one(all_points: list[float]) -> float:
    """
    Running championship total = sum of best ceil(n/2)+1 results.

    5 games -> best 4; 6 games -> best 4; 10 games -> best 6
    """
    if not all_points:
        return 0.0

    n = len(all_points)
    count = math.ceil(n / 2) + 1
    return sum(sorted(all_points, reverse=True)[:count])


# ---------------------------------------------------------------------------
# Main round processor
# ---------------------------------------------------------------------------

def process_round(
    players: list[PlayerGameInput],
    date: str,
    course: str,
    tees: str = "",
    location: str = "",
    temperature_f: int = 0,
    wind_mph: int = 0,
    wind_direction: str = "",
    skies: str = "",
    multiplier: float = 1.0,
) -> RoundSummary:
    """
    Full FUFA round processing pipeline.

    1. Find round low (lowest raw score)
    2. Compute running handicap per player
    3. Compute adjusted score per player
    4. Rank by adjusted score, resolve ties
    5. Compute single-game handicap differentials
    6. Award championship points with multiplier
    7. Update rolling last-5 handicap history

    Returns RoundSummary with full results.
    """
    if not players:
        raise ValueError("No players provided")

    # Step 1: Round low
    round_low = min(p.raw_score for p in players)

    # Steps 2-3: Compute handicaps and adjusted scores
    player_inputs_by_name = {p.name: p for p in players}
    computed: dict[str, dict] = {}

    for p in players:
        running_hc = compute_running_handicap(p.last_5_handicaps, p.games_played)
        adj_score, placement_pts, new_player_bonus = compute_adjusted_score(
            raw_score=p.raw_score,
            running_handicap=running_hc,
            strokes_of_honor=p.strokes_of_honor,
            prev_placement=p.prev_placement,
            new_players_brought=p.new_players_brought,
        )
        computed[p.name] = {
            "running_hc": running_hc,
            "adj_score": adj_score,
            "placement_pts": placement_pts,
            "new_player_bonus": new_player_bonus,
        }

    # Step 4: Group by adjusted score, resolve ties within each group
    score_groups: dict[int, list[str]] = {}
    for name, data in computed.items():
        score_groups.setdefault(data["adj_score"], []).append(name)

    ranked_names: list[str] = []
    tiebreaker_notes: list[str] = []
    tiebreaker_used_names: set[str] = set()

    for score in sorted(score_groups.keys()):
        group_names = score_groups[score]
        if len(group_names) == 1:
            ranked_names.extend(group_names)
        else:
            tied_inputs = [player_inputs_by_name[n] for n in group_names]
            ordered, notes = resolve_tiebreaker(tied_inputs)
            ranked_names.extend(ordered)
            tiebreaker_notes.extend(notes)
            tiebreaker_used_names.update(group_names)

    placements: dict[str, int] = {name: i + 1 for i, name in enumerate(ranked_names)}

    # Steps 5-7: Build final results
    results: list[PlayerGameResult] = []
    for p in players:
        name = p.name
        placement = placements[name]
        single_game_hc = compute_single_game_handicap(p.raw_score, round_low)
        raw_pts, earned_pts = award_championship_points(placement, multiplier)
        updated_history = update_last_5(p.last_5_handicaps, single_game_hc)

        results.append(PlayerGameResult(
            name=name,
            raw_score=p.raw_score,
            running_handicap=computed[name]["running_hc"],
            strokes_of_honor=p.strokes_of_honor,
            prev_placement_pts=computed[name]["placement_pts"],
            new_player_bonus=computed[name]["new_player_bonus"],
            adjusted_score=computed[name]["adj_score"],
            single_game_handicap=single_game_hc,
            placement=placement,
            championship_pts_raw=raw_pts,
            championship_pts_earned=earned_pts,
            tiebreaker_used=name in tiebreaker_used_names,
            updated_last_5=updated_history,
        ))

    results.sort(key=lambda r: r.placement)

    return RoundSummary(
        date=date,
        course=course,
        tees=tees,
        location=location,
        temperature_f=temperature_f,
        wind_mph=wind_mph,
        wind_direction=wind_direction,
        skies=skies,
        multiplier=multiplier,
        round_low=round_low,
        players=results,
        tiebreaker_notes=tiebreaker_notes,
    )


# ---------------------------------------------------------------------------
# Season winner / stroke of honor
# ---------------------------------------------------------------------------

def determine_season_winner(
    player_totals: dict[str, list[float]]
) -> tuple[str, float]:
    """
    Determine season championship winner using best half+1 formula.

    Args:
        player_totals: {player_name: [all championship points earned this season]}

    Returns:
        (winner_name, winning_total)
    """
    best = {
        name: compute_best_half_plus_one(points)
        for name, points in player_totals.items()
    }
    winner = max(best, key=lambda n: best[n])
    return winner, best[winner]


def update_strokes_of_honor(
    current_honors: dict[str, int],
    prev_winner: str,
    new_winner: str,
) -> dict[str, int]:
    """
    Update strokes of honor after season ends.

    - New winner gets +1 (stacks if consecutive)
    - Previous winner who lost resets to 0
    """
    updated = dict(current_honors)

    if new_winner == prev_winner:
        updated[new_winner] = updated.get(new_winner, 0) + 1
    else:
        updated[new_winner] = updated.get(new_winner, 0) + 1
        if prev_winner and prev_winner in updated:
            updated[prev_winner] = 0

    return updated


# ---------------------------------------------------------------------------
# Dashboard preview helpers
# ---------------------------------------------------------------------------

def preview_next_handicap(
    last_5: list[int],
    games_played: int,
    prev_placement: int = 0,
    strokes_of_honor: int = 0,
    new_players_brought: int = 0,
) -> dict:
    """
    Preview a player's effective handicap adjustment for their next game.
    Used by the Dashboard tab display.
    """
    running_hc = compute_running_handicap(last_5, games_played)
    placement_pts = PLACEMENT_BONUS.get(prev_placement, 0)

    # Net strokes subtracted from raw score (positive = net benefit)
    net_benefit = running_hc - strokes_of_honor - placement_pts + new_players_brought

    return {
        "running_handicap": running_hc,
        "strokes_of_honor": strokes_of_honor,
        "placement_pts_burden": placement_pts,
        "new_player_bonus": new_players_brought,
        "net_stroke_benefit": net_benefit,
        "games_played": games_played,
        "has_handicap": games_played >= MIN_GAMES_FOR_HANDICAP,
        "last_5_handicaps": last_5,
    }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Reproduce the Jon vs Derek example from spec
    players = [
        PlayerGameInput(
            name="Jon",
            raw_score=50,
            games_played=10,
            last_5_handicaps=[0, 0, 0, 3, 2],
            strokes_of_honor=1,
            prev_placement=1,   # won last game -> +3 burden
            new_players_brought=0,
            mulligan_used=False,
            metal_hits=2,
            arrival_order=2,
        ),
        PlayerGameInput(
            name="Derek",
            raw_score=53,
            games_played=10,
            last_5_handicaps=[4, 4, 4, 4, 4],
            strokes_of_honor=0,
            prev_placement=6,   # no placement bonus
            new_players_brought=0,
            mulligan_used=False,
            metal_hits=1,
            arrival_order=1,
        ),
    ]

    summary = process_round(
        players=players,
        date="2026-01-01",
        course="Test Course",
        multiplier=1.0,
    )

    print(f"Round low: {summary.round_low}")
    print()
    for p in summary.players:
        print(f"{p.name}:")
        print(f"  Raw: {p.raw_score}")
        print(f"  Running handicap: {p.running_handicap}")
        print(f"  Strokes of honor: +{p.strokes_of_honor}")
        print(f"  Placement burden: +{p.prev_placement_pts}")
        print(f"  Adjusted score: {p.adjusted_score}")
        print(f"  Placement: {p.placement}")
        print(f"  Champ pts: {p.championship_pts_earned}")
        print(f"  Next game last-5: {p.updated_last_5}")
        print()

    if summary.tiebreaker_notes:
        print("Tiebreakers:", summary.tiebreaker_notes)
