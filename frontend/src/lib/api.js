const API_URL = process.env.API_URL || 'http://api:8000';

export async function fetchEvents(lang = 'en') {
  const res = await fetch(`${API_URL}/events/?lang=${lang}`, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function fetchEvent(id, lang = 'en') {
  const res = await fetch(`${API_URL}/events/${id}?lang=${lang}`, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error('Failed to fetch event details');
  return res.json();
}

export async function fetchBlindspots(eventId = null, lang = 'en') {
  const url = eventId 
    ? `${API_URL}/events/${eventId}/blindspots?lang=${lang}`
    : `${API_URL}/blindspots/?lang=${lang}`;
    
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Failed to fetch blindspots');
  return res.json();
}

export async function fetchMatrix(eventId, lang = 'en') {
  const res = await fetch(`${API_URL}/events/${eventId}/matrix?lang=${lang}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Failed to fetch perspective matrix');
  return res.json();
}

export async function fetchSources() {
  const res = await fetch(`${API_URL}/sources`, { next: { revalidate: 3600 } });
  if (!res.ok) throw new Error('Failed to fetch sources');
  return res.json();
}

export async function fetchSource(id) {
  const res = await fetch(`${API_URL}/sources/${id}`, { next: { revalidate: 3600 } });
  if (!res.ok) throw new Error('Failed to fetch source details');
  return res.json();
}
