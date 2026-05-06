import { useState } from 'react';
import { FragranceComposition } from '../types/fragrance';
import { generateFragrance } from '../services/apiService';

interface GenerationState {
  composition: FragranceComposition | null;
  description: string;
  loading: boolean;
  error: string | null;
}

export function useFragranceGeneration() {
  const [state, setState] = useState<GenerationState>({
    composition: null,
    description: '',
    loading: false,
    error: null,
  });

  const generate = async (description: string, pinnedNotes: string[] = []) => {
    if (!description.trim()) return;
    setState(prev => ({ ...prev, description, loading: true, error: null }));
    try {
      const composition = await generateFragrance(description, pinnedNotes);
      setState({ composition, description, loading: false, error: null });
    } catch (err: unknown) {
      console.error('Fragrance generation failed:', err);
      setState(prev => ({ ...prev, loading: false, error: 'Generation failed. Please try again.' }));
    }
  };

  return { ...state, generate };
}
