import React from 'react';

export default function MetricCard({ label, value, subtext, badge, statusColor, tooltip }) {
  return (
    <div className="panel-subtle" style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
          {label}
        </span>
        {badge}
      </div>

      <div style={{ 
        fontSize: '1.4rem', 
        fontWeight: 800, 
        fontFamily: 'var(--font-display)', 
        color: statusColor || 'var(--text-primary)',
        letterSpacing: '-0.02em'
      }}>
        {value}
      </div>

      {subtext && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.3 }}>
          {subtext}
        </div>
      )}
    </div>
  );
}
