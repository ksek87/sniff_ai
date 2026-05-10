import React, { useState } from 'react';
import GenerationProgress from './GenerationProgress';

interface Props {
  onGenerate: (description: string) => void;
  loading: boolean;
  additionalContent?: React.ReactNode;
}

const DescriptionInput: React.FC<Props> = ({ onGenerate, loading, additionalContent }) => {
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (description.trim()) {
      onGenerate(description.trim());
    }
  };

  return (
    <form className="description-form" onSubmit={handleSubmit}>
      <textarea
        className="description-input"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Describe your fragrance… e.g. 'an autumn walk through a pine forest after rain'"
        rows={4}
        disabled={loading}
      />
      {additionalContent}
      <button
        type="submit"
        className="generate-btn"
        disabled={loading || !description.trim()}
      >
        {loading ? 'Creating…' : 'Create Fragrance'}
      </button>
      {loading && <GenerationProgress />}
    </form>
  );
};

export default DescriptionInput;
