import { Inter } from 'next/font/google';
import { fetchEvents, fetchBlindspots } from '@/lib/api';
import Link from 'next/link';
import Image from 'next/image';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700', '800'] });

const t = {
  en: {
    home: "Home",
    blindspot: "Blindspot",
    sources: "Sources",
    search: "Search...",
    date: "Date",
    location: "Tamil Nadu, India",
    trending: "Trending Topics",
    noTrending: "No trending tags found",
    dailyBriefing: "Daily Briefing",
    stories: "stories",
    articles: "articles",
    noEvents: "No events",
    breakingNews: "Breaking News",
    noBreaking: "No breaking news",
    blindspotTitle: "Blindspot",
    blindspotDesc: "Stories disproportionately covered by one side of the political spectrum.",
    noBlindspots: "No active blindspots",
    maxGap: "Max gap"
  },
  ta: {
    home: "முகப்பு",
    blindspot: "கண்பார்வைக்கு அப்பால்",
    sources: "ஆதாரங்கள்",
    search: "தேடல்...",
    date: "தேதி",
    location: "தமிழ்நாடு, இந்தியா",
    trending: "டிரெண்டிங்",
    noTrending: "டிரெண்டிங் இல்லை",
    dailyBriefing: "தினசரி சுருக்கம்",
    stories: "செய்திகள்",
    articles: "கட்டுரைகள்",
    noEvents: "செய்திகள் இல்லை",
    breakingNews: "முக்கிய செய்திகள்",
    noBreaking: "முக்கிய செய்திகள் இல்லை",
    blindspotTitle: "கண்பார்வைக்கு அப்பால்",
    blindspotDesc: "அரசியல் களத்தின் ஒரு தரப்பினரால் மட்டுமே அதிக முக்கியத்துவம் கொடுத்து செய்தியாக்கப்பட்டவை.",
    noBlindspots: "கண்பார்வைக்கு எட்டாத பகுதி இல்லை",
    maxGap: "அதிகபட்ச இடைவெளி"
  }
};

export default async function Home({ searchParams }) {
  const lang = searchParams?.lang === 'ta' ? 'ta' : 'en';
  const selectedTag = searchParams?.tag || null;
  const strings = t[lang];

  let events = [];
  let blindspotsData = { blindspots: [] };

  try {
    events = await fetchEvents(lang);
    if (selectedTag) {
      events = events.filter(e => e.tags && e.tags.includes(selectedTag));
    }
  } catch (err) {
    console.error("Error fetching events:", err);
  }

  try {
    blindspotsData = await fetchBlindspots();
  } catch (err) {
    console.error("Error fetching blindspots:", err);
  }

  const blindspots = blindspotsData.blindspots || [];

  // Separate events for middle (hero) and left (daily briefings)
  const heroEvent = events.length > 0 ? events[0] : null;
  const briefingEvents = events.length > 1 ? events.slice(1, 15) : []; // Show up to 14 events

  // Extract trending tags from all events
  const allTags = events.flatMap(e => e.tags || []);
  const uniqueTags = [...new Set(allTags)].slice(0, 8);

  // Use a stable string for the date to prevent Hydration Error
  const formattedDate = "Today's Edition";

  return (
    <div
      className={inter.className}
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#f7f5ef',
        color: '#171717',
        fontFamily: 'Inter, sans-serif',
        fontWeight: 600,
      }}
    >
      {/* Header */}
      <nav
        style={{
          display: 'flex',
          alignItems: 'center',
          minHeight: '64px',
          padding: '0 32px',
          borderBottom: '1px solid #d8d5ce',
          gap: '28px',
          backgroundColor: '#f7f5ef',
        }}
      >
        <Link
          href={`/?lang=${lang}`}
          style={{
            color: '#171717',
            textDecoration: 'none',
            fontSize: '1.25rem',
            fontWeight: 800,
            letterSpacing: '-0.04em',
            whiteSpace: 'nowrap',
          }}
        >
          PERSPECTIVE LENS
        </Link>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            fontSize: '0.9rem',
            fontWeight: 600,
            height: '64px',
          }}
        >
          <Link
            href={`/?lang=${lang}`}
            style={{
              color: '#171717',
              textDecoration: 'none',
              padding: '22px 18px 20px',
              borderBottom: '2px solid #171717',
            }}
          >
            {strings.home}
          </Link>
          <Link
            href={`/blindspots?lang=${lang}`}
            style={{
              color: '#66635d',
              textDecoration: 'none',
              padding: '22px 18px 20px',
            }}
          >
            {strings.blindspot}
          </Link>
          <Link
            href={`/sources?lang=${lang}`}
            style={{
              color: '#66635d',
              textDecoration: 'none',
              padding: '22px 18px 20px',
            }}
          >
            {strings.sources}
          </Link>
        </div>

        <div style={{ flex: 1 }} />

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '22px',
            color: '#5f5c56',
            fontSize: '0.78rem',
            whiteSpace: 'nowrap',
          }}
        >
          <span>{formattedDate}</span>
          <span style={{ color: '#b9b5ad' }}>|</span>
          <span>{strings.location}</span>
          <span style={{ color: '#b9b5ad' }}>|</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link
              href="?lang=en"
              style={{
                color: lang === 'en' ? '#171717' : '#9b9892',
                fontWeight: 700,
                textDecoration: 'none',
              }}
            >
              EN
            </Link>
            <Link
              href="?lang=ta"
              style={{
                color: lang === 'ta' ? '#171717' : '#9b9892',
                fontWeight: 700,
                textDecoration: 'none',
              }}
            >
              தமிழ்
            </Link>
          </div>
        </div>
      </nav>

      {/* Trending — Ground News style: restrained row with a rule above and below */}
      <section
        style={{
          borderBottom: '1px solid #d8d5ce',
          backgroundColor: '#f7f5ef',
          borderTop: '1px solid #d8d5ce',
          padding: '18px 32px 17px',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
            overflowX: 'auto',
            whiteSpace: 'nowrap',
          }}
        >
          <span
            style={{
              fontSize: '0.78rem',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: '#171717',
            }}
          >
            {strings.trending}
          </span>

          <div style={{ width: '1px', height: '18px', backgroundColor: '#c9c5bd', flexShrink: 0 }} />

          {uniqueTags.length > 0 ? (
            uniqueTags.map(tag => (
              <Link
                href={`/?tag=${encodeURIComponent(tag)}&lang=${lang}`}
                key={tag}
                style={{
                  textDecoration: 'none',
                  color: selectedTag === tag ? '#171717' : '#625f59',
                  fontSize: '0.82rem',
                  fontWeight: selectedTag === tag ? 800 : 600,
                }}
              >
                {tag}
                {selectedTag === tag && <span style={{ marginLeft: '5px' }}>×</span>}
              </Link>
            ))
          ) : (
            <span style={{ color: '#8a8780', fontSize: '0.82rem' }}>{strings.noTrending}</span>
          )}
        </div>
      </section>

      {/* Main newspaper-style grid */}
      <main
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(240px, 1fr) minmax(420px, 2.05fr) minmax(250px, 1fr)',
          maxWidth: '1440px',
          width: '100%',
          margin: '0 auto',
          padding: '30px 32px 48px',
          flex: 1,
          alignItems: 'start',
          boxSizing: 'border-box',
        }}
      >
        {/* LEFT — Daily Briefing */}
        <section
          style={{
            paddingRight: '28px',
            borderRight: '1px solid #d2cec6',
            minWidth: 0,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
              borderBottom: '2px solid #171717',
              paddingBottom: '10px',
              marginBottom: '4px',
            }}
          >
            <h2
              style={{
                fontSize: '1.05rem',
                fontWeight: 800,
                margin: 0,
                letterSpacing: '-0.02em',
              }}
            >
              {strings.dailyBriefing}
            </h2>
            <span style={{ fontSize: '0.7rem', color: '#77736c', fontWeight: 600 }}>
              {events.length} {strings.stories}
            </span>
          </div>

          <div
            style={{
              fontSize: '0.7rem',
              color: '#77736c',
              padding: '9px 0 15px',
              borderBottom: '1px solid #d8d5ce',
            }}
          >
            {events.length} {strings.stories} · {events.length * 3} {strings.articles}
          </div>

          {briefingEvents.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#77736c', padding: '32px 0' }}>
              {strings.noEvents}
            </div>
          ) : (
            briefingEvents.map(ev => (
              <article
                key={ev.id}
                style={{
                  display: 'flex',
                  gap: '13px',
                  padding: '16px 0',
                  borderBottom: '1px solid #dedbd4',
                }}
              >
                {ev.image_url && (
                  <div
                    style={{
                      width: '74px',
                      height: '58px',
                      flexShrink: 0,
                      position: 'relative',
                      overflow: 'hidden',
                    }}
                  >
                    <Image src={ev.image_url} alt={ev.title} fill style={{ objectFit: 'cover' }} />
                  </div>
                )}

                <div style={{ minWidth: 0 }}>
                  <Link href={`/events/${ev.id}?lang=${lang}`} style={{ textDecoration: 'none' }}>
                    <h3
                      style={{
                        fontSize: '0.88rem',
                        fontWeight: 700,
                        color: '#171717',
                        margin: 0,
                        lineHeight: 1.32,
                        letterSpacing: '-0.01em',
                      }}
                    >
                      {ev.title}
                    </h3>
                  </Link>

                  <div
                    style={{
                      marginTop: '7px',
                      fontSize: '0.68rem',
                      color: '#77736c',
                      display: 'flex',
                      gap: '7px',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                    }}
                  >
                    <span>{ev.article_count || ev.source_count * 2} {strings.articles}</span>
                    {ev.tags?.slice(0, 1).map(tag => (
                      <Link
                        href={`/?tag=${encodeURIComponent(tag)}&lang=${lang}`}
                        key={tag}
                        style={{ textDecoration: 'none', color: '#5f5c56' }}
                      >
                        #{tag}
                      </Link>
                    ))}
                  </div>
                </div>
              </article>
            ))
          )}
        </section>

        {/* CENTER — Breaking / Top Story */}
        <section
          style={{
            padding: '0 30px',
            minWidth: 0,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid #171717',
              paddingBottom: '10px',
              marginBottom: '18px',
            }}
          >
            <h2
              style={{
                fontSize: '1.05rem',
                fontWeight: 800,
                margin: 0,
                letterSpacing: '-0.02em',
              }}
            >
              {strings.breakingNews}
            </h2>
            <span
              style={{
                fontSize: '0.68rem',
                color: '#77736c',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              Top Story
            </span>
          </div>

          {heroEvent ? (
            <article>
              <div
                style={{
                  width: '100%',
                  height: '405px',
                  position: 'relative',
                  overflow: 'hidden',
                  backgroundColor: '#dedbd4',
                }}
              >
                <Image
                  src={heroEvent.image_url || 'https://images.unsplash.com/photo-1572949645841-094f3a9c4c94?q=80&w=1200&auto=format&fit=crop'}
                  alt={heroEvent.title}
                  fill
                  style={{ objectFit: 'cover' }}
                />

                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'linear-gradient(180deg, transparent 40%, rgba(0,0,0,0.82) 100%)',
                  }}
                />

                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    right: 0,
                    bottom: 0,
                    padding: '34px 28px 24px',
                  }}
                >
                  <Link href={`/events/${heroEvent.id}?lang=${lang}`} style={{ textDecoration: 'none' }}>
                    <h1
                      style={{
                        fontSize: 'clamp(1.55rem, 3vw, 2.35rem)',
                        fontWeight: 800,
                        color: '#fff',
                        margin: '0 0 20px',
                        lineHeight: 1.12,
                        letterSpacing: '-0.035em',
                      }}
                    >
                      {heroEvent.title}
                    </h1>
                  </Link>

                  {/* Ground News-style bias bar */}
                  <div
                    style={{
                      display: 'flex',
                      width: '100%',
                      height: '7px',
                      overflow: 'hidden',
                      marginBottom: '9px',
                      backgroundColor: 'rgba(255,255,255,0.25)',
                    }}
                    aria-label="Coverage distribution"
                  >
                    <div style={{ width: '45%', backgroundColor: '#c9362b' }} title="Left 45%" />
                    <div style={{ width: '30%', backgroundColor: '#f4f1e9' }} title="Center 30%" />
                    <div style={{ width: '25%', backgroundColor: '#3567b7' }} title="Right 25%" />
                  </div>

                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      fontSize: '0.72rem',
                      color: '#fff',
                      lineHeight: 1.2,
                    }}
                  >
                    <span>Left 45%</span>
                    <span style={{ textAlign: 'center' }}>Center 30%</span>
                    <span style={{ textAlign: 'right' }}>Right 25%</span>
                  </div>
                </div>
              </div>

              {/* Perspective labels — separated like Ground's comparison UI */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  borderBottom: '1px solid #d2cec6',
                  borderLeft: '1px solid #d2cec6',
                  marginTop: '16px',
                }}
              >
                {[
                  ['Left', '#c9362b'],
                  ['Center', '#77736c'],
                  ['Right', '#3567b7'],
                  ['Independent', '#171717'],
                ].map(([label, color], index) => (
                  <div
                    key={label}
                    style={{
                      padding: '11px 10px',
                      borderRight: '1px solid #d2cec6',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      color: '#3f3c37',
                      textAlign: 'center',
                    }}
                  >
                    <span
                      style={{
                        display: 'inline-block',
                        width: '7px',
                        height: '7px',
                        borderRadius: '50%',
                        backgroundColor: color,
                        marginRight: '6px',
                      }}
                    />
                    {label}
                  </div>
                ))}
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '12px',
                  padding: '13px 0',
                  fontSize: '0.7rem',
                  color: '#77736c',
                  borderBottom: '1px solid #d2cec6',
                }}
              >
                <span>{heroEvent.tags?.[0] || 'Tamil Nadu'}</span>
                <span>{heroEvent.source_count || 0} sources</span>
              </div>
            </article>
          ) : (
            <div
              style={{
                color: '#77736c',
                padding: '50px 20px',
                textAlign: 'center',
                border: '1px solid #d2cec6',
                backgroundColor: '#f7f5ef',
              }}
            >
              {strings.noBreaking}
            </div>
          )}
        </section>

        {/* RIGHT — Blindspot */}
        <section
          style={{
            paddingLeft: '28px',
            borderLeft: '1px solid #d2cec6',
            minWidth: 0,
          }}
        >
          <div
            style={{
              borderBottom: '2px solid #171717',
              paddingBottom: '10px',
              marginBottom: '12px',
            }}
          >
            <h2
              style={{
                fontSize: '1.05rem',
                fontWeight: 800,
                color: '#171717',
                margin: 0,
                letterSpacing: '-0.02em',
              }}
            >
              Blindspot
            </h2>
          </div>

          <p
            style={{
              fontSize: '0.73rem',
              color: '#77736c',
              margin: '0 0 18px',
              lineHeight: 1.45,
              fontWeight: 600,
            }}
          >
            {strings.blindspotDesc}
          </p>

          {blindspots.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                color: '#77736c',
                padding: '24px 12px',
                border: '1px solid #d2cec6',
              }}
            >
              {strings.noBlindspots}
            </div>
          ) : (
            blindspots.slice(0, 2).map((bs, i) => {
              const relatedEvent = events.find(e => e.id === bs.event_id);

              return (
                <article
                  key={i}
                  style={{
                    borderBottom: '1px solid #d2cec6',
                    paddingBottom: '18px',
                    marginBottom: '18px',
                  }}
                >
                  <div
                    style={{
                      position: 'relative',
                      width: '100%',
                      height: '145px',
                      overflow: 'hidden',
                      backgroundColor: '#dedbd4',
                    }}
                  >
                    <Image
                      src={relatedEvent?.image_url || 'https://images.unsplash.com/photo-1572949645841-094f3a9c4c94?q=80&w=800&auto=format&fit=crop'}
                      alt="Blindspot image"
                      fill
                      style={{ objectFit: 'cover' }}
                    />
                  </div>

                  <div style={{ paddingTop: '12px' }}>
                    <div
                      style={{
                        display: 'inline-block',
                        color: '#77736c',
                        fontSize: '0.65rem',
                        fontWeight: 800,
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        marginBottom: '8px',
                      }}
                    >
                      Blindspot
                    </div>

                    <Link href={`/events/${bs.event_id}?lang=${lang}`} style={{ textDecoration: 'none' }}>
                      <h3
                        style={{
                          fontSize: '0.92rem',
                          fontWeight: 700,
                          color: '#171717',
                          margin: 0,
                          lineHeight: 1.3,
                          letterSpacing: '-0.015em',
                        }}
                      >
                        {bs.event_title || bs.description}
                      </h3>
                    </Link>

                    <div
                      style={{
                        marginTop: '11px',
                        fontSize: '0.68rem',
                        color: '#9a342d',
                        fontWeight: 700,
                      }}
                    >
                      {strings.maxGap}: {bs.source_group?.replace('_ORIENTED', '')}
                    </div>
                  </div>
                </article>
              );
            })
          )}
        </section>
      </main>
    </div>
  );
}