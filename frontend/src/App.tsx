import React, { useState, useEffect } from 'react';
import './App.css';
import DescriptionInput from './components/DescriptionInput';
import FragranceCard from './components/FragranceCard';
import NoteSelector from './components/NoteSelector';
import FeedbackWidget from './components/FeedbackWidget';
import SearchPanel from './components/SearchPanel';
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
      <header className="app-header">
        <h1>Sniff AI</h1>
        <p className="app-tagline">Describe a feeling. We'll create the scent.</p>
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
        <SearchPanel />
        <MetricsDashboard />
      </main>
    </div>
  );
};

export default App;
