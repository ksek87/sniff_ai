import { useState } from 'react';
import { FragranceComposition } from '../types/fragrance';
import { generateFragrance } from '../services/apiService';

interface GenerationState {
  composition: FragranceComposition | null;
  loading: boolean;
  error: string | null;
}

export function useFragranceGeneration() {
  const [state, setState] = useState<GenerationState>({
    composition: null,
    loading: false,
    error: null,
  });

  const generate = async (description: string, pinnedNotes: string[] = []) => {
    if (!description.trim()) return;
    setState({ composition: null, loading: true, error: null });
    try {
      const composition = await generateFragrance(description, pinnedNotes);
      setState({ composition, loading: false, error: null });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Generation failed. Please try again.';
      setState({ composition: null, loading: false, error: message });
    }
  };

  return { ...state, generate };
}
