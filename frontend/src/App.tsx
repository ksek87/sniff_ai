import React from 'react';
import './App.css';
import DescriptionInput from './components/DescriptionInput';
import FragranceCard from './components/FragranceCard';
import { useFragranceGeneration } from './hooks/useFragranceGeneration';

const App: React.FC = () => {
  const { composition, loading, error, generate } = useFragranceGeneration();

  return (
    <div className="app">
      <header className="app-header">
        <h1>Sniff AI</h1>
        <p className="app-tagline">Describe a feeling. We'll create the scent.</p>
      </header>

      <main className="app-main">
        <DescriptionInput onGenerate={generate} loading={loading} />

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        {composition && <FragranceCard composition={composition} />}
      </main>
    </div>
  );
};

export default App;
