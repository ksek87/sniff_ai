import React, { useState, useEffect } from 'react';
import './App.css';
import DescriptionInput from './components/DescriptionInput';
import FragranceCard from './components/FragranceCard';
import NoteSelector from './components/NoteSelector';
import FeedbackWidget from './components/FeedbackWidget';
import MetricsDashboard from './components/MetricsDashboard';
import ShareButton from './components/ShareButton';
import { useFragranceGeneration } from './hooks/useFragranceGeneration';
import { fetchSharedFragrance } from './services/apiService';
import { SharedFragrance } from './types/fragrance';

const App: React.FC = () => {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [pinnedNotes, setPinnedNotes] = useState<string[]>([]);
  const { composition, description, loading, error, generate } = useFragranceGeneration();

  const [sharedFragrance, setSharedFragrance] = useState<SharedFragrance | null>(null);
  const [shareError, setShareError] = useState<string | null>(null);

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('share');
    if (!token) return;
    const controller = new AbortController();
    fetchSharedFragrance(token, controller.signal)
      .then(setSharedFragrance)
      .catch(err => {
        if (!controller.signal.aborted) {
          setShareError('Could not load shared fragrance — the link may have expired.');
        }
      });
    return () => controller.abort();
  }, []);

  const handleToggleNote = (note: string) => {
    setPinnedNotes(prev =>
      prev.includes(note)
        ? prev.filter(n => n !== note)
        : [...prev, note].slice(0, 10)
    );
  };

  const clearShare = () => {
    setSharedFragrance(null);
    window.history.replaceState(null, '', window.location.pathname);
  };

  const displayComposition = sharedFragrance?.composition ?? composition;
  const displayDescription = sharedFragrance?.input_description ?? description;

  return (
    <div className="app">
      <a
        href="https://github.com/ksek87/sniff_ai"
        className="github-link"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="View source on GitHub"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
        </svg>
      </a>

      <header className="app-header">
        <h1>Sniff AI</h1>
        <p className="app-tagline">From memory to molecule.</p>
        <p className="app-subtitle">Every great fragrance begins as a feeling. Describe yours.</p>
      </header>

      <main className="app-main">
        {sharedFragrance ? (
          <div className="shared-banner">
            <p className="shared-banner-text">You're viewing a shared fragrance</p>
            <button className="shared-banner-btn" onClick={clearShare}>
              Create your own →
            </button>
          </div>
        ) : (
          <DescriptionInput
            onGenerate={(desc) => generate(desc, pinnedNotes)}
            loading={loading}
            additionalContent={
              <NoteSelector selected={pinnedNotes} onToggle={handleToggleNote} />
            }
          />
        )}

        {(error || shareError) && (
          <div className="error-message" role="alert">{error ?? shareError}</div>
        )}

        {displayComposition && (
          <>
            <FragranceCard composition={displayComposition} />
            <ShareButton description={displayDescription} composition={displayComposition} />
            {!sharedFragrance && (
              <FeedbackWidget
                sessionId={sessionId}
                description={displayDescription}
                composition={displayComposition}
              />
            )}
          </>
        )}

        <div className="app-divider" />
        <MetricsDashboard />
      </main>
    </div>
  );
};

export default App;
