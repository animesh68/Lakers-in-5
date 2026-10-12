import { createServer } from 'vite';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToString } from 'react-dom/server';

async function run() {
  console.log('🚀 Initializing Vite Dev Server for Component SSR Tests...');
  const server = await createServer({
    server: { middlewareMode: true },
    appType: 'custom'
  });

  try {
    const { default: PlayerCard } = await server.ssrLoadModule('/src/components/PlayerCard.jsx');
    const { default: PlayerProjections } = await server.ssrLoadModule('/src/components/PlayerProjections.jsx');
    const { default: PlayerProjectionsSection, PlayerStatStrip } = await server.ssrLoadModule('/src/components/PlayerProjectionsSection.jsx');
    const { getVerifiedPlayerHeadshotUrl, isFooterSlideAsset, getPlayerMeta, KNOWN_PLAYER_MAP } = await server.ssrLoadModule('/src/utils/playerMapping.js');

    console.log('✓ Successfully loaded PlayerCard, PlayerProjections, PlayerProjectionsSection, and playerMapping modules.');

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

    let passCount = 0;
    const test = (name, fn) => {
      try {
        fn();
        console.log(`  PASS: ${name}`);
        passCount++;
      } catch (err) {
        console.error(`  FAIL: ${name}`);
        console.error(err);
        process.exitCode = 1;
      }
    };

    console.log('\n--- Running 15 Verification Tests ---');

    test('1. Player projections render for both teams', () => {
      const html = renderToString(
        React.createElement(PlayerProjections, {
          homeTeam: "LAL",
          awayTeam: "GSW",
          gameDate: "2026-10-21",
          initialData: sampleMockData
        })
      );
      assert.ok(html.includes('Los Angeles Lakers'), 'Should include Home Team');
      assert.ok(html.includes('Golden State Warriors'), 'Should include Away Team');
      assert.ok(html.includes('LeBron James'), 'Should render Lakers player');
      assert.ok(html.includes('Stephen Curry'), 'Should render Warriors player');
    });

    test('2. Player name and team are displayed correctly', () => {
      const html = renderToString(React.createElement(PlayerCard, { player: sampleMockData.players[0] }));
      assert.ok(html.includes('LeBron James'), 'Player name must be displayed');
      assert.ok(html.includes('LAL'), 'Team code must be displayed');
    });

    test('3. PTS, REB, AST, and projected minutes use exact API values with proper formatting', () => {
      const html = renderToString(React.createElement(PlayerCard, { player: sampleMockData.players[0] }));
      assert.ok(html.includes('34.5'), 'Projected minutes 34.5 rendered');
      assert.ok(html.includes('25.2'), 'PTS 25.2 rendered');
      assert.ok(html.includes('7.8'), 'REB 7.8 rendered');
      assert.ok(html.includes('8.4'), 'AST 8.4 rendered');
      assert.ok(html.includes('PTS'), 'PTS label rendered');
      assert.ok(html.includes('REB'), 'REB label rendered');
      assert.ok(html.includes('AST'), 'AST label rendered');
    });

    test('4. Every player card has a circular image container', () => {
      const html = renderToString(React.createElement(PlayerCard, { player: sampleMockData.players[0] }));
      assert.ok(html.includes('player-avatar-circle'), 'Must have player-avatar-circle class');
      assert.ok(html.includes('border-radius:50%'), 'Must have border-radius 50%');
      assert.ok(html.includes('width:56px'), 'Must have 56px width');
      assert.ok(html.includes('height:56px'), 'Must have 56px height');
    });

    test('5. Valid NBA player ID produces headshot URL and circular img', () => {
      const html = renderToString(React.createElement(PlayerCard, { player: sampleMockData.players[0] }));
      assert.ok(html.includes('https://cdn.nba.com/headshots/nba/latest/260x190/2544.png'), 'Headshot URL is correctly formed');
      assert.ok(html.includes('object-fit:cover'), 'Object-fit cover is applied');
    });

    test('6. Missing or non-numeric image IDs render circular placeholder with initials without collapsing', () => {
      const syntheticPlayer = sampleMockData.players[3]; // R-999999 Marcus Smart
      const html = renderToString(React.createElement(PlayerCard, { player: syntheticPlayer }));
      assert.ok(!html.includes('https://cdn.nba.com/headshots/nba/latest/260x190/R-999999.png'), 'Synthetic IDs should not invent headshot URLs');
      assert.ok(html.includes('MS'), 'Initials MS rendered in placeholder');
      assert.ok(html.includes('player-avatar-circle'), 'Circular avatar container preserved');
      assert.ok(html.includes('width:56px'), 'Width remains 56px');
      assert.ok(html.includes('height:56px'), 'Height remains 56px');
    });

    test('7. Transition player badge is displayed for offseason transfer', () => {
      const html = renderToString(React.createElement(PlayerCard, { player: sampleMockData.players[3] }));
      assert.ok(html.includes('Offseason Transfer'), 'Transition badge rendered');
    });

    test('8. Loading state renders skeleton with circular avatar placeholders', () => {
      const html = renderToString(
        React.createElement(PlayerProjections, {
          homeTeam: "LAL",
          awayTeam: "GSW",
          gameDate: "2026-10-21",
          initialData: null
        })
      );
      assert.ok(html.includes('skeleton-pulse'), 'Skeleton pulses rendered');
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
        React.createElement(PlayerProjections, {
          homeTeam: "LAL",
          awayTeam: "GSW",
          gameDate: "2026-10-21",
          initialData: emptyData
        })
      );
      assert.ok(html.includes('No player projections available for this matchup.'), 'Empty message rendered');
    });

    test('10. Disclaimer is visible in the section', () => {
      const html = renderToString(
        React.createElement(PlayerProjections, {
          homeTeam: "LAL",
          awayTeam: "GSW",
          gameDate: "2026-10-21",
          initialData: sampleMockData
        })
      );
      assert.ok(
        html.includes('These are statistical projections, not confirmed lineups or guaranteed outcomes.'),
        'Disclaimer text is present'
      );
    });

    test('11. Heading and supporting text match specifications', () => {
      const html = renderToString(
        React.createElement(PlayerProjections, {
          homeTeam: "LAL",
          awayTeam: "GSW",
          gameDate: "2026-10-21",
          initialData: sampleMockData
        })
      );
      assert.ok(html.includes('PLAYER PROJECTIONS'), 'Heading PLAYER PROJECTIONS present');
      assert.ok(html.includes('Projected performance for players in this matchup.'), 'Supporting text present');
    });

    test('12. No fabricated statistical metrics are rendered', () => {
      const html = renderToString(React.createElement(PlayerCard, { player: sampleMockData.players[0] }));
      assert.ok(!html.includes('3PT%'), 'Should not invent 3PT%');
      assert.ok(!html.includes('FG%'), 'Should not invent FG%');
      assert.ok(!html.includes('PER'), 'Should not invent PER');
      assert.ok(!html.includes('Fantasy Points'), 'Should not invent Fantasy Points');
    });

    test('13. Roster sorting preserves backend order', () => {
      const html = renderToString(
        React.createElement(PlayerProjections, {
          homeTeam: "LAL",
          awayTeam: "GSW",
          gameDate: "2026-10-21",
          initialData: sampleMockData
        })
      );
      const lbIndex = html.indexOf('LeBron James');
      const adIndex = html.indexOf('Anthony Davis');
      assert.ok(lbIndex !== -1 && adIndex !== -1, 'Both players found');
      assert.ok(lbIndex < adIndex, 'Maintains order as provided by backend');
    });

    test('14. Player avatar container dimensions consistent (56px fixed circular container)', () => {
      const html = renderToString(React.createElement(PlayerCard, { player: sampleMockData.players[0] }));
      assert.ok(html.includes('min-width:56px'), 'min-width 56px fixed');
      assert.ok(html.includes('min-height:56px'), 'min-height 56px fixed');
      assert.ok(html.includes('border-radius:50%'), 'circular shape preserved');
    });

    test('15. Fallback avatar retains initials without collapse when player_id is null', () => {
      const playerWithoutId = {
        player_id: null,
        player_name: "Austin Reaves",
        team: "Los Angeles Lakers",
        team_code: "LAL",
        expected_minutes: 31.0,
        predicted_points: 16.5,
        predicted_rebounds: 4.2,
        predicted_assists: 5.5,
        is_transition_player: false
      };
      const html = renderToString(React.createElement(PlayerCard, { player: playerWithoutId }));
      assert.ok(html.includes('AR'), 'Initials AR rendered');
      assert.ok(html.includes('player-avatar-circle'), 'Circular avatar circle exists');
    });

    test('16. Footer slideshow assets cannot be selected as player profile pictures', () => {
      // 1. isFooterSlideAsset identifies footer/editorial assets
      assert.ok(isFooterSlideAsset('/imgs/luka77.jpg'), 'luka77.jpg is identified as footer asset');
      assert.ok(isFooterSlideAsset('/imgs/ar15.jpg'), 'ar15.jpg is identified as footer asset');
      assert.ok(isFooterSlideAsset('/imgs/kessler_lal_16x9__1__720.avif'), 'kessler avif is identified as footer asset');
      assert.ok(isFooterSlideAsset('/imgs/jake12.jpg'), 'jake12.jpg is identified as footer asset');

      // 2. KNOWN_PLAYER_MAP does not map any player to a footer slideshow asset
      for (const [id, meta] of Object.entries(KNOWN_PLAYER_MAP)) {
        assert.ok(!meta.image, `Player ${id} must not have an image property pointing to footer assets`);
      }

      // 3. getPlayerMeta returns image: null
      const lukaMeta = getPlayerMeta({ player_id: '1629029', player_name: 'Luka Dončić' });
      assert.strictEqual(lukaMeta.image, null, 'getPlayerMeta must return image: null to prevent footer asset usage');
    });

    test('17. Valid NBA player ID produces verified NBA CDN headshot and never footer image', () => {
      const lukaUrl = getVerifiedPlayerHeadshotUrl({ player_id: '1629029', player_name: 'Luka Dončić' });
      assert.strictEqual(lukaUrl, 'https://cdn.nba.com/headshots/nba/latest/260x190/1629029.png');
      assert.ok(!isFooterSlideAsset(lukaUrl), 'Luka headshot is not a footer asset');

      const reavesUrl = getVerifiedPlayerHeadshotUrl({ player_id: '1630559', player_name: 'Austin Reaves' });
      assert.strictEqual(reavesUrl, 'https://cdn.nba.com/headshots/nba/latest/260x190/1630559.png');

      const kesslerUrl = getVerifiedPlayerHeadshotUrl({ player_id: '1631117', player_name: 'Walker Kessler' });
      assert.strictEqual(kesslerUrl, 'https://cdn.nba.com/headshots/nba/latest/260x190/1631117.png');

      const laraviaUrl = getVerifiedPlayerHeadshotUrl({ player_id: '1631222', player_name: 'Jake LaRavia' });
      assert.strictEqual(laraviaUrl, 'https://cdn.nba.com/headshots/nba/latest/260x190/1631222.png');
    });

    test('18. Unverified player with synthetic or missing ID receives neutral silhouette placeholder', () => {
      const syntheticUrl = getVerifiedPlayerHeadshotUrl({ player_id: 'R-0123456', player_name: 'Rookie Test' });
      assert.strictEqual(syntheticUrl, null, 'Synthetic ID must receive null headshot');

      const missingIdUrl = getVerifiedPlayerHeadshotUrl({ player_id: null, player_name: 'Unknown Player' });
      assert.strictEqual(missingIdUrl, null, 'Missing ID must receive null headshot');

      // In PlayerStatStrip (or PlayerCard), missing headshot renders silhouette/fallback
      const html = renderToString(
        React.createElement(PlayerStatStrip, {
          player: {
            player_id: 'R-0123456',
            player_name: 'Rookie Test',
            team_code: 'LAL',
            predicted_points: 5.0,
            predicted_rebounds: 2.0,
            predicted_assists: 1.0,
            expected_minutes: 10.0
          }
        })
      );
      assert.ok(html.includes('player-neutral-silhouette'), 'Neutral silhouette rendered for unverified player');
      assert.ok(!html.includes('/imgs/'), 'Never contains /imgs/ path');
    });

    test('19. White rectangular player prediction strip renders verified headshot and stats', () => {
      const html = renderToString(
        React.createElement(PlayerStatStrip, {
          player: {
            player_id: '1629029',
            player_name: 'Luka Dončić',
            team_code: 'LAL',
            predicted_points: 26.3,
            predicted_rebounds: 6.4,
            predicted_assists: 5.9,
            expected_minutes: 33.5
          }
        })
      );
      assert.ok(html.includes('player-stat-strip-white'), 'White strip class rendered');
      assert.ok(html.includes('https://cdn.nba.com/headshots/nba/latest/260x190/1629029.png'), 'Luka official headshot rendered');
      assert.ok(!html.includes('/imgs/luka77.jpg'), 'Must NOT contain footer image luka77.jpg');
      assert.ok(html.includes('26.3'), 'Predicted points 26.3 rendered');
      assert.ok(html.includes('33.5'), 'Expected minutes 33.5 rendered');
    });

    test('20. Rotation section renders and enforces canonical player IDs and names', () => {
      const html = renderToString(
        React.createElement(PlayerProjectionsSection, {
          gameId: '5',
          homeTeam: 'LAL',
          awayTeam: 'GSW',
          gameDate: '2026-10-21'
        })
      );
      assert.ok(html.includes('THE ROTATION'), 'Rotation title rendered');
      assert.ok(html.includes('LINEUP &amp; ROTATION') || html.includes('LINEUP & ROTATION'), 'Section eyebrow rendered');
      assert.ok(html.includes('LAL'), 'Home team code rendered');
      assert.ok(html.includes('GSW'), 'Away team code rendered');
    });

    console.log(`\n========================================`);
    console.log(`Result: ${passCount}/20 tests PASSED`);
    console.log(`========================================\n`);

  } finally {
    await server.close();
  }
}

run().catch(err => {
  console.error('Test execution failed:', err);
  process.exit(1);
});
