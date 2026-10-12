import React, { useState, useEffect } from 'react';
import { FOOTER_SLIDES } from '../utils/footerSlides';

export default function Footer() {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % FOOTER_SLIDES.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <footer
      style={{
        backgroundColor: '#09070D',
        color: '#FFFFFF',
        position: 'relative',
        overflow: 'hidden',
        width: '100%',
      }}
    >
      {/* =========================================================================
          FULL-BLEED CINEMATIC IMAGE SLIDESHOW (Viewport Edge to Edge)
          ========================================================================= */}
      <div
        className="footer-scene"
        style={{
          position: 'relative',
          height: 'clamp(540px, 75vh, 850px)',
          width: '100%',
          overflow: 'hidden',
          backgroundColor: '#09070D',
        }}
      >
        {FOOTER_SLIDES.map((slide, idx) => {
          const isActive = idx === currentIndex;
          return (
            <div
              key={slide.id || slide.image}
              style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                opacity: isActive ? 1 : 0,
                transition: 'opacity 1000ms ease-in-out',
                pointerEvents: isActive ? 'auto' : 'none',
                overflow: 'hidden',
              }}
            >
              {/* Full-Bleed Editorial Sports Photo (Edge-to-Edge) */}
              <img
                src={slide.image}
                alt="Lakers in 5 Showcase"
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  objectPosition: slide.position || 'center 35%',
                  transform: isActive ? 'scale(1.03)' : 'scale(1.0)',
                  transition: 'transform 5500ms cubic-bezier(0.16, 1, 0.3, 1)',
                  pointerEvents: 'none',
                }}
                loading={idx < 2 ? 'eager' : 'lazy'}
              />

              {/* Dark Gradient Vignette for Readability */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: 'linear-gradient(180deg, rgba(9, 7, 13, 0.45) 0%, rgba(9, 7, 13, 0.05) 35%, rgba(9, 7, 13, 0.75) 75%, #09070D 100%)',
                  pointerEvents: 'none',
                }}
              />
            </div>
          );
        })}

        {/* =======================================================================
            FIXED OVERLAY QUOTE: "OKC KFC, LAKERS IN 5" (Consistent Across Every Slide)
            ======================================================================= */}
        <div
          className="container"
          style={{
            position: 'absolute',
            bottom: '36px',
            left: 0,
            right: 0,
            zIndex: 10,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            <div
              className="section-eyebrow light"
              style={{
                fontSize: '0.85rem',
                letterSpacing: '0.22em',
                marginBottom: '8px',
                color: 'var(--gold-accent, #FDB927)',
                textShadow: '0 2px 8px rgba(0,0,0,0.85)',
              }}
            >
              SHOWTIME EDITION · 2026–27
            </div>
            {/* The exact fixed quote required: OKC KFC, LAKERS IN 5 */}
            <div
              className="font-display"
              style={{
                fontSize: 'clamp(2.4rem, 5.5vw, 4.4rem)',
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1,
                textShadow: '0 4px 24px rgba(0, 0, 0, 0.95), 0 2px 10px rgba(0, 0, 0, 0.8)',
                letterSpacing: '0.03em',
                textTransform: 'uppercase',
              }}
            >
              OKC KFC, <span style={{ color: 'var(--gold-accent, #FDB927)' }}>LAKERS IN 5</span>
            </div>
          </div>

          {/* Slide Indicator Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
            {FOOTER_SLIDES.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIndex(idx)}
                aria-label={`Go to slide ${idx + 1}`}
                style={{
                  width: idx === currentIndex ? '32px' : '8px',
                  height: '6px',
                  borderRadius: '3px',
                  backgroundColor: idx === currentIndex ? 'var(--gold-accent, #FDB927)' : 'rgba(255, 255, 255, 0.35)',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 300ms ease',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.6)',
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* =========================================================================
          EDITORIAL FOOTER BOTTOM BAR
          ========================================================================= */}
      <div
        style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          padding: '36px 0 28px 0',
          backgroundColor: '#09070D',
        }}
      >
        <div className="container">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '24px',
              paddingBottom: '20px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            {/* Left: Lakers in 5 Brand */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <img
                src="/imgs/Los_Angeles_Lakers_logo.svg.webp"
                alt="Lakers Logo"
                style={{ width: '32px', height: '22px', objectFit: 'contain' }}
              />
              <div>
                <span className="font-display" style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '0.05em', color: '#FFFFFF', display: 'block', lineHeight: 1 }}>
                  LAKERS IN 5
                </span>
                <span style={{ fontSize: '0.8rem', color: '#A39DAE' }}>
                  THE GAME, BEFORE THE GAME.
                </span>
              </div>
            </div>

            {/* Right: NBA Logo & Metadata */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
              <img
                src="/imgs/nba-logo-on-transparent-background-free-vector.jpg"
                alt="NBA"
                style={{ height: '22px', width: 'auto', opacity: 0.8, borderRadius: '2px' }}
              />
              <span style={{ fontSize: '0.8rem', color: '#7E7688' }}>
                2026–27 REGULAR SEASON FORECASTS
              </span>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
              paddingTop: '20px',
              fontSize: '0.78rem',
              color: '#6E6878',
            }}
          >
            <span>© 2026 Lakers in 5 · Engineered by Animesh</span>
            <span>DATA-DRIVEN HOOPS INTELLIGENCE</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
