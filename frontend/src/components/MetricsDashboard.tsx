import React, { useState, useEffect } from 'react';
import { Metrics } from '../types/fragrance';
import { fetchMetrics } from '../services/apiService';

const MetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    fetchMetrics().then(setMetrics).catch(() => {});
  }, []);

  if (!metrics || metrics.total_feedback === 0) return null;

  const dist = metrics.rating_distribution;
  const maxCount = Math.max(...Object.values(dist), 1);
  const avgStr = metrics.average_rating != null ? metrics.average_rating.toFixed(1) : '—';

  return (
    <section className="metrics-dashboard" aria-label="Feedback metrics">
      <h3 className="section-heading">Community Ratings</h3>
      <p className="metrics-summary">
        <span className="metric-value">{metrics.total_feedback}</span>
        <span className="metric-label"> ratings</span>
        <span className="metric-separator"> · </span>
        <span className="metric-value">{avgStr}</span>
        <span className="metric-label"> avg</span>
      </p>
      <div className="metrics-bars" role="list" aria-label="Rating distribution">
        {(['5', '4', '3', '2', '1'] as const).map(star => {
          const count = dist[star] ?? 0;
          const width = Math.round((count / maxCount) * 100);
          return (
            <div key={star} className="metrics-bar-row" role="listitem">
              <span className="bar-label">{star}★</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${width}%` }} />
              </div>
              <span className="bar-count">{count}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default MetricsDashboard;
