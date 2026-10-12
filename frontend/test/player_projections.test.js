import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToString } from 'react-dom/server';
import PlayerCard from '../src/components/PlayerCard.jsx';
import PlayerProjections from '../src/components/PlayerProjections.jsx';

const sampleMockData = {
  game_id: "1",
  game_date: "2026-10-21",
  home_team: "Los Angeles Lakers",
  away_team: "Golden State Warriors",
  players: [
    {
      player_id: "2544",
      player_name: "LeBron James",
      team: "Los Angeles Lakers",
      team_code: "LAL",
      expected_minutes: 34.5,
      predicted_points: 25.2,
      predicted_rebounds: 7.8,
      predicted_assists: 8.4,
      is_transition_player: false
    },
    {
      player_id: "203076",
      player_name: "Anthony Davis",
      team: "Los Angeles Lakers",
      team_code: "LAL",
      expected_minutes: 35.1,
      predicted_points: 26.4,
      predicted_rebounds: 12.1,
      predicted_assists: 3.5,
      is_transition_player: false
    },
    {
      player_id: "201939",
      player_name: "Stephen Curry",
      team: "Golden State Warriors",
      team_code: "GSW",
      expected_minutes: 33.8,
      predicted_points: 28.1,
      predicted_rebounds: 4.9,
      predicted_assists: 6.2,
      is_transition_player: false
    },
    {
      player_id: "R-999999",
      player_name: "Marcus Smart",
      team: "Golden State Warriors",
      team_code: "GSW",
      expected_minutes: 26.4,
      predicted_points: 11.2,
      predicted_rebounds: 3.8,
      predicted_assists: 5.1,
      is_transition_player: true
    }
  ],
  model_versions: {
    minutes: "ridge-v1",
    stats: "gb-multi-v1"
  },
  feature_schema_version: "v1.0-player",
  prediction_timestamp: "2026-09-30T10:00:00Z"
};

test('1. Player projections render for both teams', () => {
  const html = renderToString(
    <PlayerProjections
      homeTeam="LAL"
      awayTeam="GSW"
      gameDate="2026-10-21"
      initialData={sampleMockData}
    />
  );
  assert.ok(html.includes('Los Angeles Lakers'), 'Should include Home Team');
  assert.ok(html.includes('Golden State Warriors'), 'Should include Away Team');
  assert.ok(html.includes('LeBron James'), 'Should render Lakers player');
  assert.ok(html.includes('Stephen Curry'), 'Should render Warriors player');
});

test('2. Player name and team are displayed correctly', () => {
  const html = renderToString(<PlayerCard player={sampleMockData.players[0]} />);
  assert.ok(html.includes('LeBron James'), 'Player name must be displayed');
  assert.ok(html.includes('LAL'), 'Team code must be displayed');
});

test('3. PTS, REB, AST, and projected minutes use exact API values with proper formatting', () => {
  const html = renderToString(<PlayerCard player={sampleMockData.players[0]} />);
  assert.ok(html.includes('34.5'), 'Projected minutes 34.5 rendered');
  assert.ok(html.includes('25.2'), 'PTS 25.2 rendered');
  assert.ok(html.includes('7.8'), 'REB 7.8 rendered');
  assert.ok(html.includes('8.4'), 'AST 8.4 rendered');
  assert.ok(html.includes('PTS'), 'PTS label rendered');
  assert.ok(html.includes('REB'), 'REB label rendered');
  assert.ok(html.includes('AST'), 'AST label rendered');
});

test('4. Every player card has a circular image container', () => {
  const html = renderToString(<PlayerCard player={sampleMockData.players[0]} />);
  assert.ok(html.includes('player-avatar-circle'), 'Must have player-avatar-circle class');
  assert.ok(html.includes('border-radius:50%'), 'Must have border-radius 50%');
  assert.ok(html.includes('width:56px'), 'Must have 56px width');
  assert.ok(html.includes('height:56px'), 'Must have 56px height');
});

test('5. Valid NBA player ID produces headshot URL and circular img', () => {
  const html = renderToString(<PlayerCard player={sampleMockData.players[0]} />);
  assert.ok(html.includes('https://cdn.nba.com/headshots/nba/latest/260x190/2544.png'), 'Headshot URL is correctly formed');
  assert.ok(html.includes('object-fit:cover'), 'Object-fit cover is applied');
});

test('6. Missing or non-numeric image IDs render circular placeholder with initials without collapsing', () => {
  const syntheticPlayer = sampleMockData.players[3]; // R-999999 Marcus Smart
  const html = renderToString(<PlayerCard player={syntheticPlayer} />);
  assert.ok(!html.includes('https://cdn.nba.com/headshots/nba/latest/260x190/R-999999.png'), 'Synthetic IDs should not invent headshot URLs');
  assert.ok(html.includes('MS'), 'Initials MS rendered in placeholder');
  assert.ok(html.includes('player-avatar-circle'), 'Circular avatar container preserved');
  assert.ok(html.includes('width:56px'), 'Width remains 56px');
  assert.ok(html.includes('height:56px'), 'Height remains 56px');
});

test('7. Transition player badge is displayed for offseason transfer', () => {
  const html = renderToString(<PlayerCard player={sampleMockData.players[3]} />);
  assert.ok(html.includes('Offseason Transfer'), 'Transition badge rendered');
});

test('8. Loading state renders skeleton with circular avatar placeholders', () => {
  // Render component without initialData and let it show loading/skeleton
  const html = renderToString(
    <PlayerProjections
      homeTeam="LAL"
      awayTeam="GSW"
      gameDate="2026-10-21"
      initialData={null}
    />
  );
  // Initial SSR render without data triggers skeleton
  assert.ok(html.includes('player-avatar-circle') || html.includes('skeleton-pulse'), 'Skeleton pulses rendered');
  assert.ok(html.includes('border-radius:50%'), 'Circular avatar skeleton rendered');
});

test('9. Empty response displays clean empty state message', () => {
  const emptyData = {
    game_id: "1",
    game_date: "2026-10-21",
    home_team: "Los Angeles Lakers",
    away_team: "Golden State Warriors",
    players: []
  };
  const html = renderToString(
    <PlayerProjections
      homeTeam="LAL"
      awayTeam="GSW"
      gameDate="2026-10-21"
      initialData={emptyData}
    />
  );
  assert.ok(html.includes('No player projections available for this matchup.'), 'Empty message rendered');
});

test('10. Disclaimer is visible in the section', () => {
  const html = renderToString(
    <PlayerProjections
      homeTeam="LAL"
      awayTeam="GSW"
      gameDate="2026-10-21"
      initialData={sampleMockData}
    />
  );
  assert.ok(
    html.includes('These are statistical projections, not confirmed lineups or guaranteed outcomes.'),
    'Disclaimer text is present'
  );
});

test('11. Heading and supporting text match specifications', () => {
  const html = renderToString(
    <PlayerProjections
      homeTeam="LAL"
      awayTeam="GSW"
      gameDate="2026-10-21"
      initialData={sampleMockData}
    />
  );
  assert.ok(html.includes('PLAYER PROJECTIONS'), 'Heading PLAYER PROJECTIONS present');
  assert.ok(html.includes('Projected performance for players in this matchup.'), 'Supporting text present');
});

test('12. No fabricated statistical metrics are rendered (only PTS, REB, AST, Proj Min)', () => {
  const html = renderToString(<PlayerCard player={sampleMockData.players[0]} />);
  assert.ok(!html.includes('3PT%'), 'Should not invent 3PT%');
  assert.ok(!html.includes('FG%'), 'Should not invent FG%');
  assert.ok(!html.includes('PER'), 'Should not invent PER');
  assert.ok(!html.includes('Fantasy Points'), 'Should not invent Fantasy Points');
});
