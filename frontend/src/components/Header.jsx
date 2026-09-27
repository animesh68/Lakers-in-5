import React from 'react';
import { Flame, Swords, Calendar, Cpu, Settings } from 'lucide-react';

export default function Header({ activeTab, onTabChange, isOnline, onOpenSettings }) {
  const tabs = [
    { id: 'forecast', label: 'Forecast', icon: Flame },
    { id: 'matchups', label: 'Matchups', icon: Swords },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'model', label: 'Model', icon: Cpu },
  ];

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      background: 'rgba(8, 6, 13, 0.88)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '12px 24px'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px'
      }}>
        {/* Brand */}
        <div 
          onClick={() => onTabChange('forecast')}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #552583, #7B3AB8)',
            border: '1.5px solid #FDB927',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(253, 185, 39, 0.2)'
          }}>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.15rem', color: '#FDB927' }}>
              L
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ 
              fontFamily: 'var(--font-display)', 
              fontWeight: 800, 
              fontSize: '1.15rem', 
              letterSpacing: '-0.02em', 
              color: '#FFFFFF' 
            }}>
              LAKERS IN 5
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.04em' }}>
              NBA PREDICTION ENGINE
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{
          display: 'flex',
          gap: '4px',
          background: 'rgba(255, 255, 255, 0.03)',
          padding: '4px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)'
        }}>
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 14px',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? 700 : 500,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  background: isActive ? 'var(--gold-primary)' : 'transparent',
                  color: isActive ? '#0c0817' : 'var(--text-secondary)'
                }}
              >
                <Icon size={15} color={isActive ? '#0c0817' : 'currentColor'} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Right Status & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.78rem',
            color: isOnline ? 'var(--text-secondary)' : 'var(--rose-danger)',
            fontWeight: 600
          }}>
            <div 
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: isOnline ? 'var(--emerald-success)' : 'var(--rose-danger)',
                boxShadow: isOnline ? '0 0 8px var(--emerald-success)' : 'none'
              }}
            />
            <span>{isOnline ? 'System Operational' : 'Offline'}</span>
          </div>

          <button
            onClick={onOpenSettings}
            title="Settings & Connection"
            className="btn btn-ghost"
            style={{ padding: '8px', borderRadius: 'var(--radius-xs)' }}
          >
            <Settings size={17} />
          </button>
        </div>
      </div>
    </header>
  );
}
