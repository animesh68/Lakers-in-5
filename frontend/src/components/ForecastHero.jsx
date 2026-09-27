import React from 'react';
import { Sparkles, Calendar, Clock, MapPin, RefreshCw, ArrowRight, ShieldAlert, Award } from 'lucide-react';
import StatusBadge from './ui/StatusBadge';
import ProbabilityBar from './ui/ProbabilityBar';

export default function ForecastHero({ prediction, loading, error, onRefresh, onExploreMatchup }) {
  if (loading) {
    return (
      <div className="panel" style={{ padding: '60px 32px', textAlign: 'center' }}>
        <RefreshCw size={28} color="var(--gold-primary)" className="spin" style={{ margin: '0 auto 16px' }} />
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Extracting Pregame State & Running Champion Models...</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '6px' }}>
          Querying official 2026-27 schedule and computing differential rotations
        </p>
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="panel" style={{ padding: '40px 32px', textAlign: 'center' }}>
        <ShieldAlert size={28} color="var(--rose-danger)" style={{ margin: '0 auto 12px' }} />
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Unable to Load Next Lakers Prediction</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px', maxWidth: '400px', margin: '6px auto 16px' }}>
          {error || 'No upcoming Lakers game scheduled.'}
        </p>
        <button onClick={onRefresh} className="btn btn-secondary">
          <RefreshCw size={14} /> Retry
        </button>
      </div>
    );
  }

  const isHome = prediction.is_lakers_home;
  const lakersProb = Number(prediction.lakers_win_probability ?? 0.5);
  const opponentProb = Number(prediction.opponent_win_probability ?? (1 - lakersProb));
  const lakersMargin = Number(prediction.predicted_lakers_margin ?? 0);
  const isFavored = lakersProb >= 0.5;

  // Format date: e.g. "2026-10-21" -> "Wednesday, October 21, 2026"
  const formatDateDisplay = (dateStr) => {
    try {
      const [y, m, d] = dateStr.split('-');
      const dt = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
      return dt.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const opponentName = prediction.opponent_name || prediction.opponent_team || 'Opponent';

  return (
    <div className="panel panel-gold-glow fade-in" style={{ padding: '36px 32px' }}>
      {/* Top Meta Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        paddingBottom: '20px',
        borderBottom: '1px solid var(--border-subtle)',
        marginBottom: '28px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <StatusBadge variant="gold">
            NEXT LAKERS GAME
          </StatusBadge>
          <StatusBadge variant={isFavored ? 'gold' : 'purple'}>
            {isFavored ? 'Lakers Favored' : 'Underdog Matchup'}
          </StatusBadge>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Calendar size={14} color="var(--gold-primary)" />
            {formatDateDisplay(prediction.game_date)}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Clock size={14} color="var(--gold-primary)" />
            {prediction.game_time || '7:00 PM PST'}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <MapPin size={14} color="var(--gold-primary)" />
            {isHome ? 'Crypto.com Arena (Home)' : 'Road Matchup (Away)'}
          </span>
        </div>
      </div>

      {/* Matchup Header */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr auto 1fr',
        alignItems: 'center',
        textAlign: 'center',
        gap: '24px',
        marginBottom: '32px'
      }}>
        {/* Away Team */}
        <div style={{ textAlign: isHome ? 'left' : 'right' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {isHome ? 'Away Team' : 'Home Team'}
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: isHome ? 'var(--text-primary)' : 'var(--gold-primary)', marginTop: '2px' }}>
            {isHome ? opponentName : 'Los Angeles Lakers'}
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-secondary)', marginTop: '4px' }}>
            {isHome ? `${(opponentProb * 100).toFixed(1)}% Win Prob` : `${(lakersProb * 100).toFixed(1)}% Win Prob`}
          </div>
        </div>

        {/* VS Divider */}
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-medium)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'var(--font-display)',
          fontWeight: 800,
          fontSize: '0.85rem',
          color: 'var(--text-muted)'
        }}>
          VS
        </div>

        {/* Home Team */}
        <div style={{ textAlign: isHome ? 'right' : 'left' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {isHome ? 'Home Team' : 'Away Team'}
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: isHome ? 'var(--gold-primary)' : 'var(--text-primary)', marginTop: '2px' }}>
            {isHome ? 'Los Angeles Lakers' : opponentName}
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-secondary)', marginTop: '4px' }}>
            {isHome ? `${(lakersProb * 100).toFixed(1)}% Win Prob` : `${(opponentProb * 100).toFixed(1)}% Win Prob`}
          </div>
        </div>
      </div>

      {/* Central Focal Stat Callout */}
      <div style={{
        background: 'linear-gradient(180deg, rgba(85, 37, 131, 0.15) 0%, rgba(22, 18, 36, 0.6) 100%)',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius-md)',
        padding: '28px 24px',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px'
      }}>
        <div style={{ fontSize: '0.85rem', fontWeight: 700, color: isFavored ? 'var(--gold-primary)' : '#fb7185', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {isFavored ? '🏆 LAKERS PROJECTED WIN' : '⚠️ UNDERDOG CONTEST'}
        </div>

        <div className="hero-metric-text" style={{
          fontSize: '4.4rem',
          fontWeight: 900,
          fontFamily: 'var(--font-display)',
          letterSpacing: '-0.03em',
          color: '#FFFFFF',
          lineHeight: 1
        }}>
          {(lakersProb * 100).toFixed(1)}%
        </div>

        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
          Lakers Model Win Probability
        </div>

        {/* Projected Margin Callout */}
        <div style={{
          marginTop: '4px',
          padding: '6px 16px',
          borderRadius: 'var(--radius-full)',
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid var(--border-subtle)',
          fontSize: '1.05rem',
          fontWeight: 700,
          color: lakersMargin >= 0 ? 'var(--emerald-success)' : 'var(--rose-danger)'
        }}>
          Projected Margin: {lakersMargin >= 0 ? `+${lakersMargin.toFixed(1)} pts` : `${lakersMargin.toFixed(1)} pts`}
        </div>

        {/* Probability Dual Bar */}
        <div style={{ width: '100%', maxWidth: '460px', marginTop: '14px' }}>
          <ProbabilityBar
            homeProb={isHome ? lakersProb : opponentProb}
            awayProb={isHome ? opponentProb : lakersProb}
            homeLabel={isHome ? 'LAL' : prediction.opponent_team || 'OPP'}
            awayLabel={isHome ? prediction.opponent_team || 'OPP' : 'LAL'}
            isHomeLakers={isHome}
            isAwayLakers={!isHome}
            height={12}
          />
        </div>
      </div>

      {/* Bottom CTA */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
        <button 
          onClick={onExploreMatchup}
          className="btn btn-secondary"
          style={{ fontSize: '0.85rem' }}
        >
          Simulate in Matchup Builder <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
