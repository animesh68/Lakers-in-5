import React, { useState, useEffect } from 'react';
import { Users, RefreshCw, AlertCircle, Sparkles, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../api';
import PlayerCard from './PlayerCard';
import StatusBadge from './ui/StatusBadge';

/**
 * Skeleton Card for Player Projection Loading State
 */
function PlayerCardSkeleton() {
  return (
    <div
      className="panel-subtle"
      style={{
        padding: '16px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        opacity: 0.6
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Circular Avatar Skeleton */}
        <div
          className="skeleton-pulse"
          style={{
            width: '56px',
            height: '56px',
            minWidth: '56px',
            minHeight: '56px',
            maxWidth: '56px',
            maxHeight: '56px',
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.08)',
            flexShrink: 0
          }}
        />

        {/* Text lines */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div
            className="skeleton-pulse"
            style={{ width: '65%', height: '16px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.08)' }}
          />
          <div
            className="skeleton-pulse"
            style={{ width: '35%', height: '12px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.05)' }}
          />
        </div>

        {/* Minutes Skeleton */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
          <div
            className="skeleton-pulse"
            style={{ width: '42px', height: '18px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.08)' }}
          />
          <div
            className="skeleton-pulse"
            style={{ width: '30px', height: '10px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.05)' }}
          />
        </div>
      </div>

      {/* Stats row skeleton */}
      <div
        className="skeleton-pulse"
        style={{
          height: '46px',
          borderRadius: 'var(--radius-sm)',
          background: 'rgba(255, 255, 255, 0.04)'
        }}
      />
    </div>
  );
}

/**
 * Player Projections Section for Matchups and Forecast views
 */
export default function PlayerProjections({
  homeTeam,
  awayTeam,
  gameDate,
  gameId = null,
  initialData = null,
  isLoading = false
}) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(isLoading || (!initialData && Boolean(homeTeam && awayTeam && gameDate)));
  const [error, setError] = useState(null);

  const fetchProjections = async () => {
    if (!homeTeam || !awayTeam || !gameDate) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      let res;
      if (gameId) {
        try {
          res = await api.predictPlayersByGameId(gameId);
        } catch {
          // Fall back to POST /predict/players
          res = await api.predictPlayers(homeTeam, awayTeam, gameDate, gameId);
        }
      } else {
        res = await api.predictPlayers(homeTeam, awayTeam, gameDate);
      }
      setData(res);
    } catch (err) {
      console.warn("Player performance prediction fetch failed:", err);
      setError(err.message || "Player projections are temporarily unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialData) {
      setData(initialData);
      setLoading(false);
      setError(null);
      return;
    }

    if (homeTeam && awayTeam && gameDate) {
      fetchProjections();
    }
  }, [homeTeam, awayTeam, gameDate, gameId, initialData]);

  if (!homeTeam || !awayTeam || !gameDate) {
    return null;
  }

  // Split players by team
  const players = data?.players || [];
  
  // Group players by home vs away
  const homePlayers = [];
  const awayPlayers = [];

  players.forEach((p) => {
    const pTeam = (p.team_code || p.team || '').toLowerCase();
    const hTeam = String(homeTeam).toLowerCase();
    const aTeam = String(awayTeam).toLowerCase();
    const hName = (data?.home_team || '').toLowerCase();
    const aName = (data?.away_team || '').toLowerCase();

    if (pTeam === hTeam || hName.includes(pTeam) || (p.team && hName.includes(p.team.toLowerCase()))) {
      homePlayers.push(p);
    } else if (pTeam === aTeam || aName.includes(pTeam) || (p.team && aName.includes(p.team.toLowerCase()))) {
      awayPlayers.push(p);
    } else {
      // Fallback matching by team code
      if (p.team_code === homeTeam) {
        homePlayers.push(p);
      } else {
        awayPlayers.push(p);
      }
    }
  });

  const displayHomeName = data?.home_team || homeTeam;
  const displayAwayName = data?.away_team || awayTeam;

  return (
    <section
      aria-label="Player Performance Projections"
      className="panel fade-in"
      style={{
        padding: '32px',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        position: 'relative'
      }}
    >
      {/* Section Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '18px'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={20} color="var(--gold-primary)" />
            <h3
              style={{
                fontSize: '1.25rem',
                fontWeight: 800,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: 'var(--text-primary)'
              }}
            >
              PLAYER PROJECTIONS
            </h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '3px' }}>
            Projected performance for players in this matchup.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <StatusBadge variant="gold">
            Expected Rotation
          </StatusBadge>
          {!loading && error && (
            <button
              onClick={fetchProjections}
              className="btn btn-ghost"
              style={{ fontSize: '0.78rem', padding: '4px 10px' }}
            >
              <RefreshCw size={12} /> Retry Projections
            </button>
          )}
        </div>
      </div>

      {/* Content based on state */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ textAlign: 'center', padding: '16px 0', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            <RefreshCw size={20} color="var(--gold-primary)" className="spin" style={{ margin: '0 auto 8px' }} />
            <div>Running player rotation regression models...</div>
          </div>

          <div
            className="player-grid-columns"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '24px'
            }}
          >
            {/* Team 1 Skeleton Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div
                className="skeleton-pulse"
                style={{ width: '40%', height: '20px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.08)' }}
              />
              <PlayerCardSkeleton />
              <PlayerCardSkeleton />
              <PlayerCardSkeleton />
            </div>

            {/* Team 2 Skeleton Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div
                className="skeleton-pulse"
                style={{ width: '40%', height: '20px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.08)' }}
              />
              <PlayerCardSkeleton />
              <PlayerCardSkeleton />
              <PlayerCardSkeleton />
            </div>
          </div>
        </div>
      ) : error ? (
        <div
          className="panel-subtle"
          style={{
            padding: '32px 24px',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
            background: 'rgba(244, 63, 94, 0.05)',
            border: '1px solid rgba(244, 63, 94, 0.2)'
          }}
        >
          <ShieldAlert size={28} color="var(--rose-danger)" />
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Player projections are temporarily unavailable.
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', maxWidth: '420px' }}>
            {error}
          </p>
          <button
            onClick={fetchProjections}
            className="btn btn-secondary"
            style={{ fontSize: '0.82rem', marginTop: '6px' }}
          >
            <RefreshCw size={14} /> Retry
          </button>
        </div>
      ) : players.length === 0 ? (
        <div
          className="panel-subtle"
          style={{
            padding: '36px 24px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            fontSize: '0.9rem'
          }}
        >
          <AlertCircle size={24} color="var(--text-muted)" style={{ margin: '0 auto 8px' }} />
          <div>No player projections available for this matchup.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          {/* Two-Column Team Separation Layout */}
          <div
            className="player-grid-columns"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
              gap: '24px'
            }}
          >
            {/* Away Team Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingBottom: '8px',
                  borderBottom: '2px solid rgba(255, 255, 255, 0.08)'
                }}
              >
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                    Away Team
                  </span>
                  <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#FFFFFF', marginTop: '1px' }}>
                    {displayAwayName}
                  </h4>
                </div>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: 'rgba(255, 255, 255, 0.05)',
                    color: 'var(--text-secondary)'
                  }}
                >
                  {awayPlayers.length} Players
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {awayPlayers.map((player) => (
                  <PlayerCard key={player.player_id || player.player_name} player={player} />
                ))}
              </div>
            </div>

            {/* Home Team Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingBottom: '8px',
                  borderBottom: displayHomeName.includes('Lakers')
                    ? '2px solid var(--gold-border)'
                    : '2px solid rgba(255, 255, 255, 0.08)'
                }}
              >
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                    Home Team
                  </span>
                  <h4
                    style={{
                      fontSize: '1.2rem',
                      fontWeight: 800,
                      color: displayHomeName.includes('Lakers') ? 'var(--gold-primary)' : '#FFFFFF',
                      marginTop: '1px'
                    }}
                  >
                    {displayHomeName}
                  </h4>
                </div>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: displayHomeName.includes('Lakers') ? 'var(--gold-subtle)' : 'rgba(255, 255, 255, 0.05)',
                    color: displayHomeName.includes('Lakers') ? 'var(--gold-primary)' : 'var(--text-secondary)'
                  }}
                >
                  {homePlayers.length} Players
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {homePlayers.map((player) => (
                  <PlayerCard key={player.player_id || player.player_name} player={player} />
                ))}
              </div>
            </div>
          </div>

          {/* Section Footer / Disclaimer */}
          <div
            style={{
              paddingTop: '16px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '10px'
            }}
          >
            <p
              style={{
                fontSize: '0.78rem',
                color: 'var(--text-muted)',
                fontStyle: 'italic',
                margin: 0
              }}
            >
              These are statistical projections, not confirmed lineups or guaranteed outcomes.
            </p>

            {data?.model_versions && (
              <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Player Models: Ridge / GB Multi-Output ({data.feature_schema_version || 'v1.0'})
              </span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
