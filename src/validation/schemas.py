"""
Pydantic schema definitions for validating NBA game records, team stats, and player stats.
Ensures domain constraints, statistical boundaries, and data integrity.
"""

from datetime import date, datetime
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

class GameValidationSchema(BaseModel):
    game_id: str = Field(..., min_length=1)
    game_date: Optional[Union[date, str]] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    home_score: Optional[int] = Field(None, ge=0)
    away_score: Optional[int] = Field(None, ge=0)
    winner: Optional[str] = None

    @model_validator(mode="after")
    def validate_teams_and_winner(self):
        if self.home_team_id and self.away_team_id:
            if self.home_team_id == self.away_team_id:
                raise ValueError(f"Home team and away team cannot be identical: {self.home_team_id}")
        return self

class TeamStatValidationSchema(BaseModel):
    game_id: str
    team_id: int
    opponent_team_id: Optional[int] = None
    home: int = Field(..., ge=0, le=1)
    win: int = Field(..., ge=0, le=1)
    team_score: Optional[int] = Field(None, ge=0)
    opponent_score: Optional[int] = Field(None, ge=0)
    assists: Optional[int] = Field(None, ge=0)
    steals: Optional[int] = Field(None, ge=0)
    blocks: Optional[int] = Field(None, ge=0)
    turnovers: Optional[int] = Field(None, ge=0)
    rebounds_total: Optional[int] = Field(None, ge=0)
    field_goals_made: Optional[int] = Field(None, ge=0)
    field_goals_attempted: Optional[int] = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_shooting_and_teams(self):
        if self.team_id and self.opponent_team_id and self.team_id == self.opponent_team_id:
            raise ValueError(f"Team ID and Opponent Team ID cannot be identical: {self.team_id}")
        if self.field_goals_made is not None and self.field_goals_attempted is not None:
            if self.field_goals_made > self.field_goals_attempted:
                raise ValueError(f"Made FGs ({self.field_goals_made}) cannot exceed attempted FGs ({self.field_goals_attempted})")
        return self

class PlayerStatValidationSchema(BaseModel):
    game_id: str
    person_id: int
    player_team_id: Optional[int] = None
    opponent_team_id: Optional[int] = None
    points: Optional[int] = Field(None, ge=0)
    assists: Optional[int] = Field(None, ge=0)
    blocks: Optional[int] = Field(None, ge=0)
    steals: Optional[int] = Field(None, ge=0)
    turnovers: Optional[int] = Field(None, ge=0)
    rebounds_total: Optional[int] = Field(None, ge=0)
    field_goals_made: Optional[int] = Field(None, ge=0)
    field_goals_attempted: Optional[int] = Field(None, ge=0)
    three_pointers_made: Optional[int] = Field(None, ge=0)
    three_pointers_attempted: Optional[int] = Field(None, ge=0)
    free_throws_made: Optional[int] = Field(None, ge=0)
    free_throws_attempted: Optional[int] = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_player_shooting(self):
        if self.player_team_id and self.opponent_team_id and self.player_team_id == self.opponent_team_id:
            raise ValueError(f"Player team and opponent team cannot be identical: {self.player_team_id}")
        if self.field_goals_made is not None and self.field_goals_attempted is not None:
            if self.field_goals_made > self.field_goals_attempted:
                raise ValueError(f"Player made FGs ({self.field_goals_made}) > attempted ({self.field_goals_attempted})")
        if self.three_pointers_made is not None and self.three_pointers_attempted is not None:
            if self.three_pointers_made > self.three_pointers_attempted:
                raise ValueError(f"Player made 3Ps ({self.three_pointers_made}) > attempted ({self.three_pointers_attempted})")
        if self.free_throws_made is not None and self.free_throws_attempted is not None:
            if self.free_throws_made > self.free_throws_attempted:
                raise ValueError(f"Player made FTs ({self.free_throws_made}) > attempted ({self.free_throws_attempted})")
        return self
