import React, { useState } from 'react';
import { X, Server, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { getStoredApiUrl, setStoredApiUrl } from '../api';

export default function SettingsModal({ isOpen, onClose, apiStatus, onRecheck }) {
  const [customUrl, setCustomUrl] = useState(getStoredApiUrl());
  const [saveMessage, setSaveMessage] = useState(null);

  if (!isOpen) return null;

  const handleSave = (e) => {
    e.preventDefault();
    setStoredApiUrl(customUrl);
    setSaveMessage("API URL saved successfully.");
    onRecheck();
    setTimeout(() => setSaveMessage(null), 3000);
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 100,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="panel" style={{
        width: '100%',
        maxWidth: '480px',
        padding: '28px',
        background: '#120E1C',
        border: '1px solid var(--border-medium)',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Server size={20} color="var(--gold-primary)" />
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Connection & Settings</h3>
          </div>
          <button 
            onClick={onClose}
            className="btn btn-ghost"
            style={{ padding: '6px', borderRadius: 'var(--radius-xs)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Status Box */}
        <div className="panel-subtle" style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {apiStatus.online ? (
              <CheckCircle2 size={18} color="var(--emerald-success)" />
            ) : (
              <AlertCircle size={18} color="var(--rose-danger)" />
            )}
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                {apiStatus.online ? 'Connected to Inference API' : 'Connection Offline'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {apiStatus.online ? `Latency: ${apiStatus.latency}ms` : (apiStatus.error || 'Cannot reach API')}
              </div>
            </div>
          </div>

          <button 
            onClick={onRecheck}
            disabled={apiStatus.checking}
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.75rem' }}
          >
            <RefreshCw size={12} className={apiStatus.checking ? 'spin' : ''} />
            Check
          </button>
        </div>

        {/* API URL Config Form */}
        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 600 }}>
              Backend API Base URL
            </label>
            <input 
              type="text"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              placeholder="Leave empty for same-origin (default)"
              style={{ width: '100%', padding: '10px 14px', borderRadius: 'var(--radius-sm)' }}
            />
            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Default is empty string (serves directly from `/`).
            </p>
          </div>

          {saveMessage && (
            <div style={{ fontSize: '0.8rem', color: 'var(--emerald-success)', fontWeight: 600 }}>
              {saveMessage}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '6px' }}>
            <button 
              type="button" 
              onClick={onClose}
              className="btn btn-secondary"
            >
              Close
            </button>
            <button 
              type="submit" 
              className="btn btn-gold"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
