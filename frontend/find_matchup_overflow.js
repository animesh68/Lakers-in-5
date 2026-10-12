async function findMatchupOverflow() {
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

  await new Promise(res => ws.addEventListener('open', res));
  await cdpSend('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await new Promise(res => setTimeout(res, 1500));

  // Navigate to Matchup Predictor
  await cdpSend('Runtime.evaluate', {
    expression: `(() => {
      const buttons = Array.from(document.querySelectorAll('nav button, header button'));
      const matchupBtn = buttons.find(b => b.textContent.includes('Matchups'));
      if (matchupBtn) matchupBtn.click();
    })()`
  });
  await new Promise(res => setTimeout(res, 1000));

  // Click generate prediction
  await cdpSend('Runtime.evaluate', {
    expression: `(() => {
      const generateBtn = document.querySelector('button[type="submit"]');
      if (generateBtn) generateBtn.click();
    })()`
  });
  await new Promise(res => setTimeout(res, 2500));

  const overflowReport = await cdpSend('Runtime.evaluate', {
    expression: `(() => {
      const docWidth = document.documentElement.clientWidth;
      const elements = Array.from(document.querySelectorAll('*'));
      const overflowing = elements.filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.right > docWidth + 1 || el.scrollWidth > docWidth + 1;
      }).map(el => ({
        tag: el.tagName,
        className: el.className,
        id: el.id,
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        rect: { left: el.getBoundingClientRect().left, right: el.getBoundingClientRect().right, width: el.getBoundingClientRect().width }
      }));
      return { docWidth, overflowingCount: overflowing.length, overflowing: overflowing.slice(0, 10) };
    })()`,
    returnByValue: true
  });

  console.log('Matchup Page Mobile Overflow Elements:', JSON.stringify(overflowReport.result.value, null, 2));

  ws.close();
  await fetch(`http://127.0.0.1:9222/json/close/${newTarget.id}`);
}

findMatchupOverflow().catch(console.error);
