import React from 'react';

export default function NextGameSection({
  prediction,
  loading,
  error,
  scheduleGames = [],
  selectedGame,
  onSelectGame,
}) {
  const winProb = prediction ? (prediction.lakers_win_probability * 100).toFixed(1) : '71.7';
  const oppProb = prediction ? (prediction.opponent_win_probability * 100).toFixed(1) : '28.3';
  const margin = prediction ? (prediction.predicted_lakers_margin > 0 ? `+${prediction.predicted_lakers_margin.toFixed(1)}` : prediction.predicted_lakers_margin.toFixed(1)) : '+6.2';

  const isLakersHome = prediction?.is_lakers_home ?? true;
  const opponentName = prediction?.opponent_team || 'Golden State Warriors';
  const gameDate = prediction?.game_date || '2026-10-21';

  // Format date to human readable (e.g. OCTOBER 21 · 2026)
  const formatDate = (dateStr) => {
    try {
      const [y, m, d] = dateStr.split('-');
      const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
      const monthNames = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"];
      return `${monthNames[date.getMonth()]} ${date.getDate()} · ${date.getFullYear()}`;
    } catch {
      return dateStr;
    }
  };

  return (
    <section
      id="next-game"
      style={{
        backgroundColor: 'var(--surface-warm)',
        padding: '90px 0 80px 0',
        borderBottom: '1px solid var(--surface-warm-border)',
      }}
    >
      <div className="container">
        {/* Section Eyebrow */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '16px', marginBottom: '36px' }}>
          <div>
            <div className="section-eyebrow">
              <span>●</span> PREDICTION
            </div>
            <h2 className="section-title">NEXT GAME</h2>
          </div>

          {/* Quick Matchup Selector */}
          {scheduleGames && scheduleGames.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-dark-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                MATCHUP:
              </span>
              <select
                value={selectedGame?.game_id || ''}
                onChange={(e) => {
                  const targetGame = scheduleGames.find(g => (g.game_id || String(g.game_num)) === e.target.value);
                  if (targetGame && onSelectGame) {
                    onSelectGame(targetGame);
                  }
                }}
                style={{
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1.5px solid var(--surface-warm-border)',
                  backgroundColor: 'var(--surface-warm-card)',
                  color: 'var(--text-dark-primary)',
                  fontFamily: 'var(--font-body)',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                {scheduleGames.map((g) => (
                  <option key={g.game_id || g.game_num} value={g.game_id || String(g.game_num)}>
                    {g.game_date} vs {g.home_team_code === 'LAL' ? g.away_team : g.home_team} ({g.home_team_code === 'LAL' ? 'HOME' : 'AWAY'})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Matchup Banner */}
        <div
          style={{
            backgroundColor: 'var(--surface-warm-card)',
            borderRadius: 'var(--radius-lg)',
            border: '1.5px solid var(--surface-warm-border)',
            padding: 'clamp(28px, 4vw, 48px)',
            boxShadow: 'var(--shadow-md)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Top Border Accent */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '4px',
              background: 'linear-gradient(90deg, var(--purple-primary) 0%, var(--gold-accent) 100%)',
            }}
          />

          {loading ? (
            <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-dark-muted)' }}>
              <div className="font-display" style={{ fontSize: '1.4rem' }}>UPDATING PREDICTION...</div>
            </div>
          ) : error ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: '#B91C1C' }}>
              <div className="font-display" style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Unable to load prediction</div>
              <p style={{ fontSize: '0.9rem' }}>{error}</p>
            </div>
          ) : (
            <div>
              {/* Matchup Header: Teams & Date */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '24px',
                  paddingBottom: '36px',
                  borderBottom: '1px solid var(--surface-warm-border)',
                }}
              >
                {/* Away Team */}
                <div style={{ flex: '1 1 240px' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-dark-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '4px' }}>
                    {isLakersHome ? 'VISITOR' : 'HOST'}
                  </div>
                  <div className="font-display" style={{ fontSize: 'clamp(1.6rem, 3vw, 2.4rem)', fontWeight: 700, lineHeight: 1.1, color: 'var(--text-dark-primary)' }}>
                    {isLakersHome ? opponentName : 'LOS ANGELES LAKERS'}
                  </div>
                </div>

                {/* VS / @ Indicator */}
                <div style={{ textAlign: 'center', padding: '0 16px' }}>
                  <span
                    className="font-display"
                    style={{
                      fontSize: '1.8rem',
                      fontWeight: 800,
                      color: 'var(--purple-primary)',
                      display: 'block',
                    }}
                  >
                    @
                  </span>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark-muted)', letterSpacing: '0.08em' }}>
                    {formatDate(gameDate)}
                  </span>
                </div>

                {/* Home Team */}
                <div style={{ flex: '1 1 240px', textAlign: 'right' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-dark-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '4px' }}>
                    {isLakersHome ? 'HOST' : 'VISITOR'}
                  </div>
                  <div
                    className="font-display"
                    style={{
                      fontSize: 'clamp(1.6rem, 3vw, 2.4rem)',
                      fontWeight: 700,
                      lineHeight: 1.1,
                      color: isLakersHome ? 'var(--purple-primary)' : 'var(--text-dark-primary)',
                    }}
                  >
                    {isLakersHome ? 'LOS ANGELES LAKERS' : opponentName}
                  </div>
                </div>
              </div>

              {/* Major Prediction Display */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: '32px',
                  paddingTop: '36px',
                  alignItems: 'center',
                }}
              >
                {/* Win Probability Hero */}
                <div style={{ textAlign: 'center', padding: '16px' }}>
                  <div
                    className="font-display tabular-nums"
                    style={{
                      fontSize: 'clamp(3.5rem, 7vw, 5.5rem)',
                      fontWeight: 800,
                      lineHeight: 0.95,
                      color: 'var(--purple-primary)',
                      marginBottom: '8px',
                    }}
                  >
                    {winProb}%
                  </div>
                  <div
                    className="font-display"
                    style={{
                      fontSize: '1.05rem',
                      fontWeight: 700,
                      letterSpacing: '0.12em',
                      color: 'var(--text-dark-secondary)',
                    }}
                  >
                    LAKERS WIN PROBABILITY
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-dark-muted)', marginTop: '4px' }}>
                    Opponent Probability: {oppProb}%
                  </div>
                </div>

                {/* Projected Margin */}
                <div
                  style={{
                    textAlign: 'center',
                    padding: '24px',
                    backgroundColor: 'var(--surface-warm)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--surface-warm-border)',
                  }}
                >
                  <div
                    className="font-display tabular-nums"
                    style={{
                      fontSize: 'clamp(2.8rem, 5vw, 4rem)',
                      fontWeight: 800,
                      lineHeight: 1,
                      color: 'var(--text-dark-primary)',
                      marginBottom: '6px',
                    }}
                  >
                    {margin}
                  </div>
                  <div
                    className="font-display"
                    style={{
                      fontSize: '0.95rem',
                      fontWeight: 700,
                      letterSpacing: '0.1em',
                      color: 'var(--text-dark-secondary)',
                      textTransform: 'uppercase',
                    }}
                  >
                    PROJECTED POINT MARGIN
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-dark-muted)', marginTop: '4px' }}>
                    {parseFloat(margin) > 0 ? 'Favorable Lakers Spread' : 'Challenger Spread'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
