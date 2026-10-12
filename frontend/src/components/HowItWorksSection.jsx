import React, { useState } from 'react';

export default function HowItWorksSection() {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <section
      id="how-it-works"
      style={{
        backgroundColor: 'var(--surface-charcoal)',
        color: '#FFFFFF',
        padding: '90px 0',
        borderBottom: '1px solid var(--surface-charcoal-border)',
      }}
    >
      <div className="container">
        <div style={{ maxWidth: '820px', margin: '0 auto', textAlign: 'center' }}>
          <div className="section-eyebrow light">
            <span>●</span> METHODOLOGY
          </div>
          <h2 className="section-title light" style={{ marginBottom: '16px' }}>
            HOW IT WORKS
          </h2>
          <p
            style={{
              fontSize: '1.15rem',
              lineHeight: 1.7,
              color: '#E2DFE8',
              marginBottom: '32px',
            }}
          >
            Lakers in 5 combines historical NBA match data, rolling team form, and player usage statistics to estimate game outcomes before tip-off.
          </p>

          {/* 3 Core Analytical Pillars */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '24px',
              textAlign: 'left',
              marginBottom: '40px',
            }}
          >
            <div className="card-charcoal">
              <div className="font-display" style={{ fontSize: '1.1rem', color: 'var(--gold-accent)', marginBottom: '8px' }}>
                01 · PRE-GAME SIGNALS
              </div>
              <p style={{ fontSize: '0.9rem', color: '#A39DAE', lineHeight: 1.5 }}>
                Strict pre-game data boundaries. Only information available before the opening jump is used for predictions.
              </p>
            </div>

            <div className="card-charcoal">
              <div className="font-display" style={{ fontSize: '1.1rem', color: 'var(--gold-accent)', marginBottom: '8px' }}>
                02 · ROLLING PERFORMANCE
              </div>
              <p style={{ fontSize: '0.9rem', color: '#A39DAE', lineHeight: 1.5 }}>
                Weights recent 10-game offensive and defensive trends alongside rest schedules and home-court splits.
              </p>
            </div>

            <div className="card-charcoal">
              <div className="font-display" style={{ fontSize: '1.1rem', color: 'var(--gold-accent)', marginBottom: '8px' }}>
                03 · ROTATION RESOLUTION
              </div>
              <p style={{ fontSize: '0.9rem', color: '#A39DAE', lineHeight: 1.5 }}>
                Individual performance models project expected minutes, scoring, and playmaking across active rotations.
              </p>
            </div>
          </div>

          {/* Progressive Disclosure Toggle */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="btn-secondary"
            style={{
              padding: '10px 22px',
              fontSize: '0.9rem',
            }}
          >
            {showDetails ? 'HIDE TECHNICAL DETAILS ↑' : 'SEE HOW THE MODEL WORKS →'}
          </button>

          {/* Expandable Technical Depth */}
          {showDetails && (
            <div
              className="animate-fade-in"
              style={{
                marginTop: '40px',
                textAlign: 'left',
                backgroundColor: 'var(--surface-charcoal-card)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--surface-charcoal-border)',
                padding: '32px',
              }}
            >
              <h4 className="font-display" style={{ fontSize: '1.25rem', color: 'var(--gold-accent)', marginBottom: '16px' }}>
                ENGINEERING & MODEL ARCHITECTURE
              </h4>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', fontSize: '0.9rem', color: '#CBD5E1', lineHeight: 1.6 }}>
                <div>
                  <strong style={{ color: '#FFFFFF', display: 'block', marginBottom: '4px' }}>Chronological Validation</strong>
                  Models are trained on strictly past seasons and validated sequentially to ensure zero future-data leakage into pregame features.
                </div>
                <div>
                  <strong style={{ color: '#FFFFFF', display: 'block', marginBottom: '4px' }}>Feature Formulation</strong>
                  24 canonical pregame features capture team Elo ratings, net rating differentials, rest day disparity, and pace metrics.
                </div>
                <div>
                  <strong style={{ color: '#FFFFFF', display: 'block', marginBottom: '4px' }}>Model Suite</strong>
                  Calibrated logistic classification for win probabilities paired with ridge regression estimators for point margins and box scores.
                </div>
                <div>
                  <strong style={{ color: '#FFFFFF', display: 'block', marginBottom: '4px' }}>Roster & Transaction Sync</strong>
                  Dynamic transaction resolution tracks offseason player movements to construct accurate eligible rotation universes per game date.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
