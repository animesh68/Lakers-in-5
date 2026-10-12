import fs from 'node:fs';
import path from 'node:path';

async function cdpSend(ws, method, params = {}) {
  const id = Math.floor(Math.random() * 1000000);
  return new Promise((resolve, reject) => {
    const handler = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id === id) {
        ws.removeEventListener('message', handler);
        if (msg.error) reject(new Error(`${method} failed: ${JSON.stringify(msg.error)}`));
        else resolve(msg.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

async function runAudit() {
  console.log('--- Connecting to Edge DevTools Protocol (CDP) ---');
  let version;
  try {
    version = await fetch('http://127.0.0.1:9222/json/version').then(r => r.json());
    console.log('Browser connected:', version.Browser);
  } catch (err) {
    console.log('CDP endpoint not active at 9222:', err.message);
    return;
  }

  const newTarget = await fetch('http://127.0.0.1:9222/json/new?http://localhost:5173', { method: 'PUT' }).then(r => r.json());
  console.log('Opened target page:', newTarget.id);

  const ws = new WebSocket(newTarget.webSocketDebuggerUrl);

  await new Promise((res, rej) => {
    ws.addEventListener('open', res);
    ws.addEventListener('error', rej);
  });

  await cdpSend(ws, 'Page.enable');
  await cdpSend(ws, 'DOM.enable');
  await cdpSend(ws, 'Runtime.enable');

  const artifactDir = 'C:\\Users\\anime\\.gemini\\antigravity-ide\\brain\\ebd15286-ef45-4872-ae9c-d368b06e3be5';
  const delay = ms => new Promise(res => setTimeout(res, ms));

  console.log('\n[1/5] Setting Viewport to Desktop (1440x900)...');
  await cdpSend(ws, 'Emulation.setDeviceMetricsOverride', {
    width: 1440,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false
  });

  await delay(2500); // Allow data fetching & rendering

  // 1. Hero
  const heroScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'streamlined_01_hero.png'), Buffer.from(heroScreenshot.data, 'base64'));
  console.log('✓ Captured streamlined_01_hero.png');

  // 2. Next Game
  await cdpSend(ws, 'Runtime.evaluate', {
    expression: `document.getElementById('next-game').scrollIntoView({ behavior: 'instant' });`
  });
  await delay(800);
  const nextGameScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'streamlined_02_next_game.png'), Buffer.from(nextGameScreenshot.data, 'base64'));
  console.log('✓ Captured streamlined_02_next_game.png');

  // 3. Player Projections (Wait for rendered data)
  await cdpSend(ws, 'Runtime.evaluate', {
    expression: `document.getElementById('player-projections').scrollIntoView({ behavior: 'instant' });`
  });
  for (let i = 0; i < 20; i++) {
    const hasPlayer = await cdpSend(ws, 'Runtime.evaluate', {
      expression: `!!document.querySelector('#player-projections h3')`
    });
    if (hasPlayer.result.value) break;
    await delay(400);
  }
  await delay(500);
  const playerScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'streamlined_03_players.png'), Buffer.from(playerScreenshot.data, 'base64'));
  console.log('✓ Captured streamlined_03_players.png');

  // 4. Schedule Section (Wait for rendered games list)
  await cdpSend(ws, 'Runtime.evaluate', {
    expression: `document.getElementById('schedule').scrollIntoView({ behavior: 'instant' });`
  });
  for (let i = 0; i < 20; i++) {
    const hasGames = await cdpSend(ws, 'Runtime.evaluate', {
      expression: `document.querySelectorAll('#schedule .badge-gold').length > 0 || document.querySelectorAll('#schedule button').length > 0`
    });
    if (hasGames.result.value) break;
    await delay(400);
  }
  await delay(500);
  const scheduleScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'streamlined_04_schedule.png'), Buffer.from(scheduleScreenshot.data, 'base64'));
  console.log('✓ Captured streamlined_04_schedule.png');

  // 5. Tall Cinematic Footer Slideshow Scene & Meme
  await cdpSend(ws, 'Runtime.evaluate', {
    expression: `window.scrollTo(0, document.body.scrollHeight);`
  });
  await delay(1200);
  const footerScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'streamlined_05_footer.png'), Buffer.from(footerScreenshot.data, 'base64'));
  console.log('✓ Captured streamlined_05_footer.png');

  // 6. Mobile Viewport (390x844)
  console.log('\n[2/5] Auditing Mobile Viewport (390x844)...');
  await cdpSend(ws, 'Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 2,
    mobile: true
  });
  await delay(1000);
  const mobileScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'streamlined_06_mobile.png'), Buffer.from(mobileScreenshot.data, 'base64'));
  console.log('✓ Captured streamlined_06_mobile.png');

  // Evaluate DOM metrics
  const domAudit = await cdpSend(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const scheduleItems = document.querySelectorAll('#schedule [style*="border-radius"]').length;
      return {
        title: document.title,
        hasHeroVideo: !!document.querySelector('video[src="/hero-luka.mp4"]'),
        nextGameTitle: document.querySelector('#next-game .section-title')?.textContent,
        primaryPlayerName: document.querySelector('#player-projections h3')?.textContent,
        scheduleCount: scheduleItems,
        hasMemeImage: !!document.querySelector('img[src*="shannon-sharpe"]'),
        hasLakersLogo: !!document.querySelector('img[src*="Los_Angeles_Lakers_logo"]'),
        hasNbaLogo: !!document.querySelector('img[src*="nba-logo"]'),
        hasHowItWorks: !!document.querySelector('#how-it-works'),
        hasGameOutlook: !!document.querySelector('#game-outlook'),
        horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
      };
    })()`,
    returnByValue: true
  });

  console.log('\n--- DOM & Streamlined Audit Results ---');
  console.dir(domAudit.result.value, { depth: null });

  ws.close();
  await fetch(`http://127.0.0.1:9222/json/close/${newTarget.id}`);
  console.log('\n🎉 Streamlined Audit completed successfully!');
}

runAudit().catch(err => {
  console.error('Audit failed:', err);
  process.exit(1);
});
