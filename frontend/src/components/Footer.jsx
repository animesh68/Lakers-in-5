import React from 'react';
import { ExternalLink } from 'lucide-react';

export default function Footer({ onOpenModelTab }) {
  return (
    <footer style={{
      marginTop: 'auto',
      borderTop: '1px solid var(--border-subtle)',
      padding: '24px',
      background: 'rgba(8, 6, 13, 0.6)',
      fontSize: '0.8rem',
      color: 'var(--text-muted)'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 700, color: 'var(--text-secondary)' }}>LAKERS IN 5</span>
          <span>·</span>
          <span>Deterministic NBA Game Prediction · 2026-27 Season</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <a 
            href="/docs" 
            target="_blank" 
            rel="noreferrer"
            style={{ color: 'var(--text-secondary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            API Docs <ExternalLink size={12} />
          </a>
          <a 
            href="https://github.com/animesh68/Lakers-in-5" 
            target="_blank" 
            rel="noreferrer"
            style={{ color: 'var(--text-secondary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            GitHub <ExternalLink size={12} />
          </a>
          <button
            onClick={onOpenModelTab}
            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8rem' }}
          >
            Model Architecture
          </button>
        </div>
      </div>
    </footer>
  );
}
