import { fetchSources } from '@/lib/api';
import Link from 'next/link';

const t = {
  en: {
    home: "Home",
    blindspot: "Blindspot",
    sources: "Sources",
    title: "Source Directory",
    desc: "Transparency, ownership, and historical editorial profiles of Tamil news publishers.",
    noData: "No sources available. Check database connection.",
    viewProfile: "View Profile →",
    unknown: "Unknown"
  },
  ta: {
    home: "முகப்பு",
    blindspot: "பார்வைக்குறைபாடு",
    sources: "ஆதாரங்கள்",
    title: "ஆதாரங்கள் அடைவு",
    desc: "தமிழ் செய்தி வெளியீட்டாளர்களின் வெளிப்படைத்தன்மை, உரிமை மற்றும் வரலாற்று தலையங்க விவரங்கள்.",
    noData: "ஆதாரங்கள் கிடைக்கவில்லை.",
    viewProfile: "விவரம் காண் →",
    unknown: "தெரியவில்லை"
  }
};

export default async function SourcesPage({ searchParams }) {
  const lang = searchParams?.lang === 'ta' ? 'ta' : 'en';
  const strings = t[lang];
  let data = { sources: [] };
  
  try {
    data = await fetchSources();
  } catch (err) {
    console.error(err);
  }
  
  const sources = data.sources || [];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f9fafb', fontFamily: 'var(--font-inter), sans-serif' }}>
      {/* Top Navigation */}
      <nav style={{ display: 'flex', alignItems: 'center', padding: '12px 32px', borderBottom: '1px solid #e5e7eb', gap: '24px', backgroundColor: '#fff' }}>
        <div style={{ fontWeight: 800, fontSize: '1.4rem', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ backgroundColor: '#111', color: '#fff', padding: '2px 8px', borderRadius: '4px' }}>PERSPECTIVE</span>
          <span>Lens</span>
        </div>
        <div style={{ display: 'flex', gap: '24px', fontSize: '0.9rem', fontWeight: 600 }}>
          <Link href={`/?lang=${lang}`} style={{ color: '#6b7280', paddingBottom: '4px', textDecoration: 'none' }}>{strings.home}</Link>
          <Link href={`/blindspots?lang=${lang}`} style={{ color: '#6b7280', paddingBottom: '4px', textDecoration: 'none' }}>{strings.blindspot}</Link>
          <Link href={`/sources?lang=${lang}`} style={{ color: '#111', borderBottom: '2px solid #111', paddingBottom: '4px', textDecoration: 'none' }}>{strings.sources}</Link>
          
          <div style={{ display: 'flex', gap: '8px', marginLeft: '16px', borderLeft: '1px solid #e5e7eb', paddingLeft: '16px' }}>
            <Link href="?lang=en" style={{ color: lang === 'en' ? '#111' : '#9ca3af', fontWeight: lang === 'en' ? 'bold' : 'normal', textDecoration: 'none' }}>EN</Link>
            <span style={{ color: '#d1d5db' }}>|</span>
            <Link href="?lang=ta" style={{ color: lang === 'ta' ? '#111' : '#9ca3af', fontWeight: lang === 'ta' ? 'bold' : 'normal', textDecoration: 'none' }}>தமிழ்</Link>
          </div>
        </div>
      </nav>

      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px', width: '100%' }}>
        <header style={{ marginBottom: '40px' }}>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#111', letterSpacing: '-0.02em', marginBottom: '8px' }}>
            {strings.title}
          </h1>
          <p style={{ color: '#6b7280', fontSize: '1.1rem' }}>
            {strings.desc}
          </p>
        </header>
        
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
          {sources.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280', gridColumn: '1 / -1', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#fff' }}>
              {strings.noData}
            </div>
          ) : (
            sources.map((source) => (
              <Link key={source.id} href={`/sources/${source.id}?lang=${lang}`} style={{ textDecoration: 'none' }}>
                <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                  <div>
                    <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#111', marginBottom: '4px' }}>
                      {source.name}
                    </h2>
                    <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>
                      {source.domain}
                    </div>
                  </div>
                  
                  <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ 
                      backgroundColor: '#f3f4f6',
                      color: '#374151',
                      border: '1px solid #d1d5db',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 'bold'
                    }}>
                      {source.orientation?.replace('_ORIENTED', '') || strings.unknown}
                    </span>
                    <span style={{ color: '#111', fontSize: '0.85rem', fontWeight: 600 }}>
                      {strings.viewProfile}
                    </span>
                  </div>
                </div>
              </Link>
            ))
          )}
        </section>
      </main>
    </div>
  );
}
