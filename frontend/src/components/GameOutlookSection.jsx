import React from 'react';

export default function GameOutlookSection({ prediction }) {
  const isLakersHome = prediction?.is_lakers_home ?? true;
  const opponentName = prediction?.opponent_team || 'Golden State Warriors';
  const margin = prediction?.predicted_lakers_margin ?? 6.2;
  const winProb = prediction ? prediction.lakers_win_probability * 100 : 71.7;

  return (
    <section
      id="game-outlook"
      style={{
        backgroundColor: 'var(--surface-warm)',
        padding: '20px 0 80px 0',
        borderBottom: '1px solid var(--surface-warm-border)',
      }}
    >
      <div className="container">
        <div style={{ marginBottom: '32px' }}>
          <div className="section-eyebrow">
            <span>●</span> ANALYSIS
          </div>
          <h2 className="section-title">GAME OUTLOOK</h2>
          <p className="section-desc">
            Key factors shaping the pre-game outlook for the Lakers against {opponentName}.
          </p>
        </div>

        {/* 3 Human-Readable Insight Cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px',
          }}
        >
          {/* 1. Home Court Factor */}
          <div className="card-warm">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span className="font-display" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-dark-primary)' }}>
                FLOOR ADVANTAGE
              </span>
              <span className="badge-purple">
                {isLakersHome ? 'CRYPTO.COM ARENA' : 'ON THE ROAD'}
              </span>
            </div>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-dark-secondary)', lineHeight: 1.6 }}>
              {isLakersHome
                ? 'Lakers hold home-floor advantage. Historical baseline models credit home teams with elevated perimeter scoring efficiency.'
                : `Lakers play on the road at ${opponentName}. Travel rest and road pacing factor into the projected baseline.`}
            </p>
          </div>

          {/* 2. Rating & Net Differential */}
          <div className="card-warm">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span className="font-display" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-dark-primary)' }}>
                NET FORM & RATING
              </span>
              <span className="badge-gold">
                {margin > 0 ? `+${margin.toFixed(1)} SPREAD` : `${margin.toFixed(1)} SPREAD`}
              </span>
            </div>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-dark-secondary)', lineHeight: 1.6 }}>
              {margin > 0
                ? `Rolling 10-game efficiency metrics favor the Lakers by an estimated +${margin.toFixed(1)} points in expected point differential.`
                : `Opponent enters with competitive rolling metrics, resulting in a tight estimated margin of ${margin.toFixed(1)} points.`}
            </p>
          </div>

          {/* 3. Matchup Dynamics */}
          <div className="card-warm">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span className="font-display" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-dark-primary)' }}>
                MATCHUP PROFILE
              </span>
              <span className="badge-purple">
                {winProb >= 50 ? `${winProb.toFixed(0)}% FAVORITE` : `${(100 - winProb).toFixed(0)}% CHALLENGER`}
              </span>
            </div>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-dark-secondary)', lineHeight: 1.6 }}>
              Pre-game team strength estimates project a {winProb.toFixed(1)}% win probability for the Lakers based on canonical head-to-head parameters.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
