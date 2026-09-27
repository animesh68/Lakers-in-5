import React from 'react';
import { Calendar, Clock, Zap, RefreshCw, Filter } from 'lucide-react';
import StatusBadge from './ui/StatusBadge';

const NBA_TEAMS = [
  { code: 'LAL', name: 'Los Angeles Lakers' },
  { code: 'BOS', name: 'Boston Celtics' },
  { code: 'GSW', name: 'Golden State Warriors' },
  { code: 'NYK', name: 'New York Knicks' },
  { code: 'DEN', name: 'Denver Nuggets' },
  { code: 'PHX', name: 'Phoenix Suns' },
  { code: 'MIL', name: 'Milwaukee Bucks' },
  { code: 'DAL', name: 'Dallas Mavericks' },
  { code: 'MIA', name: 'Miami Heat' },
  { code: 'LAC', name: 'LA Clippers' },
  { code: 'PHI', name: 'Philadelphia 76ers' },
  { code: 'MIN', name: 'Minnesota Timberwolves' },
  { code: 'OKC', name: 'Oklahoma City Thunder' },
  { code: 'CLE', name: 'Cleveland Cavaliers' },
  { code: 'SAC', name: 'Sacramento Kings' },
  { code: 'IND', name: 'Indiana Pacers' },
  { code: 'ORL', name: 'Orlando Magic' },
  { code: 'HOU', name: 'Houston Rockets' },
  { code: 'CHI', name: 'Chicago Bulls' },
  { code: 'ATL', name: 'Atlanta Hawks' },
  { code: 'BKN', name: 'Brooklyn Nets' },
  { code: 'CHA', name: 'Charlotte Hornets' },
  { code: 'DET', name: 'Detroit Pistons' },
  { code: 'MEM', name: 'Memphis Grizzlies' },
  { code: 'NOP', name: 'New Orleans Pelicans' },
  { code: 'POR', name: 'Portland Trail Blazers' },
  { code: 'SAS', name: 'San Antonio Spurs' },
  { code: 'TOR', name: 'Toronto Raptors' },
  { code: 'UTA', name: 'Utah Jazz' },
  { code: 'WAS', name: 'Washington Wizards' },
];

export default function ScheduleTimeline({
  games,
  loading,
  error,
  selectedTeam,
  onTeamChange,
  limit,
  onLimitChange,
  onPredictGame
}) {
  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title & Filter Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>2026-27 NBA Schedule</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '2px' }}>
            Official regular season schedule — click Predict on any matchup to run pregame inference
          </p>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Team:</span>
            <select
              value={selectedTeam}
              onChange={(e) => onTeamChange(e.target.value)}
              style={{ padding: '8px 12px', fontSize: '0.85rem' }}
            >
              {NBA_TEAMS.map(t => (
                <option key={t.code} value={t.code}>{t.name} ({t.code})</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Show:</span>
            <select
              value={limit}
              onChange={(e) => onLimitChange(Number(e.target.value))}
              style={{ padding: '8px 12px', fontSize: '0.85rem' }}
            >
              <option value={10}>10 games</option>
              <option value={20}>20 games</option>
              <option value={40}>40 games</option>
              <option value={82}>Full Season</option>
            </select>
          </div>
        </div>
      </div>

      {/* Schedule Table / List */}
      <div className="panel" style={{ padding: '12px' }}>
        {loading ? (
          <div style={{ padding: '60px 20px', textAlign: 'center' }}>
            <RefreshCw size={24} color="var(--gold-primary)" className="spin" style={{ margin: '0 auto 12px' }} />
            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Loading schedule records...</div>
          </div>
        ) : error ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#fb7185', fontSize: '0.85rem' }}>
            Failed to load schedule: {error}
          </div>
        ) : games.length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No scheduled games found for this selection.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {games.map((g) => {
              const isLakers = g.is_lakers_game || g.home_team_code === 'LAL' || g.away_team_code === 'LAL';
              return (
                <div
                  key={g.game_num}
                  className="panel-subtle"
                  style={{
                    padding: '14px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '14px',
                    borderLeft: isLakers ? '3px solid var(--gold-primary)' : '1px solid var(--border-subtle)',
                    transition: 'background 0.2s ease, border-color 0.2s ease'
                  }}
                >
                  {/* Game Number & Date */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', minWidth: '170px' }}>
                    <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', width: '65px' }}>
                      #{g.game_num}
                    </span>
                    <div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {g.game_date}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {g.game_time || '7:00 PM'}
                      </div>
                    </div>
                  </div>

                  {/* Matchup Teams */}
                  <div style={{ flex: 1, minWidth: '240px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem', color: g.away_team_code === 'LAL' ? 'var(--gold-primary)' : 'var(--text-primary)' }}>
                      {g.away_team}
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 800 }}>@</span>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem', color: g.home_team_code === 'LAL' ? 'var(--gold-primary)' : 'var(--text-primary)' }}>
                      {g.home_team}
                    </div>
                  </div>

                  {/* Action CTA */}
                  <div>
                    <button
                      onClick={() => onPredictGame(g)}
                      className="btn btn-secondary"
                      style={{ padding: '6px 14px', fontSize: '0.8rem', fontWeight: 700 }}
                    >
                      <Zap size={13} color="var(--gold-primary)" />
                      Predict
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
