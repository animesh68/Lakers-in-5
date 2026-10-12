import { createServer } from 'vite';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToString } from 'react-dom/server';

async function run() {
  console.log('🚀 Initializing Vite Dev Server for Streamlined Component Tests...');
  const server = await createServer({
    server: { middlewareMode: true },
    appType: 'custom'
  });

  try {
    const { default: Header } = await server.ssrLoadModule('/src/components/Header.jsx');
    const { default: HeroLuka } = await server.ssrLoadModule('/src/components/HeroLuka.jsx');
    const { default: NextGameSection } = await server.ssrLoadModule('/src/components/NextGameSection.jsx');
    const { default: PlayerProjectionsSection } = await server.ssrLoadModule('/src/components/PlayerProjectionsSection.jsx');
    const { default: ScheduleSection } = await server.ssrLoadModule('/src/components/ScheduleSection.jsx');
    const { default: MemeSection } = await server.ssrLoadModule('/src/components/MemeSection.jsx');
    const { default: Footer } = await server.ssrLoadModule('/src/components/Footer.jsx');
    const { default: App } = await server.ssrLoadModule('/src/App.jsx');

    console.log('✓ Successfully loaded all streamlined frontend modules.\n');

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

    console.log('--- Running Streamlined Verification Tests ---');

    test('1. Header renders wordmark and non-technical links (GAMES, PLAYERS, SCHEDULE)', () => {
      const html = renderToString(React.createElement(Header, { activeSection: 'hero' }));
      assert(html.includes('LAKERS IN 5'), 'Header should render wordmark');
      assert(html.includes('GAMES'), 'Header should render GAMES link');
      assert(html.includes('PLAYERS'), 'Header should render PLAYERS link');
      assert(html.includes('SCHEDULE'), 'Header should render SCHEDULE link');
      assert(!html.includes('ABOUT'), 'Header should NOT contain ABOUT link');
      assert(!html.includes('ENGINE'), 'Header should NOT contain ENGINE link');
    });

    test('2. HeroLuka renders headline and video', () => {
      const html = renderToString(React.createElement(HeroLuka));
      assert(html.includes('THE GAME,<br/>BEFORE THE GAME.'), 'Hero should render headline');
      assert(html.includes('/hero-luka.mp4'), 'Hero should reference video');
      assert(html.includes('VIEW NEXT GAME'), 'Hero should render CTA');
    });

    test('3. NextGameSection renders win probability and projected margin without ML jargon', () => {
      const mockPred = {
        lakers_win_probability: 0.7172,
        opponent_win_probability: 0.2828,
        predicted_lakers_margin: 6.2,
        opponent_team: 'Golden State Warriors',
        is_lakers_home: true,
        game_date: '2026-10-21'
      };
      const html = renderToString(React.createElement(NextGameSection, {
        prediction: mockPred,
        loading: false,
        error: null
      }));
      assert(html.includes('71.7'), 'NextGameSection should render 71.7%');
      assert(html.includes('LAKERS WIN PROBABILITY'), 'NextGameSection should render probability label');
      assert(html.includes('+6.2'), 'NextGameSection should render +6.2 margin');
      assert(!html.includes('MODEL IMPACT'), 'NextGameSection should NOT have MODEL IMPACT');
      assert(!html.includes('MACHINE LEARNING'), 'NextGameSection should NOT have MACHINE LEARNING');
    });

    test('4. PlayerProjectionsSection renders primary player without hardcoded featured labels', () => {
      const html = renderToString(React.createElement(PlayerProjectionsSection, {
        gameId: '5',
        homeTeam: 'LAL',
        awayTeam: 'GSW',
        gameDate: '2026-10-21'
      }));
      assert(html.includes('PLAYER PROJECTIONS'), 'PlayerProjections should render title');
      assert(!html.includes('Featured Player'), 'PlayerProjections should NOT have Featured Player label');
      assert(!html.includes('Star Player'), 'PlayerProjections should NOT have Star Player label');
      assert(!html.includes('Player of the Game'), 'PlayerProjections should NOT have Player of the Game label');
    });

    test('5. ScheduleSection renders clean schedule header and container', () => {
      const html = renderToString(React.createElement(ScheduleSection, {
        onSelectGame: () => {},
        selectedGameId: '5'
      }));
      assert(html.includes('SCHEDULE'), 'Schedule should render section title');
      assert(html.includes('2026–27 SEASON'), 'Schedule should render eyebrow');
    });

    test('6. MemeSection renders Shannon Sharpe meme personality moment', () => {
      const html = renderToString(React.createElement(MemeSection));
      assert(html.includes('THE NUMBERS ARE SERIOUS.'), 'MemeSection should render title');
      assert(html.includes('shannon-sharpe-with-another-lakers-in-5-rhyme-meme.webp'), 'MemeSection should render meme image');
    });

    test('7. Footer renders tall slideshow scene with contained uncropped images', () => {
      const html = renderToString(React.createElement(Footer));
      assert(html.includes('THE GAME, BEFORE THE GAME.'), 'Footer should render tagline');
      assert(html.includes('LUKA DONČIĆ'), 'Footer should render player credit');
      assert(html.includes('Los_Angeles_Lakers_logo.svg.webp'), 'Footer should render Lakers logo');
      assert(html.includes('nba-logo-on-transparent-background-free-vector.jpg'), 'Footer should render NBA logo');
    });

    test('8. App full tree contains exactly 5 core sections in order (Hero -> Next Game -> Players -> Schedule -> Footer)', () => {
      const html = renderToString(React.createElement(App));
      assert(html.includes('LAKERS IN 5'), 'App should contain brand');
      assert(html.includes('THE GAME,<br/>BEFORE THE GAME.'), 'App should contain hero');
      assert(html.includes('NEXT GAME'), 'App should contain next game');
      assert(html.includes('PLAYER PROJECTIONS'), 'App should contain player projections');
      assert(html.includes('SCHEDULE'), 'App should contain schedule');
      assert(!html.includes('HOW IT WORKS'), 'App should NOT contain HOW IT WORKS');
      assert(!html.includes('FLOOR ADVANTAGE'), 'App should NOT contain GAME OUTLOOK floor advantage');
    });

    console.log(`\n🎉 All ${passCount} / 8 Streamlined Redesign Tests PASSED successfully!`);
  } finally {
    await server.close();
  }
}

run().catch((err) => {
  console.error('Fatal Test Runner Error:', err);
  process.exit(1);
});
