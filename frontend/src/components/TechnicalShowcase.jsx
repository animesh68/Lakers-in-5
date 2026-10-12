import React from 'react';

/**
 * Technical Showcase — Engineering Storytelling Layer
 * Explains the ML & MLOps architecture cleanly with visual diagrams and verified holdout metrics.
 */
export default function TechnicalShowcase() {
  return (
    <div id="engine" style={{ backgroundColor: 'var(--surface-charcoal)', color: '#FFFFFF' }}>
      
      {/* =========================================================================
          1. UNDER THE HOOD & THE MODEL STACK
          ========================================================================= */}
      <section
        style={{
          padding: '90px 0 70px 0',
          borderBottom: '1px solid var(--surface-charcoal-border)',
        }}
      >
        <div className="container">
          {/* Section Eyebrow & Intro */}
          <div style={{ maxWidth: '820px', marginBottom: '48px' }}>
            <div className="section-eyebrow light">
              <span>●</span> SYSTEM ARCHITECTURE
            </div>
            <h2 className="section-title light" style={{ marginBottom: '16px' }}>
              UNDER THE HOOD
            </h2>
            <p
              style={{
                fontSize: 'clamp(1.1rem, 2vw, 1.35rem)',
                color: '#E2DFE8',
                lineHeight: 1.6,
                fontWeight: 400,
              }}
            >
              Lakers in 5 is a production ML system built to generate pregame predictions from historical NBA data.
            </p>
          </div>

          {/* THE MODEL STACK */}
          <div style={{ marginTop: '36px' }}>
            <div className="section-eyebrow light" style={{ color: 'var(--gold-accent)', marginBottom: '8px' }}>
              CHAMPION INFERENCE ENGINES
            </div>
            <h3 className="font-display" style={{ fontSize: 'clamp(1.8rem, 3.5vw, 2.4rem)', color: '#FFFFFF', marginBottom: '28px', letterSpacing: '0.04em' }}>
              THE MODEL STACK
            </h3>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: '20px',
              }}
            >
              {/* Outcome Model */}
              <div
                style={{
                  backgroundColor: 'var(--surface-charcoal-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--surface-charcoal-border)',
                  padding: '24px',
                  borderTop: '3px solid var(--gold-accent)',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--gold-accent)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '8px' }}>
                  GAME OUTCOME
                </div>
                <div className="font-display" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFFFFF', marginBottom: '6px' }}>
                  Logistic Regression
                </div>
                <p style={{ fontSize: '0.88rem', color: '#A39DAE', lineHeight: 1.5 }}>
                  Calibrated probabilistic classifier predicting Lakers win probability across neutral and home splits.
                </p>
              </div>

              {/* Margin Model */}
              <div
                style={{
                  backgroundColor: 'var(--surface-charcoal-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--surface-charcoal-border)',
                  padding: '24px',
                  borderTop: '3px solid var(--purple-light)',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--purple-light)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '8px' }}>
                  GAME MARGIN
                </div>
                <div className="font-display" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFFFFF', marginBottom: '6px' }}>
                  Ridge Regression
                </div>
                <p style={{ fontSize: '0.88rem', color: '#A39DAE', lineHeight: 1.5 }}>
                  L2 regularized point spread estimator predicting expected point margin before tipoff.
                </p>
              </div>

              {/* Player Projections */}
              <div
                style={{
                  backgroundColor: 'var(--surface-charcoal-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--surface-charcoal-border)',
                  padding: '24px',
                  borderTop: '3px solid #60a5fa',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#60a5fa', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '8px' }}>
                  PLAYER PROJECTIONS
                </div>
                <div className="font-display" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFFFFF', marginBottom: '6px' }}>
                  Role-Stratified Ridge
                </div>
                <p style={{ fontSize: '0.88rem', color: '#A39DAE', lineHeight: 1.5 }}>
                  Stratified estimators for Minutes, Points, Rebounds, and Assists across active rotations.
                </p>
              </div>

              {/* Validation Strategy */}
              <div
                style={{
                  backgroundColor: 'var(--surface-charcoal-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--surface-charcoal-border)',
                  padding: '24px',
                  borderTop: '3px solid #34d399',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#34d399', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '8px' }}>
                  VALIDATION
                </div>
                <div className="font-display" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFFFFF', marginBottom: '6px' }}>
                  Walk-Forward Cross-Validation
                </div>
                <p style={{ fontSize: '0.88rem', color: '#A39DAE', lineHeight: 1.5 }}>
                  Strict expanding-window chronological validation ensuring zero future-data leakage.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          2. DATA PIPELINE & PREGAME FEATURES
          ========================================================================= */}
      <section
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--surface-charcoal-border)',
          backgroundColor: '#0F0D12',
        }}
      >
        <div className="container">
          <div className="section-eyebrow light">
            <span>●</span> DATA PIPELINE
          </div>
          <h3 className="section-title light" style={{ marginBottom: '12px' }}>
            END-TO-END DATA FLOW
          </h3>
          <p style={{ fontSize: '1.05rem', color: '#A39DAE', maxWidth: '680px', marginBottom: '36px' }}>
            From raw NBA play-by-play data to real-time client inference.
          </p>

          {/* VISUAL PIPELINE FLOW */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '12px',
              alignItems: 'center',
              backgroundColor: 'var(--surface-charcoal-card)',
              padding: '24px',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--surface-charcoal-border)',
              marginBottom: '50px',
            }}
          >
            {[
              'NBA HISTORICAL DATA',
              'DATA VALIDATION',
              'FEATURE ENGINEERING',
              'ROLLING STATISTICS',
              'TEAM STRENGTH / ELO',
              'GAME PREDICTION',
              'PLAYER PROJECTION',
              'FASTAPI',
              'LAKERS IN 5'
            ].map((step, idx, arr) => (
              <React.Fragment key={step}>
                <div
                  style={{
                    backgroundColor: idx === arr.length - 1 ? 'var(--gold-accent)' : idx === 0 ? 'var(--purple-primary)' : 'rgba(255, 255, 255, 0.06)',
                    color: idx === arr.length - 1 ? '#121015' : '#FFFFFF',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.82rem',
                    fontWeight: 700,
                    letterSpacing: '0.06em',
                    fontFamily: 'var(--font-display)',
                    whiteSpace: 'nowrap',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  {step}
                </div>
                {idx < arr.length - 1 && (
                  <span style={{ color: 'var(--gold-accent)', fontSize: '1.1rem', fontWeight: 800 }}>→</span>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* BUILT BEFORE TIPOFF (PREGAME-ONLY FEATURES) */}
          <div>
            <div className="section-eyebrow light" style={{ color: 'var(--gold-accent)', marginBottom: '8px' }}>
              INTEGRITY CONTRACT
            </div>
            <h4 className="font-display" style={{ fontSize: 'clamp(1.6rem, 3vw, 2.2rem)', color: '#FFFFFF', marginBottom: '10px' }}>
              BUILT BEFORE TIPOFF
            </h4>
            <p style={{ fontSize: '1rem', color: '#CBD5E1', maxWidth: '720px', marginBottom: '24px' }}>
              Every prediction is generated strictly using information available before the game begins.
            </p>

            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              {[
                'PREGAME-ONLY FEATURES',
                'ROLLING FORM',
                'TEAM STRENGTH',
                'PLAYER USAGE',
                'EXPECTED MINUTES',
                'RECENT PERFORMANCE',
                'ELO RATINGS',
                'REST DAY DISPARITY',
                'HOME / AWAY SPLITS'
              ].map((feat) => (
                <span
                  key={feat}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: 'rgba(253, 185, 39, 0.08)',
                    border: '1px solid var(--gold-border)',
                    color: 'var(--gold-accent)',
                    fontSize: '0.82rem',
                    fontWeight: 700,
                    fontFamily: 'var(--font-display)',
                    letterSpacing: '0.08em',
                  }}
                >
                  ✓ {feat}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          3. LEAKAGE CONTROL & WALK-FORWARD VALIDATION
          ========================================================================= */}
      <section
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--surface-charcoal-border)',
        }}
      >
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '40px', alignItems: 'start' }}>
            
            {/* LEAKAGE CONTROL */}
            <div
              style={{
                backgroundColor: 'var(--surface-charcoal-card)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--surface-charcoal-border)',
                padding: '32px',
              }}
            >
              <div className="section-eyebrow light">
                <span>●</span> TEMPORAL PURITY
              </div>
              <h3 className="font-display" style={{ fontSize: '1.8rem', color: '#FFFFFF', marginBottom: '8px' }}>
                NO TEMPORAL LEAKAGE
              </h3>
              <p style={{ fontSize: '0.92rem', color: '#A39DAE', lineHeight: 1.5, marginBottom: '24px' }}>
                Features are generated exclusively using information recorded prior to tipoff.
              </p>

              {/* Visual Leakage Diagram */}
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  backgroundColor: '#121015',
                  padding: '20px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#E2DFE8', fontSize: '0.9rem', fontWeight: 600 }}>
                  <span>01. Previous Games [t &lt; 0]</span>
                  <span style={{ color: '#34d399', fontSize: '0.75rem' }}>HISTORICAL ONLY</span>
                </div>
                <div style={{ textAlign: 'center', color: 'var(--gold-accent)', fontWeight: 800 }}>↓</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#E2DFE8', fontSize: '0.9rem', fontWeight: 600 }}>
                  <span>02. Feature Engineering</span>
                  <span style={{ color: '#60a5fa', fontSize: '0.75rem' }}>LAGGED AGGREGATIONS</span>
                </div>
                <div style={{ textAlign: 'center', color: 'var(--gold-accent)', fontWeight: 800 }}>↓</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#E2DFE8', fontSize: '0.9rem', fontWeight: 600 }}>
                  <span>03. Model Inference</span>
                  <span style={{ color: 'var(--gold-accent)', fontSize: '0.75rem' }}>PRE-GAME TIMESTAMP</span>
                </div>
                <div style={{ textAlign: 'center', color: 'var(--gold-accent)', fontWeight: 800 }}>↓</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#FFFFFF', fontSize: '0.9rem', fontWeight: 700, backgroundColor: 'rgba(85, 37, 131, 0.4)', padding: '6px 12px', borderRadius: '4px' }}>
                  <span>04. Today's Game Outcome</span>
                  <span style={{ color: '#FDB927', fontSize: '0.75rem' }}>TARGET [t = 0]</span>
                </div>
              </div>
            </div>

            {/* WALK-FORWARD VALIDATION */}
            <div
              style={{
                backgroundColor: 'var(--surface-charcoal-card)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--surface-charcoal-border)',
                padding: '32px',
              }}
            >
              <div className="section-eyebrow light">
                <span>●</span> RIGOROUS EVALUATION
              </div>
              <h3 className="font-display" style={{ fontSize: '1.8rem', color: '#FFFFFF', marginBottom: '8px' }}>
                VALIDATED CHRONOLOGICALLY
              </h3>
              <p style={{ fontSize: '0.92rem', color: '#A39DAE', lineHeight: 1.5, marginBottom: '24px' }}>
                Expanding window evaluation mimics actual real-world deployment across seasons.
              </p>

              {/* Walk-Forward Visual */}
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                  backgroundColor: '#121015',
                  padding: '20px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
              >
                {/* Fold 1 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ flex: 1, backgroundColor: 'rgba(85, 37, 131, 0.3)', padding: '8px 12px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700, color: '#C9C4D0', border: '1px solid var(--purple-border)' }}>
                    TRAIN: 2021–22
                  </div>
                  <span style={{ color: 'var(--gold-accent)', fontWeight: 800 }}>→</span>
                  <div style={{ flex: 1, backgroundColor: 'rgba(253, 185, 39, 0.15)', padding: '8px 12px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--gold-accent)', border: '1px solid var(--gold-border)' }}>
                    VALIDATE: 2023–24
                  </div>
                </div>

                {/* Fold 2 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ flex: 1, backgroundColor: 'rgba(85, 37, 131, 0.3)', padding: '8px 12px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700, color: '#C9C4D0', border: '1px solid var(--purple-border)' }}>
                    TRAIN: 2021–22 → 2023–24
                  </div>
                  <span style={{ color: 'var(--gold-accent)', fontWeight: 800 }}>→</span>
                  <div style={{ flex: 1, backgroundColor: 'rgba(253, 185, 39, 0.15)', padding: '8px 12px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--gold-accent)', border: '1px solid var(--gold-border)' }}>
                    VALIDATE: 2024–25
                  </div>
                </div>

                <div style={{ textAlign: 'center', marginTop: '6px' }}>
                  <span className="font-display" style={{ fontSize: '0.85rem', color: '#A39DAE', letterSpacing: '0.1em' }}>
                    METHOD: WALK-FORWARD VALIDATION
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* =========================================================================
          4. ROLE-STRATIFICATION & SHADOW MLOPS
          ========================================================================= */}
      <section
        style={{
          padding: '80px 0',
          borderBottom: '1px solid var(--surface-charcoal-border)',
          backgroundColor: '#0F0D12',
        }}
      >
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '40px', alignItems: 'start' }}>
            
            {/* PLAYER MODEL EVOLUTION */}
            <div
              style={{
                backgroundColor: 'var(--surface-charcoal-card)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--surface-charcoal-border)',
                padding: '32px',
              }}
            >
              <div className="section-eyebrow light">
                <span>●</span> PLAYER MODELING
              </div>
              <h3 className="font-display" style={{ fontSize: '1.8rem', color: '#FFFFFF', marginBottom: '8px' }}>
                FROM AVERAGES TO ROLES
              </h3>
              <p style={{ fontSize: '0.92rem', color: '#A39DAE', lineHeight: 1.5, marginBottom: '24px' }}>
                Individual projections evolved from generic team averages to tiered role-stratified regressors.
              </p>

              {/* Evolution Steps */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
                {['BASELINE (ROLLING AVG)', 'RATE / USAGE EXPERIMENTS', 'ROLE-STRATIFIED MODEL', 'SHADOW VALIDATION'].map((step, idx) => (
                  <div
                    key={step}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: idx === 2 ? 'rgba(85, 37, 131, 0.35)' : 'rgba(255, 255, 255, 0.04)',
                      border: idx === 2 ? '1px solid var(--gold-border)' : '1px solid rgba(255, 255, 255, 0.06)',
                    }}
                  >
                    <span className="font-display" style={{ color: 'var(--gold-accent)', fontWeight: 800, fontSize: '0.85rem' }}>
                      0{idx + 1}
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: idx === 2 ? 'var(--gold-accent)' : '#E2DFE8' }}>
                      {step}
                    </span>
                  </div>
                ))}
              </div>

              {/* Stratified Tiers */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', textAlign: 'center' }}>
                <div style={{ padding: '10px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="font-display" style={{ color: 'var(--gold-accent)', fontSize: '1.1rem', fontWeight: 800 }}>STAR</div>
                  <div style={{ fontSize: '0.72rem', color: '#A39DAE', marginTop: '2px' }}>High Usage</div>
                </div>
                <div style={{ padding: '10px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="font-display" style={{ color: '#FFFFFF', fontSize: '1.1rem', fontWeight: 800 }}>STARTER</div>
                  <div style={{ fontSize: '0.72rem', color: '#A39DAE', marginTop: '2px' }}>Solid Rotation</div>
                </div>
                <div style={{ padding: '10px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="font-display" style={{ color: '#A39DAE', fontSize: '1.1rem', fontWeight: 800 }}>BENCH</div>
                  <div style={{ fontSize: '0.72rem', color: '#A39DAE', marginTop: '2px' }}>Variable Minutes</div>
                </div>
              </div>
            </div>

            {/* SHADOW MODEL / MLOPS */}
            <div
              style={{
                backgroundColor: 'var(--surface-charcoal-card)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--surface-charcoal-border)',
                padding: '32px',
              }}
            >
              <div className="section-eyebrow light">
                <span>●</span> SAFE DEPLOYMENT
              </div>
              <h3 className="font-display" style={{ fontSize: '1.8rem', color: '#FFFFFF', marginBottom: '8px' }}>
                SHADOW MODELS
              </h3>
              <p style={{ fontSize: '0.92rem', color: '#A39DAE', lineHeight: 1.5, marginBottom: '24px' }}>
                Challenger architectures evaluate concurrently alongside champion models without impacting live users.
              </p>

              {/* Shadow Pipeline Diagram */}
              <div
                style={{
                  backgroundColor: '#121015',
                  padding: '20px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#FFFFFF' }}>INFERENCE REQUEST</span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <span style={{ backgroundColor: 'rgba(85, 37, 131, 0.4)', padding: '4px 10px', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--gold-accent)', border: '1px solid var(--gold-border)' }}>
                      PRODUCTION MODEL (LIVE)
                    </span>
                    <span style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', padding: '4px 10px', borderRadius: '4px', fontSize: '0.75rem', color: '#93c5fd', border: '1px solid rgba(147, 197, 253, 0.2)' }}>
                      C1 SHADOW MODEL (EXPERIMENT)
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px', fontSize: '0.78rem', color: '#A39DAE' }}>
                  <span>1. PREDICTIONS</span>
                  <span>→</span>
                  <span>2. POSTGAME</span>
                  <span>→</span>
                  <span>3. EVALUATION</span>
                  <span>→</span>
                  <span style={{ color: '#34d399', fontWeight: 700 }}>4. PROMOTION GATE</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* =========================================================================
          5. PRODUCTION SYSTEM, OBSERVABILITY & VERIFIED METRICS
          ========================================================================= */}
      <section
        style={{
          padding: '80px 0 100px 0',
        }}
      >
        <div className="container">
          
          {/* FROM MODEL TO PRODUCTION */}
          <div style={{ marginBottom: '60px' }}>
            <div className="section-eyebrow light">
              <span>●</span> FULL STACK
            </div>
            <h3 className="section-title light" style={{ marginBottom: '12px' }}>
              FROM MODEL TO PRODUCTION
            </h3>
            <p style={{ fontSize: '1.05rem', color: '#A39DAE', maxWidth: '680px', marginBottom: '32px' }}>
              Built as a reliable distributed application rather than an isolated notebook.
            </p>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '16px',
                marginBottom: '24px',
              }}
            >
              {[
                { layer: 'FRONTEND', tech: 'React / Vite', desc: 'Component architecture with responsive charts' },
                { layer: 'API GATEWAY', tech: 'FastAPI', desc: 'High-throughput async Python endpoints' },
                { layer: 'CONTAINER', tech: 'Docker', desc: 'Deterministic builds and dependencies' },
                { layer: 'CLOUD DEPLOY', tech: 'Render', desc: 'Automated CI/CD hosting and health checks' },
              ].map((item) => (
                <div
                  key={item.layer}
                  style={{
                    backgroundColor: 'var(--surface-charcoal-card)',
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--surface-charcoal-border)',
                  }}
                >
                  <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--gold-accent)', letterSpacing: '0.1em', marginBottom: '6px' }}>
                    {item.layer}
                  </div>
                  <div className="font-display" style={{ fontSize: '1.3rem', color: '#FFFFFF', marginBottom: '4px' }}>
                    {item.tech}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#A39DAE' }}>
                    {item.desc}
                  </div>
                </div>
              ))}
            </div>

            {/* Supporting Stack Chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#A39DAE', fontWeight: 600 }}>SUPPORTING INFRASTRUCTURE:</span>
              {['Neon PostgreSQL', 'Apache Parquet', 'DuckDB', 'Scikit-Learn ML Models', 'Pydantic Schemas'].map((inf) => (
                <span
                  key={inf}
                  style={{
                    fontSize: '0.78rem',
                    padding: '4px 10px',
                    backgroundColor: 'rgba(255,255,255,0.05)',
                    borderRadius: '4px',
                    color: '#E2DFE8',
                    border: '1px solid rgba(255,255,255,0.1)',
                  }}
                >
                  {inf}
                </span>
              ))}
            </div>
          </div>

          {/* OBSERVABILITY & VERIFIED HOLDOUT METRICS */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '32px' }}>
            
            {/* Observability */}
            <div
              style={{
                backgroundColor: 'var(--surface-charcoal-card)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--surface-charcoal-border)',
                padding: '28px',
              }}
            >
              <div className="section-eyebrow light">
                <span>●</span> TELEMETRY
              </div>
              <h4 className="font-display" style={{ fontSize: '1.5rem', color: '#FFFFFF', marginBottom: '16px' }}>
                PRODUCTION OBSERVABILITY
              </h4>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                {[
                  { label: 'HEALTH & READINESS', status: 'ACTIVE' },
                  { label: 'MODEL STATUS', status: 'CHAMPION' },
                  { label: 'STRUCTURED LOGGING', status: 'JSON' },
                  { label: 'REQUEST IDs', status: 'UUIDv4' },
                  { label: 'DATA QUALITY', status: 'VALIDATED' },
                  { label: 'DRIFT MONITORING', status: 'ENABLED' },
                ].map((obs) => (
                  <div
                    key={obs.label}
                    style={{
                      padding: '10px 12px',
                      backgroundColor: 'rgba(255,255,255,0.03)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid rgba(255,255,255,0.05)',
                    }}
                  >
                    <div style={{ fontSize: '0.72rem', color: '#A39DAE', fontWeight: 600 }}>{obs.label}</div>
                    <div className="font-display" style={{ fontSize: '0.95rem', color: 'var(--gold-accent)', marginTop: '2px' }}>{obs.status}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Verified Holdout Performance */}
            <div
              style={{
                backgroundColor: 'var(--surface-charcoal-card)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--surface-charcoal-border)',
                padding: '28px',
                borderTop: '3px solid var(--gold-accent)',
              }}
            >
              <div className="section-eyebrow light">
                <span>●</span> REPRODUCIBLE BENCHMARK
              </div>
              <h4 className="font-display" style={{ fontSize: '1.5rem', color: '#FFFFFF', marginBottom: '16px' }}>
                HOLDOUT PERFORMANCE
              </h4>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                <div>
                  <div className="font-display tabular-nums" style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--gold-accent)', lineHeight: 1 }}>
                    68.07%
                  </div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#A39DAE', letterSpacing: '0.08em', marginTop: '4px' }}>
                    GAME ACCURACY
                  </div>
                </div>

                <div>
                  <div className="font-display tabular-nums" style={{ fontSize: '2.4rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
                    0.6076
                  </div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#A39DAE', letterSpacing: '0.08em', marginTop: '4px' }}>
                    LOG LOSS
                  </div>
                </div>

                <div>
                  <div className="font-display tabular-nums" style={{ fontSize: '2.4rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
                    0.2093
                  </div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#A39DAE', letterSpacing: '0.08em', marginTop: '4px' }}>
                    BRIER SCORE
                  </div>
                </div>

                <div>
                  <div className="font-display tabular-nums" style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--gold-accent)', lineHeight: 1 }}>
                    0.0262
                  </div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#A39DAE', letterSpacing: '0.08em', marginTop: '4px' }}>
                    CALIBRATION ERROR
                  </div>
                </div>
              </div>
            </div>

          </div>

        </div>
      </section>

    </div>
  );
}
