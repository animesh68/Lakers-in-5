import React from 'react';
import { Calendar, Clock, ChevronRight, Zap } from 'lucide-react';
import StatusBadge from './ui/StatusBadge';

export default function UpcomingLakers({ games, onSelectGame, currentPredictionDate }) {
  if (!games || games.length === 0) return null;

  // Show top 4 upcoming games
  const displayGames = games.slice(0, 4);

  return (
    <div className="panel" style={{ padding: '28px 32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Upcoming Lakers Schedule</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginTop: '2px' }}>
            Next scheduled 2026-27 contests — click any matchup to run inference
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
        {displayGames.map((g) => {
          const isCurrent = g.game_date === currentPredictionDate;
          const isHome = g.home_team_code === 'LAL' || g.home_team?.includes('Lakers');
          const opp = isHome ? g.away_team : g.home_team;
          const oppCode = isHome ? (g.away_team_code || 'OPP') : (g.home_team_code || 'HOST');

          return (
            <div
              key={g.game_num}
              className="panel-subtle"
              style={{
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '12px',
                borderColor: isCurrent ? 'var(--gold-border)' : 'var(--border-subtle)',
                background: isCurrent ? 'rgba(253, 185, 39, 0.03)' : 'rgba(255, 255, 255, 0.02)'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Game #{g.game_num}
                  </span>
                  {isCurrent ? (
                    <StatusBadge variant="gold">Active Focus</StatusBadge>
                  ) : (
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                      {isHome ? '🏠 Home' : '✈️ Road'}
                    </span>
                  )}
                </div>

                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {isHome ? `${oppCode} @ LAL` : `LAL @ ${oppCode}`}
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {opp}
                </div>
              </div>

              <div style={{
                paddingTop: '10px',
                borderTop: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  📅 {g.game_date}
                </div>

                <button
                  onClick={() => onSelectGame(g)}
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '0.75rem', fontWeight: 700 }}
                >
                  <Zap size={12} color="var(--gold-primary)" />
                  Predict
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
