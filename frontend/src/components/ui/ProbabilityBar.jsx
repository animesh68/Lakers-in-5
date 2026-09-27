import React from 'react';

export default function ProbabilityBar({ 
  homeProb = 0.5, 
  awayProb = 0.5, 
  homeLabel = 'Home', 
  awayLabel = 'Away',
  isHomeLakers = false,
  isAwayLakers = false,
  height = 10 
}) {
  const homePercent = Math.round(homeProb * 100);
  const awayPercent = Math.round(awayProb * 100);

  const homeColor = isHomeLakers ? 'var(--gold-primary)' : 'rgba(255, 255, 255, 0.4)';
  const awayColor = isAwayLakers ? 'var(--gold-primary)' : '#475569';

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <div style={{
        width: '100%',
        height: `${height}px`,
        background: 'rgba(255, 255, 255, 0.06)',
        borderRadius: `${height / 2}px`,
        overflow: 'hidden',
        display: 'flex'
      }}>
        <div 
          style={{ 
            width: `${homePercent}%`, 
            background: homeColor, 
            transition: 'width 0.4s ease' 
          }} 
        />
        <div 
          style={{ 
            width: `${awayPercent}%`, 
            background: awayColor, 
            transition: 'width 0.4s ease' 
          }} 
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 600 }}>
        <span style={{ color: isHomeLakers ? 'var(--gold-primary)' : 'var(--text-secondary)' }}>
          {homeLabel}: {homePercent}%
        </span>
        <span style={{ color: isAwayLakers ? 'var(--gold-primary)' : 'var(--text-secondary)' }}>
          {awayLabel}: {awayPercent}%
        </span>
      </div>
    </div>
  );
}
