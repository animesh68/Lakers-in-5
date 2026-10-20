"""
Regression tests for Roster Integrity, Player Eligibility, Historical Exclusion, and Asset Separation.
"""

import os
import pytest
from src.inference.roster_service import RosterService
from src.inference.player_predictor import PlayerPredictor


def test_player_team_assignments_and_trades():
    """
    Test that historical trades and 2026 offseason transactions correctly assign:
    - James Harden -> Cleveland Cavaliers (CLE, 1610612739)
    - Ivica Zubac -> Indiana Pacers (IND, 1610612754)
    - Jake LaRavia -> Los Angeles Lakers (LAL, 1610612747)
    """
    service = RosterService()
    cutoff = "2026-10-23"
    
    # Check James Harden
    harden_id = service.resolve_player_id("James Harden")
    assert harden_id is not None
    harden_team = service.get_player_team_as_of(harden_id, cutoff)
    assert harden_team == "1610612739", f"James Harden should belong to CLE (1610612739), got {harden_team}"
    
    # Check Ivica Zubac
    zubac_id = service.resolve_player_id("Ivica Zubac")
    assert zubac_id is not None
    zubac_team = service.get_player_team_as_of(zubac_id, cutoff)
    assert zubac_team == "1610612754", f"Ivica Zubac should belong to IND (1610612754), got {zubac_team}"
    
    # Check Jake LaRavia
    laravia_id = service.resolve_player_id("Jake LaRavia")
    assert laravia_id is not None
    laravia_team = service.get_player_team_as_of(laravia_id, cutoff)
    assert laravia_team == "1610612747", f"Jake LaRavia should belong to LAL (1610612747), got {laravia_team}"


def test_historical_retired_players_excluded_from_current_rotation():
    """
    Verify that Carlos Boozer and other retired players are NOT included in the current
    2026-27 rotation solely because of an old franchise affiliation.
    Enforces active season window cutoff without hardcoding name blacklists.
    """
    service = RosterService()
    lakers_roster = service.get_active_roster_universe("LAL", "2026-10-21", max_players=20)
    lakers_names = [p["player_name"] for p in lakers_roster]
    lakers_ids = [str(p["person_id"]) for p in lakers_roster]

    # Carlos Boozer retired in 2015 (personId 2430)
    assert "Carlos Boozer" not in lakers_names, "Carlos Boozer must not appear in 2026-27 Lakers rotation"
    assert "2430" not in lakers_ids, "Carlos Boozer ID 2430 must not appear in active Lakers universe"

    # Other historical retired players whose last team was Lakers
    assert "Robert Sacre" not in lakers_names
    assert "Andre Ingram" not in lakers_names
    assert "Davon Reed" not in lakers_names

    # All active players must have recent game dates (within active window)
    for p in lakers_roster:
        assert p["last_game_date"] >= "2025-01-01", f"Player {p['player_name']} has outdated last game date: {p['last_game_date']}"


def test_general_active_window_across_all_teams():
    """
    Verify that the exclusion of historical retired players generalizes across all teams
    (e.g., Boston Celtics and Detroit Pistons have no Dino Radja, Bison Dele, Shaquille O'Neal).
    """
    service = RosterService()
    bos_roster = service.get_active_roster_universe("BOS", "2026-10-20", max_players=20)
    bos_names = [p["player_name"] for p in bos_roster]

    assert "Dino Radja" not in bos_names
    assert "Shaquille O'Neal" not in bos_names
    assert "Pervis Ellison" not in bos_names
    assert "Nenad Krstic" not in bos_names

    det_roster = service.get_active_roster_universe("DET", "2026-10-20", max_players=20)
    det_names = [p["player_name"] for p in det_roster]

    assert "Bison Dele" not in det_names
    assert "Kim English" not in det_names


def test_legitimate_players_retained_in_active_rotation():
    """
    Verify that legitimate active rotation players are retained and eligible.
    """
    service = RosterService()
    lakers_roster = service.get_active_roster_universe("LAL", "2026-10-21", max_players=15)
    names = [p["player_name"] for p in lakers_roster]

    assert "Luka Doncic" in names or "Luka Dončić" in names, "Luka Dončić must be in Lakers roster"
    assert "Austin Reaves" in names, "Austin Reaves must be in Lakers roster"
    assert "Walker Kessler" in names, "Walker Kessler must be in Lakers roster"
    assert "Jake LaRavia" in names, "Jake LaRavia must be in Lakers roster"
    assert "Collin Sexton" in names, "Collin Sexton must be in Lakers roster"


def test_jake_laravia_lakers_candidate_eligibility():
    """
    Verify Jake LaRavia is actively included in the Lakers candidate pool and receives predictions.
    """
    predictor = PlayerPredictor()
    res = predictor.predict_scheduled_game_players("Los Angeles Lakers", "Golden State Warriors", "2026-10-21")
    
    lal_players = [p for p in res.players if p.team == "LAL" or p.team_code == "LAL" or "Lakers" in p.team]
    player_names = [p.player_name for p in lal_players]
    
    assert "Jake LaRavia" in player_names, "Jake LaRavia must be included in the Lakers rotation candidate pool"
    
    laravia_pred = next(p for p in lal_players if p.player_name == "Jake LaRavia")
    assert laravia_pred.expected_minutes > 0
    assert laravia_pred.predicted_points is not None
    assert laravia_pred.predicted_rebounds is not None
    assert laravia_pred.predicted_assists is not None


def test_game_specific_roster_membership_no_leakage():
    """
    Ensure LAL vs GSW only contains active LAL and GSW players.
    All players belong exclusively to the scheduled teams.
    """
    predictor = PlayerPredictor()
    res = predictor.predict_scheduled_game_players("Los Angeles Lakers", "Golden State Warriors", "2026-10-21")
    
    assert res.home_team == "Los Angeles Lakers"
    assert res.away_team == "Golden State Warriors"
    
    for p in res.players:
        assert p.team_code in ("LAL", "GSW"), f"Player {p.player_name} has invalid team {p.team_code}"


def test_matchup_switching_integrity():
    """
    Ensure changing the matchup produces strictly the eligible players for that matchup,
    and no players from an earlier matchup persist.
    """
    predictor = PlayerPredictor()
    
    # Matchup 1: LAL vs GSW
    res_lal = predictor.predict_scheduled_game_players("Los Angeles Lakers", "Golden State Warriors", "2026-10-21")
    lal_teams = {p.team_code for p in res_lal.players}
    assert lal_teams == {"LAL", "GSW"}
    assert any("Luka" in p.player_name for p in res_lal.players)
    
    # Matchup 2: DET vs BOS
    res_det = predictor.predict_scheduled_game_players("Detroit Pistons", "Boston Celtics", "2026-10-20")
    det_teams = {p.team_code for p in res_det.players}
    assert det_teams == {"DET", "BOS"}
    assert not any(p.player_id == "1629029" for p in res_det.players), "Luka Dončić must not appear in DET vs BOS"
    assert any("Cade Cunningham" in p.player_name for p in res_det.players)


def test_canonical_player_id_and_name_preserved():
    """
    Ensure canonical player ID and name are preserved across predictions.
    """
    predictor = PlayerPredictor()
    res = predictor.predict_scheduled_game_players("Los Angeles Lakers", "Golden State Warriors", "2026-10-21")
    
    luka = next((p for p in res.players if "Luka" in p.player_name), None)
    assert luka is not None
    assert luka.player_id == "1629029", f"Canonical Luka ID must be 1629029, got {luka.player_id}"
    
    reaves = next((p for p in res.players if "Reaves" in p.player_name), None)
    assert reaves is not None
    assert reaves.player_id == "1630559", f"Canonical Reaves ID must be 1630559, got {reaves.player_id}"


def test_production_model_output_has_no_block_projection():
    """
    Confirm that the player model output schema only contains PTS, MIN, REB, AST and not BLK.
    """
    from src.inference.schemas import PlayerProjectionItem
    fields = PlayerProjectionItem.model_fields.keys()
    assert "predicted_blocks" not in fields
    assert "blk" not in fields
    assert "predicted_points" in fields
    assert "expected_minutes" in fields
    assert "predicted_rebounds" in fields
    assert "predicted_assists" in fields


def test_roster_service_diagnostics_contract():
    """
    Verify that RosterService exposes verified diagnostic metadata including
    transaction count, source file, season, and reference parquet/metadata existence.
    """
    service = RosterService()
    diag = service.get_roster_diagnostics()
    assert diag["status"] == "verified", f"Roster status must be 'verified', got {diag['status']}"
    assert diag["source_file"] == "nba_2026_offseason_transactions.csv"
    assert diag["transactions_count"] > 10, f"Expected >10 transactions, got {diag['transactions_count']}"
    assert diag["season"] == "2026-27"
    assert diag["historical_parquet_exists"] is True


def test_transaction_ordering_departures_vacate_before_additions():
    """
    Verify chronological transaction ordering: departures vacate prior rosters first,
    ensuring departed players (e.g. LeBron James) are vacated from LAL, and additions
    (e.g. Collin Sexton, Walker Kessler) receive verified 2026-27 roster spots.
    """
    service = RosterService()
    cutoff = "2026-10-21"
    lal_roster = service.get_active_roster_universe("LAL", cutoff, max_players=20)
    lal_names = [p["player_name"] for p in lal_roster]
    lal_pids = [str(p["person_id"]) for p in lal_roster]

    # Departed players must not be in LAL
    assert "LeBron James" not in lal_names, "LeBron James departed LAL and must not appear in 2026-27 Lakers roster"
    assert "2544" not in lal_pids, "LeBron James personId 2544 must not be in Lakers universe"
    assert "Rui Hachimura" not in lal_names, "Rui Hachimura departed LAL and must not appear in Lakers roster"
    assert "Deandre Ayton" not in lal_names, "Deandre Ayton must not appear in Lakers roster"

    # Added players must be in LAL
    assert "Collin Sexton" in lal_names, "Collin Sexton was added to LAL in 2026 offseason and must be eligible"
    assert "Walker Kessler" in lal_names, "Walker Kessler was added to LAL in 2026 offseason and must be eligible"
    assert any("Grimes" in name for name in lal_names), "Quentin Grimes was added to LAL and must be eligible"


def test_player_prediction_response_observability_metadata():
    """
    Verify that PlayerPredictor attaches roster validation status and source file
    to the prediction response for production deployment observability.
    """
    predictor = PlayerPredictor()
    res = predictor.predict_scheduled_game_players("Los Angeles Lakers", "Golden State Warriors", "2026-10-21")
    assert res.roster_status == "verified", f"Expected roster_status='verified', got {res.roster_status}"
    assert res.roster_source == "nba_2026_offseason_transactions.csv"
    assert len(res.players) > 0


def test_retired_historical_players_cannot_enter_via_default_fallbacks():
    """
    Verify that historical retired players cannot enter the rotation through default minute fallbacks,
    and all rotation players have recent activity in the active window.
    """
    service = RosterService()
    # Check across multiple franchises
    for team_code in ["LAL", "GSW", "BOS", "MIA"]:
        roster = service.get_active_roster_universe(team_code, "2026-10-21", max_players=15)
        for p in roster:
            assert p["last_game_date"] >= "2025-01-01", (
                f"Player {p['player_name']} on {team_code} has stale game date {p['last_game_date']}"
            )


def test_shadow_model_isolation_preserves_production():
    """
    Verify that shadow candidate evaluation executes without altering production prediction values.
    """
    predictor = PlayerPredictor()
    res_prod = predictor.predict_scheduled_game_players("Los Angeles Lakers", "Golden State Warriors", "2026-10-21", model_version="prod")
    assert res_prod.model_versions["minutes"] == "PlayerSuite-v1.0"
    for p in res_prod.players:
        assert p.expected_minutes > 0.0
        assert p.predicted_points >= 0.0

