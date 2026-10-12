import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { getPlayerMeta, getVerifiedPlayerHeadshotUrl } from '../utils/playerMapping';

/**
 * Editorial NBA Broadcast Player Strip / Row (White / Warm White Surface)
 * Matches the Upcoming Matches design system.
 * Full-width, compact, data-driven with verified player headshot or neutral silhouette.
 */
export function PlayerStatStrip({ player }) {
  const meta = getPlayerMeta(player);
  const isLakers = player.team_code === 'LAL' || (player.team && player.team.includes('Lakers'));
  const [imgError, setImgError] = useState(false);

  const jerseyNumber = meta?.jersey || (player.jersey_number ? `#${player.jersey_number}` : null);
  const position = meta?.position || 'ROTATION';

  // Strictly verified official NBA CDN individual headshot; NEVER footer assets
  const headshotUrl = getVerifiedPlayerHeadshotUrl(player);
  const showPhoto = Boolean(headshotUrl) && !imgError;

  const pts = typeof player.predicted_points === 'number' ? player.predicted_points.toFixed(1) : '0.0';
  const reb = typeof player.predicted_rebounds === 'number' ? player.predicted_rebounds.toFixed(1) : '0.0';
  const ast = typeof player.predicted_assists === 'number' ? player.predicted_assists.toFixed(1) : '0.0';
  const min = typeof player.expected_minutes === 'number' ? player.expected_minutes.toFixed(1) : '0.0';

  return (
    <div
      className="player-stat-strip-white"
      style={{
        backgroundColor: 'var(--surface-warm-card)',
        borderRadius: 'var(--radius-md)',
        border: '1.5px solid var(--surface-warm-border)',
        borderLeft: isLakers ? '4px solid var(--purple-primary)' : '4px solid var(--surface-warm-border)',
        padding: '12px 20px',
        display: 'grid',
        gridTemplateColumns: 'minmax(280px, 3.5fr) minmax(100px, 1fr) minmax(140px, 1.5fr) minmax(100px, 1.1fr) minmax(85px, 0.9fr) minmax(85px, 0.9fr)',
        alignItems: 'center',
        gap: '16px',
        width: '100%',
        boxShadow: 'var(--shadow-sm)',
        transition: 'all 200ms ease',
      }}
    >
      {/* 1. PLAYER IDENTITY: Verified Headshot or Neutral Silhouette, Jersey Number & Full Name */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0 }}>
        {/* Compact Profile Portrait (46px) */}
        <div
          style={{
            width: '46px',
            height: '46px',
            minWidth: '46px',
            minHeight: '46px',
            borderRadius: '50%',
            overflow: 'hidden',
            backgroundColor: isLakers ? 'var(--purple-subtle)' : 'var(--surface-warm-subtle)',
            border: isLakers ? '1.5px solid var(--purple-border)' : '1.5px solid var(--surface-warm-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
          }}
        >
          {showPhoto ? (
            <img
              src={headshotUrl}
              alt={player.player_name}
              onError={() => setImgError(true)}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                objectPosition: 'center 15%',
                display: 'block',
              }}
              loading="lazy"
            />
          ) : (
            /* Neutral Silhouette Placeholder */
            <div
              className="player-neutral-silhouette"
              title={`${player.player_name} (Silhouette)`}
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: isLakers ? 'var(--purple-primary)' : 'var(--text-dark-secondary)',
              }}
            >
              <svg
                viewBox="0 0 24 24"
                width="24"
                height="24"
                fill="currentColor"
                style={{ opacity: 0.8 }}
                aria-hidden="true"
              >
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
              </svg>
            </div>
          )}
        </div>

        {/* Jersey Number & Full Name */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', minWidth: 0 }}>
          {jerseyNumber && (
            <span
              className="font-display tabular-nums"
              style={{
                fontSize: '1.2rem',
                fontWeight: 800,
                color: isLakers ? 'var(--purple-primary)' : 'var(--text-dark-muted)',
                flexShrink: 0,
              }}
            >
              {jerseyNumber}
            </span>
          )}
          <span
            className="font-display"
            style={{
              fontSize: '1.25rem',
              fontWeight: 800,
              color: 'var(--text-dark-primary)',
              letterSpacing: '0.02em',
              lineHeight: 1.1,
              whiteSpace: 'normal',
              wordBreak: 'break-word',
            }}
          >
            {player.player_name}
          </span>
        </div>
      </div>

      {/* 2. POSITION */}
      <div>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: isLakers ? 'var(--purple-primary)' : 'var(--text-dark-secondary)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            backgroundColor: isLakers ? 'var(--purple-subtle)' : 'var(--surface-warm-subtle)',
            padding: '3px 8px',
            borderRadius: '4px',
            border: isLakers ? '1px solid var(--purple-border)' : '1px solid var(--surface-warm-border)',
            display: 'inline-block',
          }}
        >
          {position}
        </span>
      </div>

      {/* 3. PRIMARY STAT: PROJECTED PTS */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '5px' }}>
        <span
          className="font-display tabular-nums"
          style={{
            fontSize: '1.75rem',
            fontWeight: 800,
            color: 'var(--purple-primary)',
            lineHeight: 1,
          }}
        >
          {pts}
        </span>
        <span
          className="font-display"
          style={{
            fontSize: '0.75rem',
            letterSpacing: '0.08em',
            color: 'var(--text-dark-muted)',
            fontWeight: 700,
          }}
        >
          PTS
        </span>
      </div>

      {/* 4. MINUTES */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '5px' }}>
        <span
          className="font-display tabular-nums"
          style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            color: 'var(--text-dark-primary)',
            lineHeight: 1,
          }}
        >
          {min}
        </span>
        <span
          style={{
            fontSize: '0.72rem',
            letterSpacing: '0.06em',
            color: 'var(--text-dark-muted)',
            fontWeight: 600,
          }}
        >
          MIN
        </span>
      </div>

      {/* 5. REBOUNDS */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
        <span
          className="font-display tabular-nums"
          style={{
            fontSize: '1.2rem',
            fontWeight: 700,
            color: 'var(--text-dark-primary)',
            lineHeight: 1,
          }}
        >
          {reb}
        </span>
        <span
          className="font-display"
          style={{
            fontSize: '0.7rem',
            color: 'var(--text-dark-muted)',
            letterSpacing: '0.06em',
            fontWeight: 600,
          }}
        >
          REB
        </span>
      </div>

      {/* 6. ASSISTS */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
        <span
          className="font-display tabular-nums"
          style={{
            fontSize: '1.2rem',
            fontWeight: 700,
            color: 'var(--text-dark-primary)',
            lineHeight: 1,
          }}
        >
          {ast}
        </span>
        <span
          className="font-display"
          style={{
            fontSize: '0.7rem',
            color: 'var(--text-dark-muted)',
            letterSpacing: '0.06em',
            fontWeight: 600,
          }}
        >
          AST
        </span>
      </div>
    </div>
  );
}

export default function PlayerProjectionsSection({ gameId, homeTeam, awayTeam, gameDate }) {
  const [projections, setProjections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTeamCode, setActiveTeamCode] = useState(homeTeam || 'LAL');

  // Sync active team code when homeTeam changes
  useEffect(() => {
    setActiveTeamCode(homeTeam || 'LAL');
  }, [homeTeam]);

  // Load game-specific player projections from backend
  useEffect(() => {
    let isCancelled = false;
    const loadPlayers = async () => {
      // Clear stale matchup projections immediately so previous game's players are never retained
      setProjections([]);
      setLoading(true);
      setError(null);
      try {
        let data;
        if (gameId && !isNaN(parseInt(gameId))) {
          data = await api.predictPlayersByGameId(parseInt(gameId));
        } else {
          data = await api.predictPlayers(homeTeam || 'LAL', awayTeam || 'GSW', gameDate || '2026-10-21', gameId);
        }

        if (!isCancelled) {
          const playersList = data?.players || [];
          setProjections(playersList);
          // Default to active team
          if (playersList.some(p => p.team_code === (homeTeam || 'LAL'))) {
            setActiveTeamCode(homeTeam || 'LAL');
          } else if (playersList.length > 0) {
            setActiveTeamCode(playersList[0].team_code);
          }
          setLoading(false);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err.message || 'Unable to load player projections');
          setLoading(false);
        }
      }
    };

    loadPlayers();
    return () => { isCancelled = true; };
  }, [gameId, homeTeam, awayTeam, gameDate]);

  // Filter players for active team
  let teamPlayers = projections.filter(p => p.team_code === activeTeamCode);

  // For Lakers games, display Luka Dončić before Austin Reaves
  if (activeTeamCode === 'LAL' || activeTeamCode === 'Los Angeles Lakers') {
    const lukaIdx = teamPlayers.findIndex(p => {
      const name = String(p.player_name || '').toLowerCase();
      return name.includes('luka') || String(p.player_id) === '1629029';
    });
    const reavesIdx = teamPlayers.findIndex(p => {
      const name = String(p.player_name || '').toLowerCase();
      return name.includes('reaves') || String(p.player_id) === '1630559';
    });
    if (lukaIdx > -1 && reavesIdx > -1 && lukaIdx > reavesIdx) {
      const luka = teamPlayers[lukaIdx];
      const withoutLuka = teamPlayers.filter((_, i) => i !== lukaIdx);
      const newReavesIdx = withoutLuka.findIndex(p => {
        const name = String(p.player_name || '').toLowerCase();
        return name.includes('reaves') || String(p.player_id) === '1630559';
      });
      withoutLuka.splice(newReavesIdx, 0, luka);
      teamPlayers = withoutLuka;
    }
  }

  return (
    <section
      id="player-projections"
      style={{
        backgroundColor: 'var(--surface-warm)',
        padding: '60px 0 80px 0',
        borderBottom: '1px solid var(--surface-warm-border)',
      }}
    >
      <div className="container">
        {/* Section Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '16px', marginBottom: '28px' }}>
          <div>
            <div className="section-eyebrow">
              <span>●</span> LINEUP & ROTATION
            </div>
            <h2 className="section-title">THE ROTATION</h2>
            <p className="section-desc">
              Projected player performances for this matchup.
            </p>
          </div>

          {/* Team Switcher Tabs */}
          <div
            style={{
              display: 'flex',
              backgroundColor: 'var(--surface-warm-subtle)',
              padding: '4px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--surface-warm-border)',
            }}
          >
            <button
              onClick={() => setActiveTeamCode(homeTeam || 'LAL')}
              className="font-display"
              style={{
                padding: '8px 18px',
                border: 'none',
                borderRadius: 'var(--radius-xs)',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                backgroundColor: activeTeamCode === (homeTeam || 'LAL') ? 'var(--purple-primary)' : 'transparent',
                color: activeTeamCode === (homeTeam || 'LAL') ? '#FFFFFF' : 'var(--text-dark-secondary)',
                transition: 'all 200ms ease',
              }}
            >
              [ {homeTeam || 'LAL'} ]
            </button>
            <button
              onClick={() => setActiveTeamCode(awayTeam || 'GSW')}
              className="font-display"
              style={{
                padding: '8px 18px',
                border: 'none',
                borderRadius: 'var(--radius-xs)',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                backgroundColor: activeTeamCode === (awayTeam || 'GSW') ? 'var(--purple-primary)' : 'transparent',
                color: activeTeamCode === (awayTeam || 'GSW') ? '#FFFFFF' : 'var(--text-dark-secondary)',
                transition: 'all 200ms ease',
              }}
            >
              [ {awayTeam || 'GSW'} ]
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '50px 0', textAlign: 'center', color: 'var(--text-dark-muted)' }}>
            <div className="font-display" style={{ fontSize: '1.3rem' }}>GENERATING ROTATION PROJECTIONS...</div>
          </div>
        ) : error ? (
          <div style={{ padding: '36px 0', textAlign: 'center', color: '#B91C1C' }}>
            <div className="font-display" style={{ fontSize: '1.15rem', marginBottom: '8px' }}>Unable to load player projections</div>
            <p style={{ fontSize: '0.88rem' }}>{error}</p>
          </div>
        ) : teamPlayers.length === 0 ? (
          <div style={{ padding: '36px 0', textAlign: 'center', color: 'var(--text-dark-muted)' }}>
            <p>No player projections available for this matchup.</p>
          </div>
        ) : (
          <div style={{ width: '100%' }}>
            {/* COLUMN HEADER ROW (Desktop) */}
            <div
              className="rotation-table-header"
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(280px, 3.5fr) minmax(100px, 1fr) minmax(140px, 1.5fr) minmax(100px, 1.1fr) minmax(85px, 0.9fr) minmax(85px, 0.9fr)',
                padding: '0 20px 10px 20px',
                gap: '16px',
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'var(--text-dark-muted)',
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                textTransform: 'uppercase',
                borderBottom: '1.5px solid var(--surface-warm-border)',
                marginBottom: '12px',
              }}
            >
              <div>PLAYER</div>
              <div>POSITION</div>
              <div>PROJECTED PTS</div>
              <div>MINUTES</div>
              <div>REB</div>
              <div>AST</div>
            </div>

            {/* FULL-WIDTH WHITE PLAYER STRIPS STACKED VERTICALLY */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                width: '100%',
              }}
            >
              {teamPlayers.map((player) => (
                <PlayerStatStrip
                  key={player.player_id}
                  player={player}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      <style>{`
        .player-stat-strip-white:hover {
          transform: translateY(-2px);
          border-color: var(--purple-primary) !important;
          box-shadow: 0 6px 18px rgba(85, 37, 131, 0.12) !important;
        }

        @media (max-width: 768px) {
          .rotation-table-header {
            display: none !important;
          }
          .player-stat-strip-white {
            grid-template-columns: 1fr auto !important;
            grid-template-areas: 
              "identity position"
              "stats stats" !important;
            gap: 12px !important;
            padding: 14px 16px !important;
          }
          .player-stat-strip-white > div:nth-child(1) {
            grid-area: identity;
          }
          .player-stat-strip-white > div:nth-child(2) {
            grid-area: position;
            justify-self: end;
          }
          .player-stat-strip-white > div:nth-child(n+3) {
            display: inline-flex !important;
            margin-right: 12px;
          }
        }
      `}</style>
    </section>
  );
}
