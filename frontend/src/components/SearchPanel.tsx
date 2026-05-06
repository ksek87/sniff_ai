import React, { useState, useEffect, useRef } from 'react';
import { SearchResult } from '../types/fragrance';
import { searchFragrances, fetchFamilies } from '../services/apiService';
import { useFetchOnMount } from '../hooks/useFetchOnMount';
import { toPercent } from '../utils/format';

const MIN_QUERY_LEN = 2;
const DEBOUNCE_MS = 300;

const SearchPanel: React.FC = () => {
  const families = useFetchOnMount(fetchFamilies, []);
  const [query, setQuery] = useState('');
  const [family, setFamily] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);

    const q = query.trim();
    if (q.length < MIN_QUERY_LEN) {
      setResults([]);
      setLoading(false);
      return;
    }

    let active = true;
    timerRef.current = setTimeout(() => {
      setLoading(true);
      searchFragrances(q, family || undefined)
        .then(data => { if (active) { setResults(data); setLoading(false); } })
        .catch(() => { if (active) { setResults([]); setLoading(false); } });
    }, DEBOUNCE_MS);

    return () => {
      active = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [query, family]);

  return (
    <section className="search-panel" aria-label="Search fragrances">
      <h3 className="section-heading">Explore Fragrances</h3>
      <div className="search-controls">
        <input
          className="search-input"
          type="search"
          placeholder="Search by description, mood, or ingredient…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          aria-label="Search fragrances"
        />
        {families.length > 0 && (
          <select
            className="family-filter"
            value={family}
            onChange={e => setFamily(e.target.value)}
            aria-label="Filter by scent family"
          >
            <option value="">All families</option>
            {families.map(f => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        )}
      </div>

      {loading && <p className="search-status">Searching…</p>}

      {!loading && results.length > 0 && (
        <ul className="search-results" role="list">
          {results.map(r => (
            <li key={`${r.brand}-${r.name}`} className="search-result">
              <div className="result-header">
                <span className="result-name">{r.name}</span>
                <span className="result-brand">{r.brand}</span>
                <span className="result-score">{toPercent(r.similarity_score)} match</span>
              </div>
              {r.description && (
                <p className="result-description">
                  {r.description.length > 120 ? r.description.slice(0, 120) + '…' : r.description}
                </p>
              )}
              {r.notes && <p className="result-notes">{r.notes}</p>}
            </li>
          ))}
        </ul>
      )}

      {!loading && query.trim().length >= MIN_QUERY_LEN && results.length === 0 && (
        <p className="search-status">No fragrances found.</p>
      )}
    </section>
  );
};

export default SearchPanel;
