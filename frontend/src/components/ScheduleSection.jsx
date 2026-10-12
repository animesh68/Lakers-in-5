import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function ScheduleSection({ onSelectGame, selectedGameId }) {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSchedule = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSchedule("2026-27", "LAL", 20);
      const parsedGames = Array.isArray(data) ? data : (data?.games || []);
      setGames(parsedGames);
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Schedule unavailable right now.');
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedule();
  }, []);

  const formatDate = (dateStr) => {
    try {
      const [y, m, d] = dateStr.split('-');
      const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
      const monthNames = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
      return {
        month: monthNames[date.getMonth()],
        day: date.getDate(),
        year: date.getFullYear(),
        full: `${monthNames[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`
      };
    } catch {
      return { month: 'OCT', day: 21, year: 2026, full: dateStr };
    }
  };

  return (
    <section
      id="schedule"
      style={{
        backgroundColor: 'var(--surface-warm)',
        padding: '70px 0 90px 0',
        borderBottom: '1px solid var(--surface-warm-border)',
      }}
    >
      <div className="container">
        {/* Section Header */}
        <div style={{ marginBottom: '32px' }}>
          <div className="section-eyebrow">
            <span>●</span> 2026–27 REGULAR SEASON
          </div>
          <h2 className="section-title">SCHEDULE</h2>
          <p className="section-desc">
            Official regular season schedule. Select any matchup to update game and player forecasts.
          </p>
        </div>

        {loading ? (
          <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-dark-muted)' }}>
            <div className="font-display" style={{ fontSize: '1.4rem' }}>LOADING 2026-27 SCHEDULE...</div>
          </div>
        ) : error ? (
          <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-dark-muted)' }}>
            <div className="font-display" style={{ fontSize: '1.2rem', marginBottom: '8px', color: 'var(--text-dark-primary)' }}>
              Schedule unavailable right now.
            </div>
            <button
              onClick={loadSchedule}
              className="btn-outline-dark"
              style={{ marginTop: '12px' }}
            >
              RETRY
            </button>
          </div>
        ) : games.length === 0 ? (
          <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-dark-muted)' }}>
            <p>No upcoming games found on the schedule.</p>
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {games.map((game, idx) => {
              const isLALHome = game.home_team_code === 'LAL';
              const awayCode = game.away_team_code || (!isLALHome ? 'LAL' : 'OPP');
              const homeCode = game.home_team_code || (isLALHome ? 'LAL' : 'OPP');
              const opponent = isLALHome ? game.away_team : game.home_team;
              const isSelected = selectedGameId === String(game.game_num) || selectedGameId === String(game.game_id);
              const isUpNext = idx === 0;
              const dateInfo = formatDate(game.game_date);

              return (
                <div
                  key={game.game_id || game.game_num}
                  onClick={() => onSelectGame && onSelectGame(game)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '16px',
                    padding: '16px 24px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: isSelected ? '#FFFFFF' : 'var(--surface-warm-card)',
                    border: `1.5px solid ${isSelected ? 'var(--purple-primary)' : 'var(--surface-warm-border)'}`,
                    boxShadow: isSelected ? '0 6px 20px rgba(85, 37, 131, 0.15)' : 'var(--shadow-sm)',
                    cursor: 'pointer',
                    transition: 'all 200ms ease',
                  }}
                  className="schedule-row"
                >
                  {/* Left: Date Block & Up Next Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px', minWidth: '180px' }}>
                    <div style={{ textAlign: 'center', width: '54px' }}>
                      <span className="font-display" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--purple-primary)', display: 'block', lineHeight: 1 }}>
                        {dateInfo.month}
                      </span>
                      <span className="font-display tabular-nums" style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-dark-primary)', display: 'block', lineHeight: 1.1 }}>
                        {dateInfo.day}
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dark-muted)', letterSpacing: '0.06em' }}>
                        GAME #{game.game_num}
                      </span>
                      {isUpNext && (
                        <span className="badge-gold" style={{ marginTop: '3px' }}>
                          UP NEXT
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Center: Matchup Codes & Full Team Name */}
                  <div style={{ flex: '1 1 260px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span
                        className="font-display"
                        style={{
                          fontSize: '1.35rem',
                          fontWeight: 800,
                          color: 'var(--text-dark-primary)',
                          letterSpacing: '0.02em',
                        }}
                      >
                        {awayCode} @ {homeCode}
                      </span>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          backgroundColor: isLALHome ? 'var(--purple-subtle)' : 'var(--surface-warm-subtle)',
                          color: isLALHome ? 'var(--purple-primary)' : 'var(--text-dark-secondary)',
                          textTransform: 'uppercase',
                        }}
                      >
                        {isLALHome ? 'HOME' : 'AWAY'}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-dark-muted)', fontWeight: 500 }}>
                      {isLALHome ? `vs ${opponent}` : `@ ${opponent}`} · {game.game_time || '7:00 PM PST'}
                    </span>
                  </div>

                  {/* Right: Select Action Button */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <button
                      className={isSelected ? "btn-primary" : "btn-outline-dark"}
                      style={{
                        padding: '6px 16px',
                        fontSize: '0.8rem',
                      }}
                    >
                      {isSelected ? 'SELECTED ✓' : 'PREVIEW GAME →'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <style>{`
        .schedule-row:hover {
          border-color: var(--purple-primary) !important;
          transform: translateY(-2px);
          box-shadow: 0 6px 18px rgba(18, 16, 21, 0.08) !important;
        }
      `}</style>
    </section>
  );
}
