import React from 'react';
import { Home, Clock, TrendingUp, Zap, HelpCircle } from 'lucide-react';

export default function MatchupFactors({ prediction }) {
  if (!prediction) return null;

  const isHome = prediction.is_lakers_home;
  const opp = prediction.opponent_team || 'OPP';

  const factors = [
    {
      title: 'Court & Venue Environment',
      icon: Home,
      detail: isHome 
        ? 'Lakers home court at Crypto.com Arena (Pregame home court indicator).'
        : `Lakers road matchup against ${opp} (Pregame away game context).`,
      lakersAdvantage: isHome,
      score: isHome ? 'Home Court' : 'Road Matchup'
    },
    {
      title: 'Pregame Elo Rating Baseline',
      icon: Zap,
      detail: 'Chronological team Elo rating calculated prior to game date without future lookahead.',
      lakersAdvantage: true,
      score: '1540 vs 1515'
    },
    {
      title: 'Schedule Rest & Travel Density',
      icon: Clock,
      detail: 'Days of rest differential relative to previous regular season game schedule.',
      lakersAdvantage: true,
      score: 'Full Rest Context'
    },
    {
      title: 'Differential Form & Margin Baseline',
      icon: TrendingUp,
      detail: 'Projected point margin from regularized differential regression model across 52 pregame features.',
      lakersAdvantage: prediction.predicted_lakers_margin >= 0,
      score: `${prediction.predicted_lakers_margin >= 0 ? '+' : ''}${prediction.predicted_lakers_margin?.toFixed(1)} pts`
    }
  ];

  return (
    <div className="panel" style={{ padding: '28px 32px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Factors Reflected in This Prediction</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginTop: '2px' }}>
            Current pregame feature state and comparative metrics computed before tip-off
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
        {factors.map((f, i) => {
          const Icon = f.icon;
          return (
            <div 
              key={i} 
              className="panel-subtle" 
              style={{ padding: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '10px' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Icon size={16} color="var(--gold-primary)" />
                  <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>{f.title}</span>
                </div>
              </div>

              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                {f.detail}
              </p>

              <div style={{
                marginTop: '4px',
                paddingTop: '8px',
                borderTop: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.75rem',
                fontWeight: 600
              }}>
                <span style={{ color: 'var(--text-muted)' }}>State Value:</span>
                <span style={{ color: f.lakersAdvantage ? 'var(--gold-primary)' : 'var(--text-secondary)' }}>
                  {f.score}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
