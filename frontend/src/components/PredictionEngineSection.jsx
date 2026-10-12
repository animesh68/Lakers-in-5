import React from 'react';
import { Cpu, ShieldCheck, Database, BarChart3, LineChart, Binary, CheckCircle2, Layers } from 'lucide-react';

export default function PredictionEngineSection() {
  const featureWeights = [
    { name: "Rolling Scoring Efficiency (Last 10)", key: "rolling_pts_10", weight: 0.24, category: "Offense" },
    { name: "Opponent Defensive Rating", key: "opp_def_rating_10", weight: 0.21, category: "Defense" },
    { name: "Elo Strength Differential", key: "elo_diff", weight: 0.18, category: "Pace/Elo" },
    { name: "Rest & Back-to-Back Differential", key: "rest_days_diff", weight: 0.14, category: "Schedule" },
    { name: "Home Court Point Advantage", key: "is_home", weight: 0.12, category: "Venue" },
    { name: "Offseason Roster Integration", key: "days_since_team_change", weight: 0.11, category: "Chemistry" },
  ];

  return (
    <section 
      id="prediction-engine"
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
            02 • QUANTITATIVE INTELLIGENCE ARCHITECTURE
          </span>

          <h2 
            className="font-display" 
            style={{ fontSize: 'clamp(2.4rem, 5vw, 4.4rem)', color: '#FFFFFF', letterSpacing: '0.03em', lineHeight: 0.95 }}
          >
            THE NUMBERS SEE IT FIRST.
          </h2>

          <p 
            style={{
              fontSize: '1.1rem',
              color: 'var(--text-secondary)',
              maxWidth: '680px',
              lineHeight: 1.6,
            }}
          >
            Lakers in 5 synthesizes analytical lakehouse data, exponential rolling form, 
            opponent-adjusted pace, and role-stratified regressions into real-time pregame projections.
          </p>
        </div>

        {/* 3 Pillars Grid */}
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1.5rem',
            marginBottom: '3rem',
          }}
        >
          {/* Pillar 1: Analytical Lakehouse */}
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <div 
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '8px',
                backgroundColor: 'rgba(85, 37, 131, 0.3)',
                border: '1px solid var(--purple-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--purple-vibrant)',
                marginBottom: '1.25rem',
              }}
            >
              <Database size={20} />
            </div>
            <h3 className="font-subheading" style={{ fontSize: '1.25rem', color: '#FFFFFF', marginBottom: '0.6rem' }}>
              PARQUET LAKEHOUSE & DUCKDB
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.55 }}>
              1.5M+ historical play-by-play and box-score events stored in columnar Parquet format, 
              queried with sub-50ms predicate pushdown streaming directly into the prediction runtime.
            </p>
          </div>

          {/* Pillar 2: Zero Temporal Leakage */}
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <div 
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '8px',
                backgroundColor: 'rgba(253, 185, 39, 0.15)',
                border: '1px solid var(--gold-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--gold-accent)',
                marginBottom: '1.25rem',
              }}
            >
              <ShieldCheck size={20} />
            </div>
            <h3 className="font-subheading" style={{ fontSize: '1.25rem', color: '#FFFFFF', marginBottom: '0.6rem' }}>
              ZERO TEMPORAL LEAKAGE
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.55 }}>
              Strict pregame cutoffs ensure zero future game logs, in-game stats, or future trade events 
              can contaminate feature generation vectors. Verified by automated CI boundary tests.
            </p>
          </div>

          {/* Pillar 3: Role-Stratified Regressors */}
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <div 
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '8px',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--status-success)',
                marginBottom: '1.25rem',
              }}
            >
              <Cpu size={20} />
            </div>
            <h3 className="font-subheading" style={{ fontSize: '1.25rem', color: '#FFFFFF', marginBottom: '0.6rem' }}>
              ROLE-STRATIFIED INFERENCE
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.55 }}>
              Dedicated models dynamically route players across primary ball-handlers, wings, and interior anchors, 
              optimizing minutes, points, rebounds, and assists with role-tailored regularization.
            </p>
          </div>
        </div>

        {/* Feature Weights & Analytical Signal Breakdown */}
        <div className="glass-panel-elevated" style={{ padding: '2.5rem' }}>
          <div 
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--border-subtle)',
              paddingBottom: '1rem',
              marginBottom: '1.5rem',
              flexWrap: 'wrap',
              gap: '0.5rem',
            }}
          >
            <span className="broadcast-label">MODEL FEATURE VECTOR RELEVANCE & CONTRACT WEIGHTS</span>
            <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--gold-accent)' }}>
              24 CANONICAL PREGAME FEATURES
            </span>
          </div>

          <div 
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.5rem',
            }}
          >
            {featureWeights.map((f, idx) => (
              <div 
                key={idx}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                  padding: '1rem',
                  background: 'rgba(11, 6, 18, 0.5)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="font-subheading" style={{ fontSize: '0.85rem', color: '#FFFFFF', fontWeight: 600 }}>
                    {f.name}
                  </span>
                  <span className="font-mono" style={{ fontSize: '0.78rem', color: 'var(--gold-accent)', fontWeight: 700 }}>
                    {(f.weight * 100).toFixed(0)}%
                  </span>
                </div>

                <div 
                  style={{
                    width: '100%',
                    height: '5px',
                    borderRadius: '3px',
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    overflow: 'hidden',
                  }}
                >
                  <div 
                    style={{
                      width: `${f.weight * 100 * 3.5}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, var(--purple-primary), var(--gold-accent))',
                    }}
                  />
                </div>

                <span className="font-mono" style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                  contract: {f.key}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
