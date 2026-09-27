import React from 'react';

export default function StatusBadge({ variant = 'neutral', children, icon: Icon, style }) {
  const variantClass = {
    gold: 'badge-gold',
    purple: 'badge-purple',
    success: 'badge-success',
    danger: 'badge-danger',
    neutral: 'badge-neutral',
  }[variant] || 'badge-neutral';

  return (
    <span className={`badge ${variantClass}`} style={style}>
      {Icon && <Icon size={12} />}
      {children}
    </span>
  );
}
