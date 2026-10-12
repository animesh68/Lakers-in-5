import React from 'react';

export default function ProbabilityBar({ 
  awayProb = 0.5, 
  homeProb = 0.5, 
  awayLabel = 'Away',
  homeLabel = 'Home', 
  isAwayLakers = false,
  isHomeLakers = false,
  height = 10 
}) {
  const awayPercent = Math.round(awayProb * 100);
  const homePercent = Math.round(homeProb * 100);

  const awayColor = isAwayLakers ? 'var(--gold-primary)' : 'rgba(255, 255, 255, 0.4)';
  const homeColor = isHomeLakers ? 'var(--gold-primary)' : '#475569';

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
        {/* Left segment = Away */}
        <div 
          style={{ 
            width: `${awayPercent}%`, 
            background: awayColor, 
            transition: 'width 0.4s ease' 
          }} 
        />
        {/* Right segment = Home */}
        <div 
          style={{ 
            width: `${homePercent}%`, 
            background: homeColor, 
            transition: 'width 0.4s ease' 
          }} 
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 600 }}>
        {/* Left = Away */}
        <span style={{ color: isAwayLakers ? 'var(--gold-primary)' : 'var(--text-secondary)' }}>
          {awayLabel}: {awayPercent}%
        </span>
        {/* Right = Home */}
        <span style={{ color: isHomeLakers ? 'var(--gold-primary)' : 'var(--text-secondary)' }}>
          {homeLabel}: {homePercent}%
        </span>
      </div>
    </div>
  );
}
