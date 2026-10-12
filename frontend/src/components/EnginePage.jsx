import React from 'react';

/**
 * EnginePage — Dedicated Technical Architecture & MLOps Showcase
 * Visual Identity: Warm Editorial × Lakers Showtime Accents
 * Palette:
 *   - Warm Ivory: #F4F0E7
 *   - White: #FFFFFF
 *   - Ink: #211E19
 *   - Warm Gray: #746C60
 *   - Light Border: #D8D0C2
 *   - Lakers Purple: #552583
 *   - Lakers Gold: #FDB927
 *   - Pale Lavender: #E8E4F1
 *   - Pale Gold: #F7EAC6
 *   - Muted Olive: #6E7650
 *   - Muted Terracotta: #A35C32
 */
export default function EnginePage({ onNavigate }) {
  const handleReturnHome = (e, sectionId = 'hero') => {
    e.preventDefault();
    if (onNavigate) {
      onNavigate('/', sectionId);
    } else {
      window.history.pushState({}, '', '/');
      window.dispatchEvent(new PopStateEvent('popstate'));
      if (sectionId) {
        setTimeout(() => {
          const el = document.getElementById(sectionId);
          if (el) el.scrollIntoView({ behavior: 'smooth' });
        }, 50);
      }
    }
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--editorial-bg, #F4F0E7)',
        color: 'var(--editorial-ink, #211E19)',
        minHeight: '100vh',
        fontFamily: 'var(--font-body)',
        paddingTop: '76px', // space for fixed header
      }}
    >
      {/* =========================================================================
          0. TOP EDITORIAL BREADCRUMB & LAKERS STRIPE
          ========================================================================= */}
      <div
        style={{
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-card, #FFFFFF)',
          position: 'relative',
        }}
      >
        {/* Subtle Lakers brand indicator line */}
        <div
          style={{
            height: '3px',
            background: 'linear-gradient(90deg, #552583 0%, #552583 60%, #FDB927 60%, #FDB927 100%)',
          }}
        />
        <div
          className="container"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 24px',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <a
            href="/"
            onClick={(e) => handleReturnHome(e, 'next-game')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              textDecoration: 'none',
              color: 'var(--editorial-purple, #552583)',
              fontSize: '0.86rem',
              fontWeight: 700,
              fontFamily: 'var(--font-display)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              transition: 'color 150ms ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--editorial-terracotta, #A35C32)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--editorial-purple, #552583)')}
          >
            <span>←</span> Back to Game Projections
          </a>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: 'var(--editorial-purple, #552583)',
                backgroundColor: 'var(--editorial-lavender, #E8E4F1)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-xs)',
                letterSpacing: '0.08em',
                fontFamily: 'var(--font-display)',
                textTransform: 'uppercase',
                border: '1px solid rgba(85, 37, 131, 0.15)',
              }}
            >
              LAKERS IN 5 · ENGINEERING DOSSIER
            </span>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: 'var(--editorial-olive, #6E7650)',
                backgroundColor: 'var(--editorial-sand, #E9E2D5)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-xs)',
                letterSpacing: '0.08em',
                fontFamily: 'var(--font-display)',
                textTransform: 'uppercase',
              }}
            >
              RECRUITER REVIEW SPEC · 2026
            </span>
          </div>
        </div>
      </div>

      {/* =========================================================================
          1. HERO & BASKETBALL COURT MOTIF (Warm Ivory)
          ========================================================================= */}
      <section
        style={{
          padding: '80px 0 70px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-bg, #F4F0E7)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div className="container" style={{ position: 'relative', zIndex: 1 }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1.8fr) minmax(240px, 1fr)',
              gap: '48px',
              alignItems: 'center',
            }}
            className="engine-hero-grid"
          >
            {/* Left: Headline & Narrative */}
            <div>
              {/* Eyebrow */}
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontFamily: 'var(--font-display)',
                  fontSize: '0.88rem',
                  fontWeight: 700,
                  letterSpacing: '0.14em',
                  textTransform: 'uppercase',
                  color: 'var(--editorial-purple, #552583)',
                  marginBottom: '16px',
                }}
              >
                <span style={{ color: 'var(--editorial-gold, #FDB927)', fontSize: '1.1rem' }}>●</span>
                THE ENGINEERING BEHIND THE GAME
              </div>

              {/* Headline */}
              <h1
                className="font-display"
                style={{
                  fontSize: 'clamp(2.5rem, 5.2vw, 4.2rem)',
                  fontWeight: 800,
                  letterSpacing: '0.02em',
                  lineHeight: 1.05,
                  color: 'var(--editorial-ink, #211E19)',
                  textTransform: 'uppercase',
                  marginBottom: '24px',
                }}
              >
                Good predictions don't happen by accident.
              </h1>

              {/* Supporting paragraph */}
              <p
                style={{
                  fontSize: 'clamp(1.1rem, 1.8vw, 1.3rem)',
                  color: 'var(--editorial-gray, #746C60)',
                  lineHeight: 1.6,
                  maxWidth: '780px',
                  marginBottom: '32px',
                }}
              >
                Lakers in 5 combines historical NBA data, pregame feature engineering, chronological model evaluation and production inference in one end-to-end system.
              </p>

              {/* Understated Category Badges */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '10px',
                  alignItems: 'center',
                }}
              >
                <span
                  style={{
                    backgroundColor: 'var(--editorial-card, #FFFFFF)',
                    border: '1px solid var(--editorial-border, #D8D0C2)',
                    borderLeft: '4px solid var(--editorial-gold, #FDB927)',
                    color: 'var(--editorial-ink, #211E19)',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    fontFamily: 'var(--font-display)',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-xs)',
                    textTransform: 'uppercase',
                  }}
                >
                  MACHINE LEARNING
                </span>
                <span
                  style={{
                    backgroundColor: 'var(--editorial-card, #FFFFFF)',
                    border: '1px solid var(--editorial-border, #D8D0C2)',
                    borderLeft: '4px solid var(--editorial-purple, #552583)',
                    color: 'var(--editorial-ink, #211E19)',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    fontFamily: 'var(--font-display)',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-xs)',
                    textTransform: 'uppercase',
                  }}
                >
                  TEMPORAL VALIDATION
                </span>
                <span
                  style={{
                    backgroundColor: 'var(--editorial-card, #FFFFFF)',
                    border: '1px solid var(--editorial-border, #D8D0C2)',
                    borderLeft: '4px solid var(--editorial-olive, #6E7650)',
                    color: 'var(--editorial-ink, #211E19)',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    fontFamily: 'var(--font-display)',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-xs)',
                    textTransform: 'uppercase',
                  }}
                >
                  PRODUCTION MLOPS
                </span>
              </div>
            </div>

            {/* Right: Half-Court Geometry Schematic */}
            <div
              style={{
                backgroundColor: 'var(--editorial-card, #FFFFFF)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderRadius: 'var(--radius-sm)',
                padding: '24px',
                boxShadow: 'var(--shadow-sm)',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '14px',
                  borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
                  paddingBottom: '8px',
                }}
              >
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    fontFamily: 'var(--font-mono)',
                    letterSpacing: '0.08em',
                    color: 'var(--editorial-purple, #552583)',
                  }}
                >
                  HALFCOUT TELEMETRY // 94×50 FT
                </span>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    color: 'var(--editorial-gold, #FDB927)',
                    backgroundColor: 'rgba(253, 185, 39, 0.15)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                  }}
                >
                  PREGAME GEOMETRY
                </span>
              </div>

              {/* Bespoke Half-Court SVG Illustration */}
              <svg
                viewBox="0 0 280 220"
                style={{
                  width: '100%',
                  height: 'auto',
                  display: 'block',
                }}
              >
                {/* Court Boundary */}
                <rect x="10" y="10" width="260" height="200" fill="#FAF7F2" stroke="#D8D0C2" strokeWidth="2" />
                
                {/* Half court line & center circle */}
                <line x1="10" y1="200" x2="270" y2="200" stroke="#746C60" strokeWidth="2" />
                <path d="M 110 200 A 30 30 0 0 1 170 200" fill="none" stroke="#552583" strokeWidth="2" strokeDasharray="3 3" />
                <circle cx="140" cy="200" r="10" fill="none" stroke="#FDB927" strokeWidth="2" />

                {/* Key / Paint area */}
                <rect x="100" y="10" width="80" height="100" fill="rgba(85, 37, 131, 0.04)" stroke="#552583" strokeWidth="1.5" />
                
                {/* Free throw circle */}
                <circle cx="140" cy="110" r="30" fill="none" stroke="#552583" strokeWidth="1.5" />
                <path d="M 110 110 A 30 30 0 0 0 170 110" fill="none" stroke="#D8D0C2" strokeWidth="1.5" strokeDasharray="4 4" />

                {/* 3-Point Arc */}
                <path
                  d="M 28 10 L 28 50 A 112 112 0 0 0 252 50 L 252 10"
                  fill="none"
                  stroke="#746C60"
                  strokeWidth="2"
                />

                {/* Restricted Area Arc & Basket */}
                <path d="M 125 10 A 15 15 0 0 0 155 10" fill="none" stroke="#FDB927" strokeWidth="1.5" />
                <line x1="128" y1="18" x2="152" y2="18" stroke="#211E19" strokeWidth="2" />
                <circle cx="140" cy="22" r="4.5" fill="#FDB927" stroke="#211E19" strokeWidth="1" />

                {/* Schematic Coordinates Callout */}
                <circle cx="140" cy="110" r="3" fill="#552583" />
                <text x="148" y="114" fontSize="8" fill="#552583" fontFamily="monospace" fontWeight="bold">ORtg=115.4</text>
                <circle cx="70" cy="70" r="3" fill="#FDB927" />
                <text x="76" y="74" fontSize="8" fill="#746C60" fontFamily="monospace">3PT_RATE</text>
                <circle cx="210" cy="70" r="3" fill="#6E7650" />
                <text x="180" y="86" fontSize="8" fill="#6E7650" fontFamily="monospace">DEF_EFF</text>
              </svg>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '12px',
                  fontSize: '0.74rem',
                  color: 'var(--editorial-gray, #746C60)',
                }}
              >
                <span>Spatial &amp; Possession Context</span>
                <span style={{ fontWeight: 700, color: 'var(--editorial-ink, #211E19)' }}>STRICT PRE-TIPOFF</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          2. THE MODEL STACK (White Surface with Lakers Brand Accents)
          ========================================================================= */}
      <section
        id="model-stack"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-card, #FFFFFF)',
        }}
      >
        <div className="container">
          <div style={{ maxWidth: '820px', marginBottom: '44px' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                color: 'var(--editorial-purple, #552583)',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--editorial-purple, #552583)' }} />
              01 · INFERENCE ARCHITECTURE
            </div>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
              }}
            >
              THE MODEL STACK
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6 }}>
              Production inferences are generated using specialized, task-tailored estimators rather than an opaque black box.
            </p>
          </div>

          {/* Model Stack Editorial Grid (Asymmetric & Accented) */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              gap: '24px',
            }}
          >
            {/* Game Outcome — Lakers Gold Highlight */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderTop: '5px solid var(--editorial-gold, #FDB927)',
                padding: '28px 22px',
                borderRadius: 'var(--radius-xs)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span
                    style={{
                      fontSize: '0.74rem',
                      fontWeight: 800,
                      color: 'var(--editorial-ink, #211E19)',
                      letterSpacing: '0.12em',
                      fontFamily: 'var(--font-display)',
                      textTransform: 'uppercase',
                    }}
                  >
                    GAME OUTCOME
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: '#6F4E00',
                      backgroundColor: 'var(--editorial-pale-gold, #F7EAC6)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    PRIMARY PREDICTION
                  </span>
                </div>
                <h3
                  className="font-display"
                  style={{ fontSize: '1.6rem', color: 'var(--editorial-ink, #211E19)', marginBottom: '8px' }}
                >
                  Logistic Regression
                </h3>
                <p style={{ fontSize: '0.92rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.55, marginBottom: '16px' }}>
                  Calibrated probabilistic classifier estimating home vs. away win probabilities from 24 pregame features.
                </p>
              </div>
              <div
                style={{
                  borderTop: '1px solid var(--editorial-border, #D8D0C2)',
                  paddingTop: '12px',
                  fontSize: '0.78rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--editorial-ink, #211E19)',
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span>TARGET: WIN / LOSS</span>
                <span style={{ color: 'var(--editorial-purple, #552583)', fontWeight: 'bold' }}>P(Win) ∈ [0, 1]</span>
              </div>
            </div>

            {/* Game Margin — Olive Accent */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderTop: '5px solid var(--editorial-olive, #6E7650)',
                padding: '28px 22px',
                borderRadius: 'var(--radius-xs)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span
                    style={{
                      fontSize: '0.74rem',
                      fontWeight: 800,
                      color: 'var(--editorial-olive, #6E7650)',
                      letterSpacing: '0.12em',
                      fontFamily: 'var(--font-display)',
                      textTransform: 'uppercase',
                    }}
                  >
                    GAME MARGIN
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: 'var(--editorial-olive, #6E7650)',
                      backgroundColor: 'rgba(110, 118, 80, 0.12)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    POINT SPREAD
                  </span>
                </div>
                <h3
                  className="font-display"
                  style={{ fontSize: '1.6rem', color: 'var(--editorial-ink, #211E19)', marginBottom: '8px' }}
                >
                  Ridge Regression
                </h3>
                <p style={{ fontSize: '0.92rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.55, marginBottom: '16px' }}>
                  L2-regularized linear regressor predicting the final score differential before tipoff.
                </p>
              </div>
              <div
                style={{
                  borderTop: '1px solid var(--editorial-border, #D8D0C2)',
                  paddingTop: '12px',
                  fontSize: '0.78rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--editorial-ink, #211E19)',
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span>TARGET: SCORE MARGIN</span>
                <span style={{ color: 'var(--editorial-olive, #6E7650)', fontWeight: 'bold' }}>SPREAD (PTS)</span>
              </div>
            </div>

            {/* Player Projections — Lakers Purple Highlight */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderTop: '5px solid var(--editorial-purple, #552583)',
                padding: '28px 22px',
                borderRadius: 'var(--radius-xs)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span
                    style={{
                      fontSize: '0.74rem',
                      fontWeight: 800,
                      color: 'var(--editorial-purple, #552583)',
                      letterSpacing: '0.12em',
                      fontFamily: 'var(--font-display)',
                      textTransform: 'uppercase',
                    }}
                  >
                    PLAYER PROJECTIONS
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: 'var(--editorial-purple, #552583)',
                      backgroundColor: 'var(--editorial-lavender, #E8E4F1)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    ROLE-STRATIFIED
                  </span>
                </div>
                <h3
                  className="font-display"
                  style={{ fontSize: '1.6rem', color: 'var(--editorial-ink, #211E19)', marginBottom: '8px' }}
                >
                  Role-Stratified Ridge
                </h3>
                <p style={{ fontSize: '0.92rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.55, marginBottom: '16px' }}>
                  Stratified estimators predicting Minutes, Points, Rebounds, and Assists across active rotations. (Note: Production models do not predict blocks).
                </p>
              </div>
              <div
                style={{
                  borderTop: '1px solid var(--editorial-border, #D8D0C2)',
                  paddingTop: '12px',
                  fontSize: '0.78rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--editorial-ink, #211E19)',
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span>TARGETS: MIN · PTS · REB · AST</span>
                <span style={{ color: 'var(--editorial-purple, #552583)', fontWeight: 'bold' }}>4 TARGETS</span>
              </div>
            </div>

            {/* Validation Strategy — Terracotta Accent */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderTop: '5px solid var(--editorial-terracotta, #A35C32)',
                padding: '28px 22px',
                borderRadius: 'var(--radius-xs)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span
                    style={{
                      fontSize: '0.74rem',
                      fontWeight: 800,
                      color: 'var(--editorial-terracotta, #A35C32)',
                      letterSpacing: '0.12em',
                      fontFamily: 'var(--font-display)',
                      textTransform: 'uppercase',
                    }}
                  >
                    VALIDATION
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: 'var(--editorial-terracotta, #A35C32)',
                      backgroundColor: 'rgba(163, 92, 50, 0.12)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    TEMPORAL INTEGRITY
                  </span>
                </div>
                <h3
                  className="font-display"
                  style={{ fontSize: '1.6rem', color: 'var(--editorial-ink, #211E19)', marginBottom: '8px' }}
                >
                  Walk-Forward Cross-Validation
                </h3>
                <p style={{ fontSize: '0.92rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.55, marginBottom: '16px' }}>
                  Chronologically ordered expanding-window evaluation guaranteeing that test observations never leak into model training.
                </p>
              </div>
              <div
                style={{
                  borderTop: '1px solid var(--editorial-border, #D8D0C2)',
                  paddingTop: '12px',
                  fontSize: '0.78rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--editorial-ink, #211E19)',
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span>SPLITS: 2018–2025</span>
                <span style={{ color: 'var(--editorial-terracotta, #A35C32)', fontWeight: 'bold' }}>ZERO LEAKAGE</span>
              </div>
            </div>
          </div>

          {/* Model Distinction Note (Warm Lavender Callout) */}
          <div
            style={{
              marginTop: '44px',
              padding: '18px 24px',
              backgroundColor: 'var(--editorial-lavender, #E8E4F1)',
              borderRadius: 'var(--radius-xs)',
              borderLeft: '4px solid var(--editorial-purple, #552583)',
              fontSize: '0.92rem',
              color: 'var(--editorial-ink, #211E19)',
              lineHeight: 1.55,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div>
              <strong style={{ color: 'var(--editorial-purple, #552583)' }}>Production vs. Shadow Distinction:</strong> Production predictions serve champion Logistic and Ridge models exclusively. The experimental C1 shadow suite runs asynchronously for offline paired comparison and does not alter live projections.
            </div>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.76rem',
                backgroundColor: 'rgba(85, 37, 131, 0.1)',
                padding: '4px 10px',
                borderRadius: '4px',
                fontWeight: 700,
                color: 'var(--editorial-purple, #552583)',
              }}
            >
              DEPLOYMENT: CHAMPION_ONLY
            </span>
          </div>
        </div>
      </section>

      {/* =========================================================================
          3. END-TO-END DATA PIPELINE (Pale Lavender / White Grouped Flow)
          ========================================================================= */}
      <section
        id="data-pipeline"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-lavender, #E8E4F1)',
        }}
      >
        <div className="container">
          <div style={{ maxWidth: '820px', marginBottom: '40px' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                color: 'var(--editorial-purple, #552583)',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--editorial-gold, #FDB927)' }} />
              02 · DATA MOVEMENT &amp; TRANSFORMATION
            </div>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
              }}
            >
              END-TO-END DATA PIPELINE
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6 }}>
              A deterministic transformation flow grouped into three core architectural boundaries: Historical Data Ingestion, Analytical Modeling, and Real-Time Serving.
            </p>
          </div>

          {/* Grouped Data Pipeline Architecture Flow */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '24px',
            }}
          >
            {/* DOMAIN 1: DATA INGESTION & QUALITY */}
            <div
              style={{
                backgroundColor: 'var(--editorial-card, #FFFFFF)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderRadius: 'var(--radius-sm)',
                padding: '24px',
                boxShadow: 'var(--shadow-sm)',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingBottom: '12px',
                  marginBottom: '16px',
                  borderBottom: '2px solid var(--editorial-purple, #552583)',
                }}
              >
                <span className="font-display" style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--editorial-purple, #552583)' }}>
                  PHASE 1: DATA INGESTION
                </span>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--editorial-gray, #746C60)' }}>
                  OFFLINE / BATCH
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {[
                  {
                    num: '01',
                    title: 'NBA HISTORICAL DATA',
                    desc: 'Raw game logs, box scores, schedules, and roster history via nba_api.',
                  },
                  {
                    num: '02',
                    title: 'DATA VALIDATION',
                    desc: 'Schema verification, null-rate bounds, and range checks via Pydantic.',
                  },
                  {
                    num: '03',
                    title: 'FEATURE ENGINEERING',
                    desc: 'Deterministic feature extraction enforcing strict temporal cutoffs.',
                  },
                ].map((item, idx, arr) => (
                  <div
                    key={item.num}
                    style={{
                      backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--editorial-border, #D8D0C2)',
                      position: 'relative',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--editorial-purple, #552583)', fontFamily: 'var(--font-mono)' }}>
                        [{item.num}]
                      </span>
                      <strong className="font-display" style={{ fontSize: '0.95rem', color: 'var(--editorial-ink, #211E19)' }}>
                        {item.title}
                      </strong>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--editorial-gray, #746C60)', margin: 0, lineHeight: 1.4 }}>
                      {item.desc}
                    </p>
                    {idx < arr.length - 1 && (
                      <div style={{ textAlign: 'center', margin: '4px 0 -8px 0', color: 'var(--editorial-purple, #552583)', fontSize: '0.9rem', fontWeight: 'bold' }}>
                        ↓
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* DOMAIN 2: MODELING & INFERENCE */}
            <div
              style={{
                backgroundColor: 'var(--editorial-card, #FFFFFF)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderRadius: 'var(--radius-sm)',
                padding: '24px',
                boxShadow: 'var(--shadow-sm)',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingBottom: '12px',
                  marginBottom: '16px',
                  borderBottom: '2px solid var(--editorial-gold, #FDB927)',
                }}
              >
                <span className="font-display" style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)' }}>
                  PHASE 2: ANALYTICAL MODELING
                </span>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--editorial-gray, #746C60)' }}>
                  CALCULATED FORM
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {[
                  {
                    num: '04',
                    title: 'ROLLING STATISTICS',
                    desc: '10-game & 20-game expanding window metrics for team pace and offensive rating.',
                  },
                  {
                    num: '05',
                    title: 'TEAM STRENGTH / ELO',
                    desc: 'Opponent quality adjustments, rest differential, and schedule density.',
                  },
                  {
                    num: '06',
                    title: 'GAME PREDICTION',
                    desc: 'Logistic Regression calibrated win probabilities & Ridge point spreads.',
                  },
                  {
                    num: '07',
                    title: 'PLAYER PROJECTION',
                    desc: 'Role-stratified Ridge regressors for minutes, points, rebounds, and assists.',
                  },
                ].map((item, idx, arr) => (
                  <div
                    key={item.num}
                    style={{
                      backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--editorial-border, #D8D0C2)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '0.74rem', fontWeight: 800, color: '#976800', fontFamily: 'var(--font-mono)' }}>
                        [{item.num}]
                      </span>
                      <strong className="font-display" style={{ fontSize: '0.95rem', color: 'var(--editorial-ink, #211E19)' }}>
                        {item.title}
                      </strong>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--editorial-gray, #746C60)', margin: 0, lineHeight: 1.4 }}>
                      {item.desc}
                    </p>
                    {idx < arr.length - 1 && (
                      <div style={{ textAlign: 'center', margin: '4px 0 -8px 0', color: 'var(--editorial-gold, #FDB927)', fontSize: '0.9rem', fontWeight: 'bold' }}>
                        ↓
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* DOMAIN 3: REAL-TIME SERVING */}
            <div
              style={{
                backgroundColor: 'var(--editorial-card, #FFFFFF)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderRadius: 'var(--radius-sm)',
                padding: '24px',
                boxShadow: 'var(--shadow-sm)',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingBottom: '12px',
                  marginBottom: '16px',
                  borderBottom: '2px solid var(--editorial-olive, #6E7650)',
                }}
              >
                <span className="font-display" style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--editorial-olive, #6E7650)' }}>
                  PHASE 3: CLIENT DELIVERY
                </span>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--editorial-gray, #746C60)' }}>
                  ONLINE / LIVE
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {[
                  {
                    num: '08',
                    title: 'FASTAPI ENGINE',
                    desc: 'Pre-warmed model inference in memory with correlation ID tracking and Pydantic validation.',
                  },
                  {
                    num: '09',
                    title: 'WEB APPLICATION',
                    desc: 'Interactive schedule selector, live win probability cards, and projected starting lineups.',
                  },
                ].map((item, idx, arr) => (
                  <div
                    key={item.num}
                    style={{
                      backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--editorial-border, #D8D0C2)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--editorial-olive, #6E7650)', fontFamily: 'var(--font-mono)' }}>
                        [{item.num}]
                      </span>
                      <strong className="font-display" style={{ fontSize: '0.95rem', color: 'var(--editorial-ink, #211E19)' }}>
                        {item.title}
                      </strong>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--editorial-gray, #746C60)', margin: 0, lineHeight: 1.4 }}>
                      {item.desc}
                    </p>
                    {idx < arr.length - 1 && (
                      <div style={{ textAlign: 'center', margin: '4px 0 -8px 0', color: 'var(--editorial-olive, #6E7650)', fontSize: '0.9rem', fontWeight: 'bold' }}>
                        ↓
                      </div>
                    )}
                  </div>
                ))}

                {/* Performance SLA Card */}
                <div
                  style={{
                    marginTop: '8px',
                    padding: '14px',
                    backgroundColor: 'var(--editorial-sand, #E9E2D5)',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px dashed var(--editorial-border, #D8D0C2)',
                  }}
                >
                  <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--editorial-ink, #211E19)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    PRODUCTION INFERENCE SLA
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.4 }}>
                    End-to-end request latency target is &lt;45ms p95 on warm container execution.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          4. PREGAME FEATURES & LEAKAGE PREVENTION (Built Before Tipoff)
          ========================================================================= */}
      <section
        id="pregame-features"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-card, #FFFFFF)',
        }}
      >
        <div className="container">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1.1fr) minmax(0, 1fr)',
              gap: '48px',
              alignItems: 'start',
            }}
            className="engine-split-grid"
          >
            {/* Left: Narrative & Verified Features */}
            <div>
              <div
                style={{
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  letterSpacing: '0.12em',
                  fontFamily: 'var(--font-display)',
                  color: 'var(--editorial-terracotta, #A35C32)',
                  textTransform: 'uppercase',
                  marginBottom: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--editorial-terracotta, #A35C32)' }} />
                03 · FEATURE INTEGRITY
              </div>
              <h2
                className="font-display"
                style={{
                  fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                  color: 'var(--editorial-ink, #211E19)',
                  marginBottom: '16px',
                }}
              >
                BUILT BEFORE TIPOFF
              </h2>
              <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6, marginBottom: '24px' }}>
                A sports prediction model is only valid if every single feature is strictly known before the opening jump ball. Our pipeline enforces strict historical cutoff timestamps prior to tipoff (t &lt; tipoff).
              </p>

              {/* Verified Feature Categories Grid */}
              <div style={{ marginBottom: '28px' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', marginBottom: '12px', textTransform: 'uppercase' }}>
                  Verified Pregame Features:
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
                  {[
                    'Rolling Form (10 & 20-game)',
                    'Team Strength & Efficiency',
                    'Player Usage & Pace',
                    'Expected Minutes Baseline',
                    'Offensive / Defensive Rating',
                    'Elo Rating Differential',
                    'Rest Day Disparity',
                    'Home / Road Venue Splits'
                  ].map((feat) => (
                    <div
                      key={feat}
                      style={{
                        padding: '8px 12px',
                        backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                        border: '1px solid var(--editorial-border, #D8D0C2)',
                        borderLeft: '3px solid var(--editorial-purple, #552583)',
                        color: 'var(--editorial-ink, #211E19)',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        borderRadius: 'var(--radius-xs)',
                      }}
                    >
                      ✓ {feat}
                    </div>
                  ))}
                </div>
              </div>

              <div
                style={{
                  padding: '14px 18px',
                  backgroundColor: 'var(--editorial-sand, #E9E2D5)',
                  borderRadius: 'var(--radius-xs)',
                  borderLeft: '4px solid var(--editorial-terracotta, #A35C32)',
                  fontSize: '0.86rem',
                  color: 'var(--editorial-ink, #211E19)',
                  lineHeight: 1.5,
                }}
              >
                Automated regression leakage tests in <code>tests/test_features.py</code> assert that target scores, actual game minutes, and postgame box scores are strictly omitted during pregame feature vector synthesis.
              </div>
            </div>

            {/* Right: Chronological Feature Timeline Diagram */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderRadius: 'var(--radius-sm)',
                padding: '32px 28px',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--editorial-purple, #552583)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
                  TEMPORAL FEATURE TIMELINE
                </div>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    color: 'var(--editorial-purple, #552583)',
                    backgroundColor: 'var(--editorial-lavender, #E8E4F1)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                  }}
                >
                  STRICT CAUSALITY
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative' }}>
                {/* Step 1: Historical Cutoff */}
                <div
                  style={{
                    backgroundColor: 'var(--editorial-card, #FFFFFF)',
                    padding: '16px 20px',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--editorial-border, #D8D0C2)',
                    borderLeft: '5px solid var(--editorial-purple, #552583)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--editorial-purple, #552583)' }}>
                      STEP 1 · HISTORICAL CUTOFF
                    </span>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--editorial-gray, #746C60)' }}>
                      t &lt; 0
                    </span>
                  </div>
                  <div className="font-display" style={{ fontSize: '1.2rem', color: 'var(--editorial-ink, #211E19)', margin: '4px 0' }}>
                    PREVIOUS GAMES
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--editorial-gray, #746C60)' }}>
                    Historical game logs strictly prior to match date. Zero lookahead into future matchups.
                  </div>
                </div>

                <div style={{ textAlign: 'center', color: 'var(--editorial-purple, #552583)', fontWeight: 800, fontSize: '1.2rem' }}>
                  ↓
                </div>

                {/* Step 2: Lagged Features */}
                <div
                  style={{
                    backgroundColor: 'var(--editorial-card, #FFFFFF)',
                    padding: '16px 20px',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--editorial-border, #D8D0C2)',
                    borderLeft: '5px solid var(--editorial-purple, #552583)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--editorial-purple, #552583)' }}>
                      STEP 2 · FEATURE SYNTHESIS
                    </span>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--editorial-gray, #746C60)' }}>
                      t = -2h
                    </span>
                  </div>
                  <div className="font-display" style={{ fontSize: '1.2rem', color: 'var(--editorial-ink, #211E19)', margin: '4px 0' }}>
                    LAGGED FEATURES
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--editorial-gray, #746C60)' }}>
                    Rolling averages, pace calculations, rest disparities, and opponent defensive ratings.
                  </div>
                </div>

                <div style={{ textAlign: 'center', color: 'var(--editorial-purple, #552583)', fontWeight: 800, fontSize: '1.2rem' }}>
                  ↓
                </div>

                {/* Step 3: Pre-Game Inference */}
                <div
                  style={{
                    backgroundColor: 'var(--editorial-card, #FFFFFF)',
                    padding: '16px 20px',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--editorial-border, #D8D0C2)',
                    borderLeft: '5px solid var(--editorial-purple, #552583)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--editorial-purple, #552583)' }}>
                      STEP 3 · MODEL INFERENCE
                    </span>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--editorial-gray, #746C60)' }}>
                      t = -30m
                    </span>
                  </div>
                  <div className="font-display" style={{ fontSize: '1.2rem', color: 'var(--editorial-ink, #211E19)', margin: '4px 0' }}>
                    PRE-GAME INFERENCE
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--editorial-gray, #746C60)' }}>
                    Champion estimators evaluate feature vectors for win probabilities and player totals.
                  </div>
                </div>

                {/* TARGET GAME TIPOFF BOUNDARY — LAKERS GOLD MARKER */}
                <div
                  style={{
                    backgroundColor: 'var(--editorial-pale-gold, #F7EAC6)',
                    border: '2px dashed var(--editorial-gold, #FDB927)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '12px 18px',
                    textAlign: 'center',
                    margin: '4px 0',
                  }}
                >
                  <div style={{ fontSize: '0.74rem', fontWeight: 800, color: '#7E5B00', letterSpacing: '0.1em' }}>
                    ⚡ TARGET GAME TIPOFF BOUNDARY (t = 0)
                  </div>
                  <div style={{ fontSize: '0.74rem', color: '#684D00' }}>
                    Feature synthesis strictly seals here. No post-tipoff data is ever accessible.
                  </div>
                </div>

                {/* Step 4: Postgame Evaluation */}
                <div
                  style={{
                    backgroundColor: 'var(--editorial-card, #FFFFFF)',
                    padding: '16px 20px',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--editorial-border, #D8D0C2)',
                    borderLeft: '5px solid var(--editorial-terracotta, #A35C32)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--editorial-terracotta, #A35C32)' }}>
                      STEP 4 · AUDIT &amp; TELEMETRY
                    </span>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--editorial-gray, #746C60)' }}>
                      t &gt; final
                    </span>
                  </div>
                  <div className="font-display" style={{ fontSize: '1.2rem', color: 'var(--editorial-ink, #211E19)', margin: '4px 0' }}>
                    POSTGAME EVALUATION
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--editorial-gray, #746C60)' }}>
                    Actual final scores recorded postgame for Brier score audit, Wilcoxon tests, and drift tracking.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          5. CHRONOLOGICAL VALIDATION (Pale Gold / Warm Neutral Surface)
          ========================================================================= */}
      <section
        id="chronological-validation"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-pale-gold, #F7EAC6)',
        }}
      >
        <div className="container">
          <div style={{ maxWidth: '820px', marginBottom: '40px' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                color: '#7E5B00',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#7E5B00' }} />
              04 · TEMPORAL VALIDATION RIGOR
            </div>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
              }}
            >
              CHRONOLOGICAL VALIDATION
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6 }}>
              Standard k-fold cross validation randomly shuffles games, destroying temporal causality. We implement strict expanding-window walk-forward splits.
            </p>
          </div>

          {/* Validation Timeline Table with Distinct Patterned Bands */}
          <div
            style={{
              backgroundColor: 'var(--editorial-card, #FFFFFF)',
              border: '1px solid var(--editorial-border, #D8D0C2)',
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            {/* Visual Timeline Bars Header */}
            <div
              style={{
                padding: '20px 24px',
                borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
              }}
            >
              <div style={{ fontSize: '0.76rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', marginBottom: '12px', textTransform: 'uppercase' }}>
                EXPANDING-WINDOW TIMELINE BANDS:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {/* Fold 1 Bar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.78rem' }}>
                  <span style={{ width: '60px', fontWeight: 700, color: 'var(--editorial-ink, #211E19)' }}>Fold 1</span>
                  <div style={{ flex: 1, display: 'flex', height: '24px', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: '60%', backgroundColor: '#552583', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>
                      TRAIN: 2021–22
                    </div>
                    <div style={{ width: '40%', backgroundColor: '#FDB927', color: '#211E19', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>
                      VAL: 2023–24
                    </div>
                  </div>
                </div>

                {/* Fold 2 Bar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.78rem' }}>
                  <span style={{ width: '60px', fontWeight: 700, color: 'var(--editorial-ink, #211E19)' }}>Fold 2</span>
                  <div style={{ flex: 1, display: 'flex', height: '24px', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: '75%', backgroundColor: '#552583', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>
                      EXPANDED TRAIN: 2021–22 → 2023–24
                    </div>
                    <div style={{ width: '25%', backgroundColor: '#FDB927', color: '#211E19', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>
                      VAL: 2024–25
                    </div>
                  </div>
                </div>

                {/* Benchmark Bar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.78rem' }}>
                  <span style={{ width: '60px', fontWeight: 700, color: 'var(--editorial-ink, #211E19)' }}>Compare</span>
                  <div style={{ flex: 1, display: 'flex', height: '24px', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: '85%', backgroundColor: '#746C60', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>
                      FULL HISTORICAL REFERENCE
                    </div>
                    <div style={{ width: '15%', backgroundColor: '#6E7650', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>
                      2025–26 BENCHMARK
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Detailed Table */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '600px' }}>
                <thead>
                  <tr style={{ backgroundColor: 'var(--editorial-card, #FFFFFF)', borderBottom: '1px solid var(--editorial-border, #D8D0C2)' }}>
                    <th style={{ padding: '14px 20px', fontSize: '0.78rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>FOLD</th>
                    <th style={{ padding: '14px 20px', fontSize: '0.78rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>TRAINING WINDOW</th>
                    <th style={{ padding: '14px 20px', fontSize: '0.78rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>VALIDATION WINDOW</th>
                    <th style={{ padding: '14px 20px', fontSize: '0.78rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>EVALUATION PURPOSE</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid var(--editorial-border, #D8D0C2)' }}>
                    <td style={{ padding: '16px 20px', fontWeight: 700, color: 'var(--editorial-ink, #211E19)' }}>Fold 1</td>
                    <td style={{ padding: '16px 20px', color: 'var(--editorial-purple, #552583)', fontWeight: 600 }}>2021–22 Season</td>
                    <td style={{ padding: '16px 20px', color: '#976800', fontWeight: 700 }}>2023–24 Season</td>
                    <td style={{ padding: '16px 20px', color: 'var(--editorial-gray, #746C60)', fontSize: '0.88rem' }}>Hyperparameter grid search & baseline calibration</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--editorial-border, #D8D0C2)' }}>
                    <td style={{ padding: '16px 20px', fontWeight: 700, color: 'var(--editorial-ink, #211E19)' }}>Fold 2</td>
                    <td style={{ padding: '16px 20px', color: 'var(--editorial-purple, #552583)', fontWeight: 600 }}>2021–22 → 2023–24</td>
                    <td style={{ padding: '16px 20px', color: '#976800', fontWeight: 700 }}>2024–25 Season</td>
                    <td style={{ padding: '16px 20px', color: 'var(--editorial-gray, #746C60)', fontSize: '0.88rem' }}>Out-of-sample regularized holdout verification</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '16px 20px', fontWeight: 700, color: 'var(--editorial-ink, #211E19)' }}>Benchmark</td>
                    <td style={{ padding: '16px 20px', color: 'var(--editorial-gray, #746C60)' }}>Full Historical Set</td>
                    <td style={{ padding: '16px 20px', color: 'var(--editorial-olive, #6E7650)', fontWeight: 700 }}>2025–26 Comparative Set</td>
                    <td style={{ padding: '16px 20px', color: 'var(--editorial-gray, #746C60)', fontSize: '0.88rem' }}>Architecture comparison & offline benchmark (Not an untouched test set for C1)</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div
              style={{
                padding: '16px 20px',
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                borderTop: '1px solid var(--editorial-border, #D8D0C2)',
                fontSize: '0.84rem',
                color: 'var(--editorial-gray, #746C60)',
                lineHeight: 1.5,
              }}
            >
              <strong>Chronological Integrity Note:</strong> The 2025–26 season was explicitly utilized for model architecture benchmarking and comparative calibration. It is transparently documented as a comparison cohort rather than an untouched final holdout test set for experimental candidate models.
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          6. PLAYER MODEL EVOLUTION & ROLE STRATIFICATION (White Surface)
          ========================================================================= */}
      <section
        id="player-evolution"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-card, #FFFFFF)',
        }}
      >
        <div className="container">
          <div style={{ maxWidth: '820px', marginBottom: '40px' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                color: 'var(--editorial-purple, #552583)',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--editorial-purple, #552583)' }} />
              05 · PLAYER PERFORMANCE PROGRESSION
            </div>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
              }}
            >
              PLAYER MODEL EVOLUTION
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6 }}>
              How individual player projections progressed from naive career averages to tiered role-stratified ridge regressors.
            </p>
          </div>

          {/* Connected Horizontal Timeline Graphic */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '40px',
            }}
          >
            {[
              {
                step: '01',
                title: 'BASELINE',
                desc: 'Rolling 10-game simple moving averages. Sensitive to extreme noise, rest games, and blowouts.',
                status: 'Initial Baseline',
                accent: 'var(--editorial-gray, #746C60)',
                highlight: false,
              },
              {
                step: '02',
                title: 'RATE / USAGE EXPERIMENTS',
                desc: 'Per-minute and per-possession rate scaling. Improved normalization across differing pace environments.',
                status: 'Exploratory',
                accent: 'var(--editorial-olive, #6E7650)',
                highlight: false,
              },
              {
                step: '03',
                title: 'ROLE-STRATIFIED MODEL',
                desc: 'L2 Ridge models conditioned on rotation tier (Star, Starter, Bench) for expected minutes and counting stats.',
                status: 'Champion System',
                accent: 'var(--editorial-purple, #552583)',
                highlight: true,
              },
              {
                step: '04',
                title: 'SHADOW EVALUATION',
                desc: 'Continuous postgame error tracking evaluating challenger estimators without impacting production.',
                status: 'Active Pipeline',
                accent: 'var(--editorial-terracotta, #A35C32)',
                highlight: false,
              },
            ].map((st) => (
              <div
                key={st.title}
                style={{
                  backgroundColor: st.highlight ? 'var(--editorial-lavender, #E8E4F1)' : 'var(--editorial-bg, #F4F0E7)',
                  border: st.highlight ? '2px solid var(--editorial-purple, #552583)' : '1px solid var(--editorial-border, #D8D0C2)',
                  borderTop: `5px solid ${st.accent}`,
                  padding: '24px 20px',
                  borderRadius: 'var(--radius-xs)',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span className="font-display" style={{ fontSize: '1.4rem', fontWeight: 800, color: st.accent }}>
                    {st.step}
                  </span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      color: st.highlight ? 'var(--editorial-purple, #552583)' : 'var(--editorial-ink, #211E19)',
                      backgroundColor: st.highlight ? 'rgba(85, 37, 131, 0.12)' : 'var(--editorial-sand, #E9E2D5)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    {st.status}
                  </span>
                </div>
                <div className="font-display" style={{ fontSize: '1.15rem', color: 'var(--editorial-ink, #211E19)', marginBottom: '8px' }}>
                  {st.title}
                </div>
                <div style={{ fontSize: '0.84rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.45 }}>
                  {st.desc}
                </div>
              </div>
            ))}
          </div>

          {/* Role Groups Explanation Cards */}
          <div
            style={{
              backgroundColor: 'var(--editorial-bg, #F4F0E7)',
              border: '1px solid var(--editorial-border, #D8D0C2)',
              borderRadius: 'var(--radius-xs)',
              padding: '28px',
            }}
          >
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '16px' }}>
              Rotation Stratification Tiers (MIN, PTS, REB, AST):
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
              {/* Star Tier — Gold Accent */}
              <div
                style={{
                  padding: '20px',
                  backgroundColor: 'var(--editorial-card, #FFFFFF)',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--editorial-border, #D8D0C2)',
                  borderTop: '4px solid var(--editorial-gold, #FDB927)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="font-display" style={{ fontSize: '1.25rem', color: 'var(--editorial-ink, #211E19)', fontWeight: 800 }}>
                    STAR TIER
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#886200', backgroundColor: 'var(--editorial-pale-gold, #F7EAC6)', padding: '2px 8px', borderRadius: '4px' }}>
                    USAGE &gt; 26%
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--editorial-gray, #746C60)', marginTop: '8px', lineHeight: 1.5 }}>
                  Projected 30+ minutes. Primary offensive engines with self-generated shot creation, high free throw volume, and heavy usage.
                </p>
              </div>

              {/* Starter Tier — Purple Accent */}
              <div
                style={{
                  padding: '20px',
                  backgroundColor: 'var(--editorial-card, #FFFFFF)',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--editorial-border, #D8D0C2)',
                  borderTop: '4px solid var(--editorial-purple, #552583)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="font-display" style={{ fontSize: '1.25rem', color: 'var(--editorial-purple, #552583)', fontWeight: 800 }}>
                    STARTER TIER
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--editorial-purple, #552583)', backgroundColor: 'var(--editorial-lavender, #E8E4F1)', padding: '2px 8px', borderRadius: '4px' }}>
                    20–30 MIN
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--editorial-gray, #746C60)', marginTop: '8px', lineHeight: 1.5 }}>
                  Established rotation players. Role-specific outputs (spot-up 3-point shooting, glass rebounding, secondary creation).
                </p>
              </div>

              {/* Bench Tier — Olive Accent */}
              <div
                style={{
                  padding: '20px',
                  backgroundColor: 'var(--editorial-card, #FFFFFF)',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--editorial-border, #D8D0C2)',
                  borderTop: '4px solid var(--editorial-olive, #6E7650)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="font-display" style={{ fontSize: '1.25rem', color: 'var(--editorial-olive, #6E7650)', fontWeight: 800 }}>
                    BENCH TIER
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--editorial-olive, #6E7650)', backgroundColor: 'rgba(110, 118, 80, 0.12)', padding: '2px 8px', borderRadius: '4px' }}>
                    &lt; 20 MIN
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--editorial-gray, #746C60)', marginTop: '8px', lineHeight: 1.5 }}>
                  Variable minutes, game-script dependent usage. High sample variance stabilized using regularized Bayesian shrinkage.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          7. SHADOW MODEL EVALUATION & PROMOTION GATES (Pale Lavender Surface)
          ========================================================================= */}
      <section
        id="shadow-evaluation"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-lavender, #E8E4F1)',
        }}
      >
        <div className="container">
          <div style={{ maxWidth: '820px', marginBottom: '40px' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                color: 'var(--editorial-purple, #552583)',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--editorial-purple, #552583)' }} />
              06 · CONTINUOUS EXPERIMENTATION
            </div>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
              }}
            >
              SHADOW MODEL EVALUATION
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6 }}>
              Production stability requires that experimental models prove superiority in a production-like shadow environment prior to promotion.
            </p>
          </div>

          {/* Two-Branch Architecture Comparison Diagram */}
          <div
            style={{
              backgroundColor: 'var(--editorial-card, #FFFFFF)',
              border: '1px solid var(--editorial-border, #D8D0C2)',
              borderRadius: 'var(--radius-sm)',
              padding: '32px 28px',
              boxShadow: 'var(--shadow-sm)',
              marginBottom: '28px',
            }}
          >
            {/* Top Root Node */}
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <div
                style={{
                  display: 'inline-block',
                  backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                  border: '1px solid var(--editorial-border, #D8D0C2)',
                  padding: '10px 24px',
                  borderRadius: 'var(--radius-xs)',
                  fontWeight: 700,
                  fontSize: '0.92rem',
                  fontFamily: 'var(--font-display)',
                  letterSpacing: '0.08em',
                  color: 'var(--editorial-ink, #211E19)',
                }}
              >
                ⚡ INCOMING PREDICTION REQUEST
              </div>
              <div style={{ fontSize: '1.2rem', color: 'var(--editorial-purple, #552583)', fontWeight: 800, marginTop: '8px' }}>
                ↙ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ↘
              </div>
            </div>

            {/* Split Branches */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '24px',
                marginBottom: '24px',
              }}
            >
              {/* Branch A: Production Model (Champion) */}
              <div
                style={{
                  backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                  border: '2px solid var(--editorial-purple, #552583)',
                  borderTop: '5px solid var(--editorial-gold, #FDB927)',
                  padding: '24px',
                  borderRadius: 'var(--radius-xs)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--editorial-purple, #552583)', letterSpacing: '0.1em' }}>
                    PRIMARY ROUTE · USER FACING
                  </span>
                  <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#7E5B00', backgroundColor: 'var(--editorial-pale-gold, #F7EAC6)', padding: '2px 8px', borderRadius: '4px' }}>
                    ACTIVE CHAMPION
                  </span>
                </div>
                <h3 className="font-display" style={{ fontSize: '1.4rem', color: 'var(--editorial-ink, #211E19)', marginBottom: '8px' }}>
                  PRODUCTION MODEL
                </h3>
                <p style={{ fontSize: '0.86rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.5, marginBottom: '14px' }}>
                  Synchronous serving path with p95 &lt; 45ms latency SLA. Delivers live forecast cards, rotation strips, and point margins to the client.
                </p>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--editorial-purple, #552583)', fontFamily: 'var(--font-mono)' }}>
                  STATUS: LIVE PRODUCTION (Default)
                </div>
              </div>

              {/* Branch B: C1 Shadow Model (Experimental) */}
              <div
                style={{
                  backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                  border: '1px solid var(--editorial-border, #D8D0C2)',
                  borderTop: '5px solid var(--editorial-terracotta, #A35C32)',
                  padding: '24px',
                  borderRadius: 'var(--radius-xs)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--editorial-terracotta, #A35C32)', letterSpacing: '0.1em' }}>
                    BACKGROUND ROUTE · TELEMETRY
                  </span>
                  <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--editorial-terracotta, #A35C32)', backgroundColor: 'rgba(163, 92, 50, 0.12)', padding: '2px 8px', borderRadius: '4px' }}>
                    EXPERIMENTAL
                  </span>
                </div>
                <h3 className="font-display" style={{ fontSize: '1.4rem', color: 'var(--editorial-ink, #211E19)', marginBottom: '8px' }}>
                  C1 SHADOW MODEL
                </h3>
                <p style={{ fontSize: '0.86rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.5, marginBottom: '14px' }}>
                  Asynchronous evaluation path. Generates candidate predictions logged to PostgreSQL for offline paired comparison without client impact.
                </p>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--editorial-terracotta, #A35C32)', fontFamily: 'var(--font-mono)' }}>
                  STATUS: SHADOW MODE ONLY
                </div>
              </div>
            </div>

            {/* Bottom Confluence Sequence */}
            <div style={{ textAlign: 'center', marginBottom: '16px', color: 'var(--editorial-purple, #552583)', fontSize: '1.2rem', fontWeight: 800 }}>
              ↓
            </div>

            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                padding: '20px',
                borderRadius: 'var(--radius-xs)',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '16px',
                textAlign: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--editorial-purple, #552583)', textTransform: 'uppercase' }}>
                  01 · OUTCOMES
                </div>
                <div className="font-display" style={{ fontSize: '1.05rem', color: 'var(--editorial-ink, #211E19)', marginTop: '4px' }}>
                  POSTGAME OUTCOMES
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--editorial-gray, #746C60)', marginTop: '2px' }}>
                  Official final box scores recorded
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--editorial-purple, #552583)', textTransform: 'uppercase' }}>
                  02 · COMPARISON
                </div>
                <div className="font-display" style={{ fontSize: '1.05rem', color: 'var(--editorial-ink, #211E19)', marginTop: '4px' }}>
                  PAIRED EVALUATION
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--editorial-gray, #746C60)', marginTop: '2px' }}>
                  Wilcoxon signed-rank significance tests
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--editorial-gold, #FDB927)', textTransform: 'uppercase' }}>
                  03 · DECISION
                </div>
                <div className="font-display" style={{ fontSize: '1.05rem', color: 'var(--editorial-ink, #211E19)', marginTop: '4px' }}>
                  PROMOTION GATE
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--editorial-gray, #746C60)', marginTop: '2px' }}>
                  Explicit human approval required
                </div>
              </div>
            </div>
          </div>

          <div
            style={{
              padding: '16px 20px',
              backgroundColor: 'var(--editorial-card, #FFFFFF)',
              border: '1px solid var(--editorial-border, #D8D0C2)',
              borderRadius: 'var(--radius-xs)',
              fontSize: '0.86rem',
              color: 'var(--editorial-gray, #746C60)',
              lineHeight: 1.5,
            }}
          >
            * <strong>Strict Promotion Policy:</strong> Production predictions remain the default system. C1 remains strictly experimental until formal statistical thresholds are exceeded and human sign-off is logged in version control.
          </div>
        </div>
      </section>

      {/* =========================================================================
          8. PRODUCTION ARCHITECTURE (White Surface Systems Diagram)
          ========================================================================= */}
      <section
        id="production-architecture"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-card, #FFFFFF)',
        }}
      >
        <div className="container">
          <div style={{ maxWidth: '820px', marginBottom: '40px' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                color: 'var(--editorial-olive, #6E7650)',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--editorial-olive, #6E7650)' }} />
              07 · SYSTEM INFRASTRUCTURE
            </div>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
              }}
            >
              PRODUCTION ARCHITECTURE
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6 }}>
              A lightweight, highly resilient serving architecture deployed on Render container instances.
            </p>
          </div>

          {/* Primary Runtime Stack Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '32px',
            }}
          >
            {[
              { tier: 'CLIENT LAYER', tech: 'React / Vite', role: 'Responsive single-page application with cached client state and fast hydration.', accent: 'var(--editorial-purple, #552583)' },
              { tier: 'API RUNTIME', tech: 'FastAPI (Python 3.11)', role: 'Asynchronous REST gateway, request validation, and prediction pre-warming.', accent: 'var(--editorial-gold, #FDB927)' },
              { tier: 'CONTAINER', tech: 'Docker Multi-Stage', role: 'Isolated build steps ensuring slim deployment footprint (<450MB).', accent: 'var(--editorial-olive, #6E7650)' },
              { tier: 'HOSTING', tech: 'Render Cloud', role: 'Auto-healing web service with continuous deployment from GitHub main.', accent: 'var(--editorial-terracotta, #A35C32)' },
            ].map((st) => (
              <div
                key={st.tier}
                style={{
                  backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                  border: '1px solid var(--editorial-border, #D8D0C2)',
                  borderTop: `4px solid ${st.accent}`,
                  padding: '24px 20px',
                  borderRadius: 'var(--radius-xs)',
                }}
              >
                <div style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.1em', marginBottom: '6px' }}>
                  {st.tier}
                </div>
                <div className="font-display" style={{ fontSize: '1.25rem', color: 'var(--editorial-ink, #211E19)', marginBottom: '8px' }}>
                  {st.tech}
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.45 }}>
                  {st.role}
                </div>
              </div>
            ))}
          </div>

          {/* Supporting Infrastructure */}
          <div
            style={{
              backgroundColor: 'var(--editorial-sand, #E9E2D5)',
              border: '1px solid var(--editorial-border, #D8D0C2)',
              borderRadius: 'var(--radius-xs)',
              padding: '24px 28px',
            }}
          >
            <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '14px' }}>
              Supporting Data & Modeling Technologies:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
              {[
                { name: 'Neon PostgreSQL', desc: 'Serverless prediction persistence & monitoring store' },
                { name: 'Apache Parquet', desc: 'Columnar storage for box scores & rolling features' },
                { name: 'DuckDB', desc: 'In-process zero-copy SQL queries & fast window aggregations' },
                { name: 'Scikit-learn', desc: 'L2 Ridge & Logistic Regression model serialization' },
                { name: 'Pydantic V2', desc: 'Strict runtime input validation & output contracts' }
              ].map((item) => (
                <div
                  key={item.name}
                  style={{
                    backgroundColor: 'var(--editorial-card, #FFFFFF)',
                    border: '1px solid var(--editorial-border, #D8D0C2)',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '0.82rem',
                  }}
                >
                  <strong style={{ color: 'var(--editorial-purple, #552583)' }}>{item.name}:</strong>{' '}
                  <span style={{ color: 'var(--editorial-gray, #746C60)' }}>{item.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          9. OBSERVABILITY & RELIABILITY (Warm Ivory Checklist)
          ========================================================================= */}
      <section
        id="observability"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-bg, #F4F0E7)',
        }}
      >
        <div className="container">
          <div style={{ maxWidth: '820px', marginBottom: '40px' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                color: 'var(--editorial-purple, #552583)',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--editorial-purple, #552583)' }} />
              08 · TELEMETRY &amp; RESILIENCE
            </div>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
              }}
            >
              OBSERVABILITY &amp; RELIABILITY
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6 }}>
              Production readiness verified through automated health probes, drift statistical testing, and request tracking.
            </p>
          </div>

          {/* Implemented Capabilities Checklist Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '16px',
            }}
          >
            {[
              {
                capability: 'Health & Readiness Endpoints',
                code: 'GET /health · GET /health/ready',
                description: 'Liveness probes checking database connection, model artifact availability, and schedule integrity.',
                status: 'OPERATIONAL'
              },
              {
                capability: 'Model Status & Metadata',
                code: 'GET /monitoring/health',
                description: 'Serves current champion model version, artifact hashes, and pre-warm execution timestamps.',
                status: 'CHAMPION v1.0'
              },
              {
                capability: 'Structured JSON Logging',
                code: 'log_event()',
                description: 'Standardized ISO-8601 logs including latency_ms, endpoint, status, and payload signatures.',
                status: 'STRUCTURED'
              },
              {
                capability: 'Request Correlation IDs',
                code: 'X-Request-ID Middleware',
                description: 'Unique UUIDv4 per incoming request propagated through downstream inference and DB operations.',
                status: 'TRACKED'
              },
              {
                capability: 'Data Quality Verification',
                code: 'Pydantic V2 Schemas',
                description: 'Input shape assertion, null-checking, and range boundaries before model vector generation.',
                status: 'ENFORCED'
              },
              {
                capability: 'Feature Drift Monitoring',
                code: 'DataDriftDetector',
                description: 'Two-sample Kolmogorov-Smirnov and PSI statistics comparing rolling 30-day distributions to training baseline.',
                status: 'SCHEDULED'
              },
              {
                capability: 'Prediction Integrity Bounding',
                code: 'Probability [0.01, 0.99]',
                description: 'Calibrated boundary clipping preventing degenerate edge-case probabilities or negative minute predictions.',
                status: 'BOUNDED'
              },
            ].map((item) => (
              <div
                key={item.capability}
                style={{
                  backgroundColor: 'var(--editorial-card, #FFFFFF)',
                  border: '1px solid var(--editorial-border, #D8D0C2)',
                  padding: '20px 22px',
                  borderRadius: 'var(--radius-xs)',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div className="font-display" style={{ fontSize: '1.05rem', color: 'var(--editorial-ink, #211E19)', fontWeight: 700 }}>
                    {item.capability}
                  </div>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      color: 'var(--editorial-purple, #552583)',
                      backgroundColor: 'var(--editorial-lavender, #E8E4F1)',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      letterSpacing: '0.06em',
                    }}
                  >
                    {item.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--editorial-terracotta, #A35C32)', marginBottom: '8px' }}>
                  {item.code}
                </div>
                <div style={{ fontSize: '0.84rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.45 }}>
                  {item.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =========================================================================
          10. MODEL PERFORMANCE (Verified Holdout Metrics Quad)
          ========================================================================= */}
      <section
        id="model-performance"
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--editorial-border, #D8D0C2)',
          backgroundColor: 'var(--editorial-card, #FFFFFF)',
        }}
      >
        <div className="container">
          <div style={{ maxWidth: '820px', marginBottom: '40px' }}>
            <div
              style={{
                fontSize: '0.82rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                fontFamily: 'var(--font-display)',
                color: 'var(--editorial-purple, #552583)',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--editorial-gold, #FDB927)' }} />
              09 · QUANTITATIVE RIGOR
            </div>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.5vw, 2.8rem)',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
              }}
            >
              VERIFIED MODEL PERFORMANCE
            </h2>
            <p style={{ fontSize: '1.05rem', color: 'var(--editorial-gray, #746C60)', lineHeight: 1.6 }}>
              Historical holdout metrics computed on out-of-sample regular season games using strict walk-forward evaluation.
            </p>
          </div>

          {/* Metric Quad Cards with Gold & Purple Prominence */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '24px',
              marginBottom: '32px',
            }}
          >
            {/* 68.07% Accuracy — Lakers Gold */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderTop: '5px solid var(--editorial-gold, #FDB927)',
                padding: '28px 24px',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              <div
                className="font-display tabular-nums"
                style={{ fontSize: '3.2rem', fontWeight: 800, color: '#C68B00', lineHeight: 1 }}
              >
                68.07%
              </div>
              <div style={{ fontSize: '0.84rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: '12px' }}>
                ACCURACY
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--editorial-gray, #746C60)', marginTop: '6px', lineHeight: 1.4 }}>
                Out-of-sample game outcome prediction rate on regular-season holdout matches.
              </p>
            </div>

            {/* 0.6076 Log Loss — Lakers Purple */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderTop: '5px solid var(--editorial-purple, #552583)',
                padding: '28px 24px',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              <div
                className="font-display tabular-nums"
                style={{ fontSize: '3.2rem', fontWeight: 800, color: 'var(--editorial-purple, #552583)', lineHeight: 1 }}
              >
                0.6076
              </div>
              <div style={{ fontSize: '0.84rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: '12px' }}>
                LOG LOSS
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--editorial-gray, #746C60)', marginTop: '6px', lineHeight: 1.4 }}>
                Cross-entropy loss penalizing overconfident incorrect probabilistic predictions.
              </p>
            </div>

            {/* 0.2093 Brier Score — Ink */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderTop: '5px solid var(--editorial-ink, #211E19)',
                padding: '28px 24px',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              <div
                className="font-display tabular-nums"
                style={{ fontSize: '3.2rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', lineHeight: 1 }}
              >
                0.2093
              </div>
              <div style={{ fontSize: '0.84rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: '12px' }}>
                BRIER SCORE
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--editorial-gray, #746C60)', marginTop: '6px', lineHeight: 1.4 }}>
                Mean squared error of probabilistic forecast vs. binary game outcomes.
              </p>
            </div>

            {/* 0.0262 ECE — Muted Olive */}
            <div
              style={{
                backgroundColor: 'var(--editorial-bg, #F4F0E7)',
                border: '1px solid var(--editorial-border, #D8D0C2)',
                borderTop: '5px solid var(--editorial-olive, #6E7650)',
                padding: '28px 24px',
                borderRadius: 'var(--radius-xs)',
              }}
            >
              <div
                className="font-display tabular-nums"
                style={{ fontSize: '3.2rem', fontWeight: 800, color: 'var(--editorial-olive, #6E7650)', lineHeight: 1 }}
              >
                0.0262
              </div>
              <div style={{ fontSize: '0.84rem', fontWeight: 800, color: 'var(--editorial-ink, #211E19)', letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: '12px' }}>
                CALIBRATION (ECE)
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--editorial-gray, #746C60)', marginTop: '6px', lineHeight: 1.4 }}>
                Expected Calibration Error verifying that 70% confidence predictions win ~70% of the time.
              </p>
            </div>
          </div>

          <div
            style={{
              padding: '16px 20px',
              backgroundColor: 'var(--editorial-sand, #E9E2D5)',
              borderRadius: 'var(--radius-xs)',
              fontSize: '0.84rem',
              color: 'var(--editorial-ink, #211E19)',
              lineHeight: 1.5,
            }}
          >
            <strong>Evaluation Scope Disclosure:</strong> The metrics above represent historical holdout performance of the production Game Outcome model. They are not to be confused with player-level projection metrics (which evaluate MAE across minutes and points) or unpromoted C1 shadow experiments.
          </div>
        </div>
      </section>

      {/* =========================================================================
          11. EDITORIAL FOOTER & RETURN TO MAIN PRODUCT
          ========================================================================= */}
      <footer
        style={{
          padding: '60px 0 80px 0',
          backgroundColor: 'var(--editorial-bg, #F4F0E7)',
        }}
      >
        <div className="container" style={{ textAlign: 'center' }}>
          <div style={{ maxWidth: '640px', margin: '0 auto' }}>
            <h3
              className="font-display"
              style={{
                fontSize: '1.8rem',
                color: 'var(--editorial-ink, #211E19)',
                marginBottom: '12px',
                textTransform: 'uppercase',
              }}
            >
              READY TO EXPLORE THE PREDICTIONS?
            </h3>
            <p style={{ fontSize: '1rem', color: 'var(--editorial-gray, #746C60)', marginBottom: '24px' }}>
              Experience the live forecasts, interactive schedule switcher, and rotation projections.
            </p>
            <a
              href="/"
              onClick={(e) => handleReturnHome(e, 'next-game')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '10px',
                backgroundColor: 'var(--editorial-purple, #552583)',
                color: '#FFFFFF',
                fontFamily: 'var(--font-display)',
                fontSize: '1rem',
                fontWeight: 700,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                padding: '14px 28px',
                borderRadius: 'var(--radius-sm)',
                textDecoration: 'none',
                boxShadow: '0 4px 14px rgba(85, 37, 131, 0.25)',
                transition: 'all 200ms ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#421B66';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--editorial-purple, #552583)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <span>←</span> Return to Game Forecasts
            </a>
          </div>

          <div
            style={{
              marginTop: '50px',
              paddingTop: '24px',
              borderTop: '1px solid var(--editorial-border, #D8D0C2)',
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.8rem',
              color: 'var(--editorial-gray, #746C60)',
            }}
          >
            <span>© 2026 Lakers in 5 · Engineered by Animesh</span>
            <span style={{ fontWeight: 700, color: 'var(--editorial-purple, #552583)' }}>
              SHOWTIME × SPORTS INTELLIGENCE
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
