import React from 'react';
import { Shield, Target, Gauge, Clock, Home, Flame, Activity } from 'lucide-react';

export default function GameIntelligenceSection({ lakersNext }) {
  const data = lakersNext?.data || {
    win_probability: 0.717,
    expected_margin: 6.2,
    home_advantage_points: 3.2,
    elo_home: 1592,
    elo_away: 1548,
    team_pace: 101.4,
    opp_pace: 99.8,
    team_off_rating: 116.8,
    opp_def_rating: 111.4,
  };

  const eloDiff = (data.elo_home || 1592) - (data.elo_away || 1548);
  const winProbPct = Math.round((data.win_probability || 0.717) * 1000) / 10;

  const factors = [
    {
      title: "ELO POWER RATING ADVANTAGE",
      value: `+${eloDiff} ELO`,
      desc: "Lakers baseline strength rating (1592) holds a positive rating margin over Golden State (1548).",
      impact: "High Positive (+3.8 pts)",
      icon: Target,
      color: "var(--gold-accent)",
    },
    {
      title: "CRYPTO.COM ARENA HOME FLOOR",
      value: "+3.2 PTS",
      desc: "Historical home court advantage accounts for crowd variance and pregame travel rest.",
      impact: "Moderate Positive (+3.2 pts)",
      icon: Home,
      color: "var(--purple-vibrant)",
    },
    {
      title: "OFFENSIVE VS DEFENSIVE RATING",
      value: "+5.4 NET",
      desc: "Lakers 10-game rolling offensive rating (116.8) exceeds Warriors defensive baseline (111.4).",
      impact: "High Positive (+2.4 pts)",
      icon: Flame,
      color: "var(--gold-accent)",
    },
    {
      title: "EXPECTED GAME PACE (POSS/48)",
      value: "100.6 POSS",
      desc: "Blended pace projection expects an up-tempo contest favoring transition initiators.",
      impact: "Neutral (Pace Match)",
      icon: Gauge,
      color: "var(--text-secondary)",
    },
  ];

  return (
    <section 
      id="game-intelligence"
      className="section-spacing"
      style={{
        position: 'relative',
        backgroundColor: '#0E0817',
        borderTop: '1px solid var(--border-subtle)',
      }}
    >
      <div className="container-editorial">
        {/* Section Header */}
        <div 
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.6rem',
            marginBottom: '3.5rem',
          }}
        >
          <span className="banner-marker">
            04 • MATCHUP INTELLIGENCE & FACTORS
          </span>

          <h2 
            className="font-display" 
            style={{ fontSize: 'clamp(2.4rem, 5vw, 4.4rem)', color: '#FFFFFF', letterSpacing: '0.03em', lineHeight: 0.95 }}
          >
            THE FACTORS BEHIND THE SPREAD
          </h2>

          <p 
            style={{
              fontSize: '1.1rem',
              color: 'var(--text-secondary)',
              maxWidth: '680px',
              lineHeight: 1.6,
            }}
          >
            How the machine learning model decomposes home advantage, Elo differentials, 
            and rolling opponent pace into a +6.2 projected margin.
          </p>
        </div>

        {/* Factors Grid */}
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1.5rem',
          }}
        >
          {factors.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div 
                key={idx}
                className="glass-panel"
                style={{
                  padding: '2rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div 
                    style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: item.color,
                    }}
                  >
                    <Icon size={18} />
                  </div>
                  <span 
                    className="font-mono"
                    style={{
                      fontSize: '1.1rem',
                      fontWeight: 800,
                      color: item.color,
                    }}
                  >
                    {item.value}
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <h3 className="font-subheading" style={{ fontSize: '1rem', color: '#FFFFFF', fontWeight: 700 }}>
                    {item.title}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                    {item.desc}
                  </p>
                </div>

                <div 
                  style={{
                    marginTop: 'auto',
                    paddingTop: '0.85rem',
                    borderTop: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span className="broadcast-label" style={{ fontSize: '0.62rem' }}>MODEL IMPACT</span>
                  <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--gold-accent)', fontWeight: 600 }}>
                    {item.impact}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
