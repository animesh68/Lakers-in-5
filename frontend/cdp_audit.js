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
  console.log('--- Connecting to Edge DevTools Protocol ---');
  const version = await fetch('http://127.0.0.1:9222/json/version').then(r => r.json());
  console.log('Browser:', version.Browser);

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

  console.log('\n[1/4] Auditing Desktop View (1440x900) - Forecast Tab...');
  await cdpSend(ws, 'Emulation.setDeviceMetricsOverride', {
    width: 1440,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false
  });

  await delay(3000); // Allow data fetching & rendering

  // Evaluate DOM for player cards and circular avatars
  const desktopEval = await cdpSend(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const section = document.querySelector('section[aria-label="Player Performance Projections"]');
      const cards = Array.from(document.querySelectorAll('.player-card'));
      const avatars = Array.from(document.querySelectorAll('.player-avatar-circle'));
      const teamHeaders = Array.from(document.querySelectorAll('.player-grid-columns h4')).map(h => h.textContent.trim());
      const scrollOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth;

      return {
        sectionFound: !!section,
        cardCount: cards.length,
        avatarCount: avatars.length,
        teamHeaders: teamHeaders,
        scrollOverflow: scrollOverflow,
        firstAvatarStyles: avatars[0] ? {
          width: window.getComputedStyle(avatars[0]).width,
          height: window.getComputedStyle(avatars[0]).height,
          borderRadius: window.getComputedStyle(avatars[0]).borderRadius,
          objectFit: avatars[0].querySelector('img') ? window.getComputedStyle(avatars[0].querySelector('img')).objectFit : 'none',
          hasImage: !!avatars[0].querySelector('img'),
          hasInitials: !!avatars[0].querySelector('span')
        } : null
      };
    })()`,
    returnByValue: true
  });

  console.log('Desktop Forecast Audit Results:\n', JSON.stringify(desktopEval.result.value, null, 2));

  // Capture Desktop Screenshot
  const desktopScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'desktop_forecast.png'), Buffer.from(desktopScreenshot.data, 'base64'));
  console.log('✓ Saved desktop_forecast.png');

  // Navigate to Matchup Predictor
  console.log('\n[2/4] Testing Matchup Predictor Tab...');
  await cdpSend(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('nav button, header button'));
      const matchupBtn = buttons.find(b => b.textContent.includes('Matchups'));
      if (matchupBtn) matchupBtn.click();
      return !!matchupBtn;
    })()`
  });

  await delay(1500);

  // Click Generate Prediction
  await cdpSend(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const generateBtn = document.querySelector('button[type="submit"]');
      if (generateBtn) generateBtn.click();
      return !!generateBtn;
    })()`
  });

  await delay(3000); // Wait for simulation + player projections

  const matchupEval = await cdpSend(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const section = document.querySelector('section[aria-label="Player Performance Projections"]');
      const cards = Array.from(document.querySelectorAll('.player-card'));
      const resultCard = document.querySelector('.panel.panel-gold-glow');
      return {
        resultCardFound: !!resultCard,
        sectionFound: !!section,
        cardCount: cards.length
      };
    })()`,
    returnByValue: true
  });

  console.log('Matchup Predictor Audit Results:\n', JSON.stringify(matchupEval.result.value, null, 2));

  const matchupScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'desktop_matchup.png'), Buffer.from(matchupScreenshot.data, 'base64'));
  console.log('✓ Saved desktop_matchup.png');

  // Test Tablet View (768x1024)
  console.log('\n[3/4] Testing Tablet View (768x1024)...');
  await cdpSend(ws, 'Emulation.setDeviceMetricsOverride', {
    width: 768,
    height: 1024,
    deviceScaleFactor: 1,
    mobile: false
  });

  await delay(1000);
  const tabletScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'tablet_matchup.png'), Buffer.from(tabletScreenshot.data, 'base64'));
  console.log('✓ Saved tablet_matchup.png');

  // Test Mobile View (390x844)
  console.log('\n[4/4] Testing Mobile View (390x844)...');
  await cdpSend(ws, 'Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 2,
    mobile: true
  });

  await delay(1000);

  const mobileEval = await cdpSend(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const avatars = Array.from(document.querySelectorAll('.player-avatar-circle'));
      const scrollOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth;
      return {
        scrollOverflow: scrollOverflow,
        firstAvatarStyles: avatars[0] ? {
          width: window.getComputedStyle(avatars[0]).width,
          height: window.getComputedStyle(avatars[0]).height,
          borderRadius: window.getComputedStyle(avatars[0]).borderRadius
        } : null
      };
    })()`,
    returnByValue: true
  });

  console.log('Mobile Audit Results:\n', JSON.stringify(mobileEval.result.value, null, 2));

  const mobileScreenshot = await cdpSend(ws, 'Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(artifactDir, 'mobile_matchup.png'), Buffer.from(mobileScreenshot.data, 'base64'));
  console.log('✓ Saved mobile_matchup.png');

  // Close target
  ws.close();
  await fetch(`http://127.0.0.1:9222/json/close/${newTarget.id}`);
  console.log('\n✓ Browser Visual & Interaction Audit Completed Successfully.');
}

runAudit().catch(err => {
  console.error('Audit failed:', err);
  process.exit(1);
});
