import React, { useState, useEffect } from 'react';
import { Sparkles, RefreshCw, Calendar, ChevronDown, ChevronUp, CheckCircle2, ShieldCheck, Zap, Info } from 'lucide-react';
import { api } from '../api';
import StatusBadge from './ui/StatusBadge';
import ProbabilityBar from './ui/ProbabilityBar';

const NBA_TEAMS = [
  { code: 'ATL', name: 'Atlanta Hawks' },
  { code: 'BOS', name: 'Boston Celtics' },
  { code: 'BKN', name: 'Brooklyn Nets' },
  { code: 'CHA', name: 'Charlotte Hornets' },
  { code: 'CHI', name: 'Chicago Bulls' },
  { code: 'CLE', name: 'Cleveland Cavaliers' },
  { code: 'DAL', name: 'Dallas Mavericks' },
  { code: 'DEN', name: 'Denver Nuggets' },
  { code: 'DET', name: 'Detroit Pistons' },
  { code: 'GSW', name: 'Golden State Warriors' },
  { code: 'HOU', name: 'Houston Rockets' },
  { code: 'IND', name: 'Indiana Pacers' },
  { code: 'LAC', name: 'LA Clippers' },
  { code: 'LAL', name: 'Los Angeles Lakers' },
  { code: 'MEM', name: 'Memphis Grizzlies' },
  { code: 'MIA', name: 'Miami Heat' },
  { code: 'MIL', name: 'Milwaukee Bucks' },
  { code: 'MIN', name: 'Minnesota Timberwolves' },
  { code: 'NOP', name: 'New Orleans Pelicans' },
  { code: 'NYK', name: 'New York Knicks' },
  { code: 'OKC', name: 'Oklahoma City Thunder' },
  { code: 'ORL', name: 'Orlando Magic' },
  { code: 'PHI', name: 'Philadelphia 76ers' },
  { code: 'PHX', name: 'Phoenix Suns' },
  { code: 'POR', name: 'Portland Trail Blazers' },
  { code: 'SAC', name: 'Sacramento Kings' },
  { code: 'SAS', name: 'San Antonio Spurs' },
  { code: 'TOR', name: 'Toronto Raptors' },
  { code: 'UTA', name: 'Utah Jazz' },
  { code: 'WAS', name: 'Washington Wizards' },
];

export default function MatchupPredictor({
  simHome,
  setSimHome,
  simAway,
  setSimAway,
  simDate,
  setSimDate,
  simPersist,
  setSimPersist,
  simLoading,
  simResult,
  simError,
  onSimulate,
  matchupGames,
  matchupLoading
}) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  // Quick swap teams helper
  const handleSwapTeams = () => {
    const temp = simHome;
    setSimHome(simAway);
    setSimAway(temp);
  };

  const homeProb = Number(simResult?.home_win_probability ?? 0.5);
  const awayProb = Number(simResult?.away_win_probability ?? (1 - homeProb));
  const margin = Number(simResult?.predicted_home_margin ?? simResult?.predicted_margin ?? 0);

  const isLakersInvolved = simResult && (
    simResult.home_team_id === "1610612747" || 
    simResult.away_team_id === "1610612747" || 
    simResult.home_team?.includes("Lakers") || 
    simResult.away_team?.includes("Lakers")
  );

  const isLakersHome = simResult && (
    simResult.home_team_id === "1610612747" || 
    simResult.home_team?.includes("Lakers")
  );

  const lakersProb = isLakersHome ? homeProb : awayProb;
  const lakersMargin = isLakersHome ? margin : -margin;

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Title */}
      <div>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>NBA Matchup Predictor</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '2px' }}>
          Select any official 2026-27 matchup to generate pregame win probability and projected point margin
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(320px, 420px) 1fr',
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* Matchup Builder Form */}
        <form onSubmit={onSimulate} className="panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={16} color="var(--gold-primary)" />
              Matchup Builder
            </h3>

            <button
              type="button"
              onClick={handleSwapTeams}
              className="btn btn-ghost"
              style={{ fontSize: '0.75rem', padding: '4px 8px' }}
              title="Swap Home and Away Teams"
            >
              ⇄ Swap Teams
            </button>
          </div>

          {/* Home Team Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 600 }}>
              Home Team
            </label>
            <select
              value={simHome}
              onChange={(e) => setSimHome(e.target.value)}
              style={{ width: '100%' }}
            >
              {NBA_TEAMS.map(t => (
                <option key={t.code} value={t.code}>
                  {t.name} ({t.code})
                </option>
              ))}
            </select>
          </div>

          {/* Away Team Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 600 }}>
              Away Team
            </label>
            <select
              value={simAway}
              onChange={(e) => setSimAway(e.target.value)}
              style={{ width: '100%' }}
            >
              {NBA_TEAMS.map(t => (
                <option key={t.code} value={t.code}>
                  {t.name} ({t.code})
                </option>
              ))}
            </select>
          </div>

          {/* Scheduled Game Date Selector */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Scheduled Game Date
              </label>
              {matchupLoading && (
                <span style={{ fontSize: '0.72rem', color: 'var(--gold-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <RefreshCw size={10} className="spin" /> Verifying...
                </span>
              )}
            </div>

            {simHome === simAway ? (
              <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 255, 255, 0.03)', border: '1px dashed var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                Select two distinct teams.
              </div>
            ) : matchupGames.length > 0 ? (
              <select
                value={simDate}
                onChange={(e) => setSimDate(e.target.value)}
                style={{ width: '100%' }}
              >
                {matchupGames.map(g => (
                  <option key={g.game_num} value={g.game_date}>
                    📅 {g.game_date} (Game #{g.game_num} • {g.game_time})
                  </option>
                ))}
              </select>
            ) : !matchupLoading ? (
              <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.25)', color: '#fb7185', fontSize: '0.8rem' }}>
                No scheduled 2026-27 regular season game found for {simHome} hosting {simAway}. Try swapping teams.
              </div>
            ) : (
              <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 255, 255, 0.03)', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                Querying official schedule...
              </div>
            )}
          </div>

          {/* Persist Forecast Checkbox */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <input 
              type="checkbox"
              id="persistForecast"
              checked={simPersist}
              onChange={(e) => setSimPersist(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: 'var(--gold-primary)', cursor: 'pointer' }}
            />
            <label htmlFor="persistForecast" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
              Persist forecast to prediction repository
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={simLoading || matchupLoading || simHome === simAway || (!matchupLoading && matchupGames.length === 0)}
            className="btn btn-gold"
            style={{ width: '100%', padding: '12px', marginTop: '4px' }}
          >
            {simLoading ? <RefreshCw size={16} className="spin" /> : <Sparkles size={16} />}
            {simLoading ? 'Running Champion Pipeline...' : 'Generate Prediction'}
          </button>

          {simError && (
            <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: 'rgba(244, 63, 94, 0.1)', color: '#fb7185', fontSize: '0.82rem' }}>
              {simError}
            </div>
          )}
        </form>

        {/* Prediction Result Display */}
        {simResult ? (
          <div className="panel panel-gold-glow fade-in" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Header / Badges */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <StatusBadge variant="gold">
                  OFFICIAL 2026-27 MATCHUP
                </StatusBadge>
                <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {simResult.game_date}
                </span>
              </div>

              {simResult.prediction_id && (
                <StatusBadge variant="success" icon={CheckCircle2}>
                  Persisted
                </StatusBadge>
              )}
            </div>

            {/* Lakers Focus Callout if Applicable */}
            {isLakersInvolved && (
              <div style={{
                background: 'linear-gradient(135deg, rgba(85, 37, 131, 0.35), rgba(253, 185, 39, 0.12))',
                border: '1px solid var(--gold-border)',
                borderRadius: 'var(--radius-md)',
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px'
              }}>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--gold-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    🌟 Lakers Perspective ({isLakersHome ? 'Home' : 'Away'})
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '2px' }}>
                    Win Probability: {(lakersProb * 100).toFixed(1)}% · Margin: {lakersMargin >= 0 ? `+${lakersMargin.toFixed(1)}` : lakersMargin.toFixed(1)} pts
                  </div>
                </div>

                <StatusBadge variant={lakersProb >= 0.5 ? 'gold' : 'purple'}>
                  {lakersProb >= 0.5 ? 'Lakers Favored' : 'Underdog Contest'}
                </StatusBadge>
              </div>
            )}

            {/* Matchup Summary Grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto 1fr',
              alignItems: 'center',
              textAlign: 'center',
              gap: '20px',
              padding: '12px 0'
            }}>
              <div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFFFFF' }}>{simResult.away_team}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: '2px' }}>Away Team</div>
                <div style={{ fontSize: '1.8rem', fontWeight: 900, fontFamily: 'var(--font-display)', marginTop: '8px', color: awayProb >= 0.5 ? 'var(--gold-primary)' : 'var(--text-secondary)' }}>
                  {(awayProb * 100).toFixed(1)}%
                </div>
              </div>

              <div style={{
                width: '38px',
                height: '38px',
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-medium)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.8rem',
                fontWeight: 800,
                color: 'var(--text-muted)'
              }}>
                @
              </div>

              <div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--gold-primary)' }}>{simResult.home_team}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: '2px' }}>Home Team</div>
                <div style={{ fontSize: '1.8rem', fontWeight: 900, fontFamily: 'var(--font-display)', marginTop: '8px', color: homeProb >= 0.5 ? 'var(--gold-primary)' : 'var(--text-secondary)' }}>
                  {(homeProb * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Probability Comparison Bar */}
            <ProbabilityBar
              homeProb={homeProb}
              awayProb={awayProb}
              homeLabel={simResult.home_team}
              awayLabel={simResult.away_team}
              isHomeLakers={Boolean(simResult.home_team?.includes('Lakers'))}
              isAwayLakers={Boolean(simResult.away_team?.includes('Lakers'))}
              height={12}
            />

            {/* Projected Margin Card */}
            <div className="panel-subtle" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                  Projected Point Margin (Home Perspective)
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: margin >= 0 ? 'var(--emerald-success)' : 'var(--rose-danger)', marginTop: '2px' }}>
                  {margin >= 0 ? `+${margin.toFixed(1)} points` : `${margin.toFixed(1)} points`}
                </div>
              </div>
              <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Ridge Regressor
              </span>
            </div>

            {/* Collapsible Technical Details */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
              <button
                onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                className="btn btn-ghost"
                style={{ fontSize: '0.8rem', padding: '6px 10px', width: '100%', justifyContent: 'space-between' }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Info size={14} /> Technical Model & Feature Snapshot
                </span>
                {showTechnicalDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showTechnicalDetails && (
                <div className="fade-in" style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.75rem' }}>
                  <div className="panel-subtle" style={{ padding: '10px 12px' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Model Version</div>
                    <div style={{ fontWeight: 600, marginTop: '2px' }}>{simResult.model_version}</div>
                  </div>
                  <div className="panel-subtle" style={{ padding: '10px 12px' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Feature Snapshot Hash</div>
                    <div className="mono" style={{ fontWeight: 600, marginTop: '2px', wordBreak: 'break-all' }}>
                      {simResult.feature_snapshot_hash?.slice(0, 16)}...
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="panel" style={{ padding: '60px 32px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <Sparkles size={32} color="var(--gold-primary)" style={{ opacity: 0.6, marginBottom: '14px' }} />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Ready to Predict Matchup</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '360px', margin: '6px auto 0' }}>
              Choose a home team, away team, and scheduled game date, then click Generate Prediction.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
