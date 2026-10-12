import React, { useState } from 'react';
import StatusBadge from './ui/StatusBadge';
import { getVerifiedPlayerHeadshotUrl } from '../utils/playerMapping';

/**
 * Extracts 2-letter initials from a player's full name (e.g., "LeBron James" -> "LJ").
 */
function getPlayerInitials(name) {
  if (!name) return '??';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Formats statistics to 1 decimal place.
 */
function formatStat(value) {
  if (value === null || value === undefined || isNaN(value)) return '0.0';
  return Number(value).toFixed(1);
}

/**
 * Circular Player Profile Image & Stats Card
 */
export default function PlayerCard({ player }) {
  const [imgError, setImgError] = useState(false);

  // Authoritative verified individual NBA headshot; never footer assets
  const headshotUrl = getVerifiedPlayerHeadshotUrl(player);
  const showFallback = !headshotUrl || imgError;
  const initials = getPlayerInitials(player.player_name);
  const isLakers = player.team_code === 'LAL' || (player.team && player.team.includes('Lakers'));

  return (
    <div
      className="player-card panel-subtle"
      style={{
        padding: '16px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        transition: 'transform 0.2s ease, border-color 0.2s ease, background 0.2s ease',
        position: 'relative'
      }}
    >
      {/* Top Header: Circular Profile Avatar + Player Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* MANDATORY CIRCULAR PROFILE IMAGE CONTAINER */}
        <div
          className="player-avatar-circle"
          style={{
            width: '56px',
            height: '56px',
            minWidth: '56px',
            minHeight: '56px',
            maxWidth: '56px',
            maxHeight: '56px',
            borderRadius: '50%',
            overflow: 'hidden',
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: isLakers
              ? 'linear-gradient(135deg, rgba(85, 37, 131, 0.45) 0%, rgba(253, 185, 39, 0.2) 100%)'
              : 'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(22, 18, 36, 0.8) 100%)',
            border: isLakers ? '2px solid var(--gold-border)' : '2px solid var(--border-medium)',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.35)',
            boxSizing: 'border-box'
          }}
        >
          {!showFallback ? (
            <img
              src={headshotUrl}
              alt={player.player_name}
              onError={() => setImgError(true)}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                borderRadius: '50%',
                display: 'block'
              }}
              loading="lazy"
            />
          ) : (
            <span
              style={{
                fontSize: '1.05rem',
                fontWeight: 800,
                fontFamily: 'var(--font-display)',
                color: isLakers ? 'var(--gold-primary)' : 'var(--text-secondary)',
                letterSpacing: '0.05em',
                userSelect: 'none'
              }}
            >
              {initials}
            </span>
          )}
        </div>

        {/* Player Name and Metadata */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: '1.02rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              lineHeight: 1.2
            }}
            title={player.player_name}
          >
            {player.player_name}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', flexWrap: 'wrap' }}>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: isLakers ? 'var(--gold-primary)' : 'var(--text-muted)',
                letterSpacing: '0.05em',
                textTransform: 'uppercase'
              }}
            >
              {player.team_code || player.team}
            </span>

            {player.is_transition_player && (
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  padding: '1px 6px',
                  borderRadius: 'var(--radius-full)',
                  background: 'rgba(59, 130, 246, 0.15)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  color: '#60a5fa'
                }}
                title="Offseason roster transfer"
              >
                Offseason Transfer
              </span>
            )}
          </div>
        </div>

        {/* Prominent Expected Minutes Badge */}
        <div
          style={{
            textAlign: 'right',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            flexShrink: 0
          }}
        >
          <div
            style={{
              fontSize: '1.15rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: Number(player.expected_minutes) >= 25 ? 'var(--gold-primary)' : 'var(--text-primary)',
              lineHeight: 1
            }}
          >
            {formatStat(player.expected_minutes)}
          </div>
          <div
            style={{
              fontSize: '0.68rem',
              color: 'var(--text-muted)',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginTop: '3px'
            }}
          >
            Proj Min
          </div>
        </div>
      </div>

      {/* Statistical Projections Row (PTS, REB, AST) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '8px',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '10px 8px',
          textAlign: 'center'
        }}
      >
        {/* Points */}
        <div>
          <div
            style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}
          >
            PTS
          </div>
          <div
            style={{
              fontSize: '1.15rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: '#FFFFFF',
              marginTop: '2px'
            }}
          >
            {formatStat(player.predicted_points)}
          </div>
        </div>

        {/* Rebounds */}
        <div style={{ borderLeft: '1px solid var(--border-subtle)', borderRight: '1px solid var(--border-subtle)' }}>
          <div
            style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}
          >
            REB
          </div>
          <div
            style={{
              fontSize: '1.15rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: '#FFFFFF',
              marginTop: '2px'
            }}
          >
            {formatStat(player.predicted_rebounds)}
          </div>
        </div>

        {/* Assists */}
        <div>
          <div
            style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}
          >
            AST
          </div>
          <div
            style={{
              fontSize: '1.15rem',
              fontWeight: 800,
              fontFamily: 'var(--font-display)',
              color: '#FFFFFF',
              marginTop: '2px'
            }}
          >
            {formatStat(player.predicted_assists)}
          </div>
        </div>
      </div>
    </div>
  );
}
