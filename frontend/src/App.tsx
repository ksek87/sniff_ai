import React, { useMemo, useState } from 'react';
import './App.css';
import DescriptionInput from './components/DescriptionInput';
import FragranceCard from './components/FragranceCard';
import NoteSelector from './components/NoteSelector';
import FeedbackWidget from './components/FeedbackWidget';
import SearchPanel from './components/SearchPanel';
import MetricsDashboard from './components/MetricsDashboard';
import { useFragranceGeneration } from './hooks/useFragranceGeneration';

const App: React.FC = () => {
  const sessionId = useMemo(() => crypto.randomUUID(), []);
  const [pinnedNotes, setPinnedNotes] = useState<string[]>([]);
  const { composition, description, loading, error, generate } = useFragranceGeneration();

  const handleToggleNote = (note: string) => {
    setPinnedNotes(prev =>
      prev.includes(note)
        ? prev.filter(n => n !== note)
        : [...prev, note].slice(0, 10)
    );
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Sniff AI</h1>
        <p className="app-tagline">Describe a feeling. We'll create the scent.</p>
      </header>

      <main className="app-main">
        <DescriptionInput
          onGenerate={(desc) => generate(desc, pinnedNotes)}
          loading={loading}
          additionalContent={
            <NoteSelector selected={pinnedNotes} onToggle={handleToggleNote} />
          }
        />

        {error && (
          <div className="error-message" role="alert">{error}</div>
        )}

        {composition && (
          <>
            <FragranceCard composition={composition} />
            <FeedbackWidget
              sessionId={sessionId}
              description={description}
              composition={composition}
            />
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
