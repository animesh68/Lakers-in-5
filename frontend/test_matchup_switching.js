import assert from 'node:assert/strict';

async function testMatchupSwitching() {
  const newTarget = await fetch('http://127.0.0.1:9222/json/new?http://localhost:5173', { method: 'PUT' }).then(r => r.json());
  const ws = new WebSocket(newTarget.webSocketDebuggerUrl);

  const cdpSend = (method, params = {}) => {
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
  };

  const delay = ms => new Promise(res => setTimeout(res, ms));

  await new Promise(res => ws.addEventListener('open', res));
  await delay(2000);

  // Navigate to Matchup Predictor
  await cdpSend('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('nav button, header button'));
      const matchupBtn = buttons.find(b => b.textContent.includes('Matchups'));
      if (matchupBtn) matchupBtn.click();
    })()`
  });
  await delay(1000);

  // 1. Simulate GSW @ LAL
  await cdpSend('Runtime.evaluate', {
    expression: `document.querySelector('button[type="submit"]').click()`
  });
  await delay(3000);

  const gswLalHeaders = await cdpSend('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll('.player-grid-columns h4')).map(h => h.textContent.trim())`,
    returnByValue: true
  });
  console.log('Matchup 1 (GSW @ LAL) Headers:', gswLalHeaders.result.value);
  assert.ok(gswLalHeaders.result.value.includes('Los Angeles Lakers'), 'Matchup 1 has Lakers');
  assert.ok(gswLalHeaders.result.value.includes('Golden State Warriors'), 'Matchup 1 has Warriors');

  // 2. Change Away Team to Boston Celtics (BOS) using React native setter
  await cdpSend('Runtime.evaluate', {
    expression: `(() => {
      const selects = Array.from(document.querySelectorAll('select'));
      const awaySelect = selects[1];
      const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
      setter.call(awaySelect, 'BOS');
      awaySelect.dispatchEvent(new Event('change', { bubbles: true }));
    })()`
  });

  // Wait until matchupGames finishes loading and date is updated
  console.log('Waiting for date verification & enabled submit button...');
  for (let i = 0; i < 20; i++) {
    await delay(300);
    const isReady = await cdpSend('Runtime.evaluate', {
      expression: `(() => {
        const btn = document.querySelector('button[type="submit"]');
        const dateSelect = Array.from(document.querySelectorAll('select'))[2];
        return btn && !btn.disabled && dateSelect && dateSelect.value === '2027-01-07';
      })()`,
      returnByValue: true
    });
    if (isReady.result.value) {
      console.log(`Button and Date ready after ${(i + 1) * 300}ms.`);
      break;
    }
  }

  // 3. Click Generate Prediction for BOS @ LAL
  await cdpSend('Runtime.evaluate', {
    expression: `document.querySelector('button[type="submit"]').click()`
  });
  await delay(3500);

  const bosLalHeaders = await cdpSend('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll('.player-grid-columns h4')).map(h => h.textContent.trim())`,
    returnByValue: true
  });
  console.log('Matchup 2 (BOS @ LAL) Headers:', bosLalHeaders.result.value);
  assert.ok(bosLalHeaders.result.value.includes('Boston Celtics'), 'Matchup 2 correctly updated to Boston Celtics');
  assert.ok(bosLalHeaders.result.value.includes('Los Angeles Lakers'), 'Matchup 2 correctly has Los Angeles Lakers');
  assert.ok(!bosLalHeaders.result.value.includes('Golden State Warriors'), 'Stale Warriors roster is removed');

  ws.close();
  await fetch(`http://127.0.0.1:9222/json/close/${newTarget.id}`);
  console.log('✓ Matchup switching test PASSED: No stale projections persisted.');
}

testMatchupSwitching().catch(err => {
  console.error('Matchup switching test failed:', err);
  process.exit(1);
});
