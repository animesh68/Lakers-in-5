import React from 'react';

export default function MemeSection() {
  return (
    <section
      id="personality"
      style={{
        backgroundColor: 'var(--surface-warm)',
        padding: '70px 0 80px 0',
        borderBottom: '1px solid var(--surface-warm-border)',
      }}
    >
      <div className="container" style={{ textAlign: 'center' }}>
        <div style={{ maxWidth: '640px', margin: '0 auto' }}>
          <div className="section-eyebrow">
            <span>●</span> CULTURE
          </div>
          <h2 className="section-title" style={{ fontSize: 'clamp(1.8rem, 3.5vw, 2.6rem)', marginBottom: '8px' }}>
            THE NUMBERS ARE SERIOUS.
          </h2>
          <p className="font-display" style={{ fontSize: '1.25rem', color: 'var(--purple-primary)', fontWeight: 700, letterSpacing: '0.08em', marginBottom: '28px' }}>
            THE PROJECT DOESN'T HAVE TO BE.
          </p>

          {/* Supplied Meme Asset */}
          <div
            style={{
              display: 'inline-block',
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
              boxShadow: 'var(--shadow-md)',
              border: '2px solid var(--surface-warm-border)',
              backgroundColor: '#FFFFFF',
              padding: '8px',
            }}
          >
            <img
              src="/imgs/shannon-sharpe-with-another-lakers-in-5-rhyme-meme.webp"
              alt="Lakers in 5 Meme"
              style={{
                maxWidth: '100%',
                maxHeight: '380px',
                borderRadius: 'var(--radius-md)',
                display: 'block',
                objectFit: 'contain',
              }}
              loading="lazy"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
