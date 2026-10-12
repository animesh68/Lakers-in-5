async function testApi() {
  const health = await fetch('http://127.0.0.1:8000/health').then(r => r.json());
  console.log('Health API:', health);

  const lakersNext = await fetch('http://127.0.0.1:8000/predict/lakers/next').then(r => r.json());
  console.log('\nLakers Next Game:', lakersNext.game_date, lakersNext.opponent_name, 'Home:', lakersNext.is_lakers_home);

  const playerProjections = await fetch('http://127.0.0.1:8000/predict/players', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      home_team: 'LAL',
      away_team: 'GSW',
      game_date: '2026-10-21'
    })
  }).then(r => r.json());

  console.log('\nPlayer Projections Count:', playerProjections.players?.length);
  console.log('Home Team:', playerProjections.home_team);
  console.log('Away Team:', playerProjections.away_team);
  console.log('Game Date:', playerProjections.game_date);
  console.log('\nSample Players:');
  playerProjections.players?.slice(0, 6).forEach(p => {
    console.log(`  - [${p.team_code}] ${p.player_name}: ${p.expected_minutes} min | ${p.predicted_points} PTS | ${p.predicted_rebounds} REB | ${p.predicted_assists} AST (id: ${p.player_id}, transfer: ${p.is_transition_player})`);
  });
}
testApi().catch(console.error);
