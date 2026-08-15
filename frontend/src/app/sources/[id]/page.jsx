import { fetchSource } from '@/lib/api';
import Link from 'next/link';

export default async function SourcePage({ params }) {
  const { id } = await params;
  let source = null;

  try {
    source = await fetchSource(id);
  } catch (err) {
    console.error(err);
    return <div style={{ color: 'var(--color-negative)', padding: '2rem' }}>Failed to load source details.</div>;
  }

  return (
    <main style={{ maxWidth: '1200px', margin: '0 auto', padding: 'var(--spacing-container)' }}>
      <header style={{ marginBottom: '32px' }}>
        <Link href="/" style={{ color: 'var(--brand-primary)', fontWeight: 600, fontSize: '0.9rem', marginBottom: '16px', display: 'inline-block' }}>
          ← Back to Events
        </Link>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, lineHeight: 1.3, marginBottom: '8px', color: 'var(--text-primary)' }}>
          {source.name}
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
          {source.domain}
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '24px', color: 'var(--text-primary)' }}>
            Editorial Profile
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Primary Orientation
              </div>
              <div style={{ display: 'inline-block' }} className="badge">
                <span style={{
                  color: `var(--color-${source.orientation?.toLowerCase().replace('_oriented', '') || 'neutral'})`,
                  fontWeight: 700,
                  fontSize: '1.1rem'
                }}>
                  {source.orientation?.replace('_ORIENTED', '') || 'Unknown'}
                </span>
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Orientation Confidence
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                background: 'var(--bg-surface-hover)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${(source.orientation_confidence || 0) * 100}%`,
                  height: '100%',
                  background: 'var(--brand-gradient)'
                }} />
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'right' }}>
                {Math.round((source.orientation_confidence || 0) * 100)}%
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Classification Evidence
              </div>
              <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                "{source.orientation_evidence || 'Algorithmically derived from historical framing analysis.'}"
              </p>
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '24px', color: 'var(--text-primary)' }}>
            Transparency & Ownership
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Parent Company / Owner
              </div>
              <p style={{ fontSize: '1.05rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                {source.ownership?.parent_company || 'Unknown / Independent'}
              </p>
            </div>

            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Political Affiliation
              </div>
              <p style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                {source.ownership?.political_affiliation || 'None declared'}
              </p>
            </div>

            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Reliability Rating
              </div>
              <div className="badge" style={{ display: 'inline-block', backgroundColor: 'var(--bg-surface-hover)', color: 'var(--text-primary)' }}>
                {source.reliability?.rating || 'Unrated'}
              </div>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                {source.reliability?.notes || 'Insufficient data to compute reliability profile.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
