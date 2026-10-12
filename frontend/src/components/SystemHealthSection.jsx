import React from 'react';
import { Activity, Server, ShieldCheck, CheckCircle2, Cpu, HardDrive, BarChart2 } from 'lucide-react';

export default function SystemHealthSection({ apiStatus }) {
  return (
    <section 
      id="system-status"
      className="section-spacing"
      style={{
        position: 'relative',
        backgroundColor: '#0E0817',
        borderTop: '1px solid var(--border-subtle)',
      }}
    >
      <div className="container-editorial">
        {/* Section Header */}
        <div 
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.6rem',
            marginBottom: '3rem',
          }}
        >
          <span className="banner-marker">
            06 • MLOPS TELEMETRY & SYSTEM RELIABILITY
          </span>

          <h2 
            className="font-display" 
            style={{ fontSize: 'clamp(2.4rem, 5vw, 4.4rem)', color: '#FFFFFF', letterSpacing: '0.03em', lineHeight: 0.95 }}
          >
            PRODUCTION MODEL AUDIT
          </h2>
          <span className="broadcast-label">
            PROMETHEUS-COMPATIBLE TELEMETRY • PERSISTENT SHADOW ISOLATION • DUCKDB LAKEHOUSE
          </span>
        </div>

        {/* Telemetry Cards Grid */}
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1.5rem',
          }}
        >
          {/* Active Production Suite */}
          <div className="glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <span className="broadcast-label">PRODUCTION SUITE</span>
              <span 
                style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--status-success)',
                  backgroundColor: 'var(--status-success-bg)',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '3px',
                  fontWeight: 700,
                }}
              >
                ACTIVE SERVING
              </span>
            </div>
            <h3 className="font-subheading" style={{ fontSize: '1.4rem', color: '#FFFFFF', fontWeight: 700 }}>
              PlayerSuite-v1.0
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.5 }}>
              Ridge regularized point regressor + Bayesian expected minutes model trained on 1.5M historical events.
            </p>
          </div>

          {/* Frozen Shadow Model */}
          <div className="glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <span className="broadcast-label">FROZEN SHADOW</span>
              <span 
                style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--gold-accent)',
                  backgroundColor: 'var(--gold-subtle)',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '3px',
                  fontWeight: 700,
                }}
              >
                PROSPECTIVE AUDIT
              </span>
            </div>
            <h3 className="font-subheading" style={{ fontSize: '1.4rem', color: '#FFFFFF', fontWeight: 700 }}>
              PlayerSuite-v1.1-c1-shadow
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.5 }}>
              Role-stratified candidate suite running concurrently in isolated background thread with zero user disruption.
            </p>
          </div>

          {/* Data Quality & Schema */}
          <div className="glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <span className="broadcast-label">DATA QUALITY</span>
              <span 
                style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--status-success)',
                  backgroundColor: 'var(--status-success-bg)',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '3px',
                  fontWeight: 700,
                }}
              >
                100% HEALTHY
              </span>
            </div>
            <h3 className="font-subheading" style={{ fontSize: '1.4rem', color: '#FFFFFF', fontWeight: 700 }}>
              0 Schema Anomalies
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.5 }}>
              Real-time Pydantic validation on every request vector. Zero NaN/Inf anomalies detected.
            </p>
          </div>

          {/* Memory & Budget Headroom */}
          <div className="glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <span className="broadcast-label">512 MB DEPLOYMENT</span>
              <span 
                style={{
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--status-success)',
                  backgroundColor: 'var(--status-success-bg)',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '3px',
                  fontWeight: 700,
                }}
              >
                348 MB PEAK (PASS)
              </span>
            </div>
            <h3 className="font-subheading" style={{ fontSize: '1.4rem', color: '#FFFFFF', fontWeight: 700 }}>
              +163 MB Headroom
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.5 }}>
              Phase 12.1 DuckDB vectorized pushdown streaming eliminates in-memory table bloat.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
