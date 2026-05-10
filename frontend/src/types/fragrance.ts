export interface FragranceNote {
  note: string;
  percentage: number;
}

export interface SimilarFragrance {
  brand: string;
  name: string;
  similarity_score: number;
}

export interface FragranceComposition {
  name: string;
  scent_family: string;
  top_notes: FragranceNote[];
  middle_notes: FragranceNote[];
  base_notes: FragranceNote[];
  poetic_description: string;
  similar_fragrances: SimilarFragrance[];
  confidence_score: number;
}

export interface FeedbackPayload {
  session_id: string;
  input_description: string;
  composition: FragranceComposition;
  rating: number;
  comment?: string;
}

export interface SearchResult {
  brand: string;
  name: string;
  notes: string;
  concepts: string;
  description: string;
  similarity_score: number;
}

export interface Metrics {
  total_feedback: number;
  average_rating: number | null;
  rating_distribution: Record<string, number>;
}

export interface SharePayload {
  input_description: string;
  composition: FragranceComposition;
}

export interface SharedFragrance {
  input_description: string;
  composition: FragranceComposition;
}
