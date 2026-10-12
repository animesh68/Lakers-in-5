import React, { useState, useEffect } from 'react';

export default function Header({ currentRoute = '/', activeSection, onNavigate }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { label: 'GAMES', target: 'next-game', route: '/' },
    { label: 'PLAYERS', target: 'player-projections', route: '/' },
    { label: 'SCHEDULE', target: 'schedule', route: '/' },
    { label: 'ENGINE', target: 'engine', route: '/engine' },
  ];

  const handleNavClick = (route, targetId) => {
    setMobileMenuOpen(false);
    if (onNavigate) {
      onNavigate(route, targetId);
    } else {
      if (route === '/engine') {
        window.history.pushState({}, '', '/engine');
        window.dispatchEvent(new PopStateEvent('popstate'));
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        window.history.pushState({}, '', '/');
        window.dispatchEvent(new PopStateEvent('popstate'));
        if (targetId) {
          setTimeout(() => {
            const el = document.getElementById(targetId);
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }, 50);
        }
      }
    }
  };

  return (
    <header
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        backgroundColor: scrolled ? 'rgba(18, 16, 21, 0.94)' : 'rgba(18, 16, 21, 0.65)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderBottom: `1px solid ${scrolled ? 'rgba(255, 255, 255, 0.12)' : 'rgba(255, 255, 255, 0.06)'}`,
        transition: 'all 300ms ease',
        padding: '14px 0',
      }}
    >
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Brand / Logo */}
        <a
          href="/"
          onClick={(e) => {
            e.preventDefault();
            handleNavClick('/', 'hero');
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            textDecoration: 'none',
            color: '#FFFFFF',
          }}
        >
          <img 
            src="/imgs/Los_Angeles_Lakers_logo.svg.webp" 
            alt="Lakers Logo" 
            style={{ width: '32px', height: '22px', objectFit: 'contain' }}
          />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              className="font-display"
              style={{
                fontSize: '1.45rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                lineHeight: 1,
                color: '#FFFFFF',
              }}
            >
              LAKERS IN 5
            </span>
          </div>
        </a>

        {/* Desktop Navigation Links */}
        <nav
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '32px',
          }}
          className="desktop-nav"
        >
          {navItems.map((item) => {
            const isActive = item.target === 'engine'
              ? currentRoute === '/engine'
              : (currentRoute === '/' && activeSection === item.target);

            return (
              <button
                key={item.target}
                onClick={() => handleNavClick(item.route, item.target)}
                className="font-display"
                style={{
                  background: 'none',
                  border: 'none',
                  color: isActive ? 'var(--gold-accent)' : '#C9C4D0',
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  letterSpacing: '0.1em',
                  cursor: 'pointer',
                  position: 'relative',
                  padding: '6px 0',
                  transition: 'color 200ms ease',
                }}
              >
                {item.label}
                {isActive && (
                  <span
                    style={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      height: '2px',
                      backgroundColor: 'var(--gold-accent)',
                      borderRadius: '2px',
                    }}
                  />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right CTA */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={() => handleNavClick('/', 'next-game')}
            className="btn-primary"
            style={{
              padding: '8px 18px',
              fontSize: '0.85rem',
              display: 'inline-flex',
            }}
          >
            NEXT GAME →
          </button>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="mobile-menu-btn"
            aria-label="Toggle navigation menu"
            style={{
              display: 'none',
              background: 'none',
              border: 'none',
              color: '#FFFFFF',
              fontSize: '1.5rem',
              cursor: 'pointer',
              padding: '4px',
            }}
          >
            {mobileMenuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: 'rgba(18, 16, 21, 0.98)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          {navItems.map((item) => {
            const isActive = item.target === 'engine'
              ? currentRoute === '/engine'
              : (currentRoute === '/' && activeSection === item.target);

            return (
              <button
                key={item.target}
                onClick={() => handleNavClick(item.route, item.target)}
                className="font-display"
                style={{
                  background: 'none',
                  border: 'none',
                  color: isActive ? 'var(--gold-accent)' : '#FFFFFF',
                  fontSize: '1.2rem',
                  textAlign: 'left',
                  padding: '8px 0',
                  cursor: 'pointer',
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .desktop-nav {
            display: none !important;
          }
          .mobile-menu-btn {
            display: block !important;
          }
        }
      `}</style>
    </header>
  );
}
