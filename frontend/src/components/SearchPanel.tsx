import React, { useState, useEffect, useRef } from 'react';
import { SearchResult } from '../types/fragrance';
import { searchFragrances, fetchFamilies } from '../services/apiService';

const SearchPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const [family, setFamily] = useState('');
  const [families, setFamilies] = useState<string[]>([]);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchFamilies().then(setFamilies).catch(() => {});
  }, []);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);

    const q = query.trim();
    if (q.length < 2) {
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
    }, 300);

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
          {results.map((r, i) => (
            <li key={`${r.brand}-${r.name}-${i}`} className="search-result">
              <div className="result-header">
                <span className="result-name">{r.name}</span>
                <span className="result-brand">{r.brand}</span>
                <span className="result-score">{Math.round(r.similarity_score * 100)}% match</span>
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

      {!loading && query.trim().length >= 2 && results.length === 0 && (
        <p className="search-status">No fragrances found.</p>
      )}
    </section>
  );
};

export default SearchPanel;
