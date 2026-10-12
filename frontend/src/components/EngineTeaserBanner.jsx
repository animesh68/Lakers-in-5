import React from 'react';

/**
 * EngineTeaserBanner — Compact Homepage Editorial Transition
 * Replaces large technical sections on the product homepage with a clean,
 * refined editorial transition linking directly to /engine.
 */
export default function EngineTeaserBanner({ onNavigate }) {
  const handleClick = (e) => {
    e.preventDefault();
    if (onNavigate) {
      onNavigate('/engine');
    } else {
      window.history.pushState({}, '', '/engine');
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };

  return (
    <section
      id="engine-teaser"
      style={{
        backgroundColor: 'var(--editorial-bg)',
        borderTop: '1px solid var(--editorial-border)',
        borderBottom: '1px solid var(--editorial-border)',
        padding: '56px 0',
      }}
    >
      <div className="container">
        <div
          style={{
            maxWidth: '920px',
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: '16px',
          }}
        >
          {/* Eyebrow */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              fontFamily: 'var(--font-display)',
              fontSize: '0.82rem',
              fontWeight: 700,
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
              color: 'var(--editorial-terracotta)',
            }}
          >
            <span>●</span> THE ENGINEERING BEHIND THE GAME
          </div>

          {/* Headline */}
          <h2
            className="font-display"
            style={{
              fontSize: 'clamp(1.6rem, 3.2vw, 2.3rem)',
              fontWeight: 700,
              letterSpacing: '0.03em',
              color: 'var(--editorial-ink)',
              lineHeight: 1.15,
              textTransform: 'uppercase',
              maxWidth: '780px',
            }}
          >
            Historical NBA data. Pregame features. Chronological evaluation. Production inference.
          </h2>

          {/* Supporting brief */}
          <p
            style={{
              fontSize: '1rem',
              color: 'var(--editorial-gray)',
              maxWidth: '620px',
              lineHeight: 1.5,
              marginBottom: '6px',
            }}
          >
            Discover the role-stratified regressions, walk-forward validation windows, and shadow MLOps infrastructure powering Lakers in 5.
          </p>

          {/* Action CTA */}
          <a
            href="/engine"
            onClick={handleClick}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '10px',
              backgroundColor: 'var(--editorial-ink)',
              color: 'var(--editorial-card)',
              fontFamily: 'var(--font-display)',
              fontSize: '0.95rem',
              fontWeight: 700,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              padding: '13px 26px',
              borderRadius: 'var(--radius-sm)',
              textDecoration: 'none',
              boxShadow: '0 4px 14px rgba(33, 30, 25, 0.15)',
              transition: 'all 200ms ease',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--editorial-terracotta)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--editorial-ink)';
              e.currentTarget.style.transform = 'none';
            }}
          >
            Explore the Engine <span>→</span>
          </a>
        </div>
      </div>
    </section>
  );
}
