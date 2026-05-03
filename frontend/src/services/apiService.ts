import axios from 'axios';
import { FragranceComposition, FeedbackPayload, SearchResult } from '../types/fragrance';

// Empty string = same origin (production); set REACT_APP_API_URL for local dev
const BASE_URL = process.env.REACT_APP_API_URL ?? "";

export const generateFragrance = async (
  description: string,
  pinnedNotes: string[] = []
): Promise<FragranceComposition> => {
  const { data } = await axios.post<FragranceComposition>(`${BASE_URL}/api/v1/generate`, {
    description,
    pinned_notes: pinnedNotes,
  });
  return data;
};

export const submitFeedback = async (payload: FeedbackPayload): Promise<void> => {
  await axios.post(`${BASE_URL}/api/v1/feedback`, payload);
};

export const searchFragrances = async (
  query: string,
  family?: string
): Promise<SearchResult[]> => {
  const { data } = await axios.get<SearchResult[]>(`${BASE_URL}/api/v1/search`, {
    params: { q: query, ...(family ? { family } : {}) },
  });
  return data;
};

export const fetchNotes = async (): Promise<string[]> => {
  const { data } = await axios.get<string[]>(`${BASE_URL}/api/v1/notes`);
  return data;
};

export const fetchFamilies = async (): Promise<string[]> => {
  const { data } = await axios.get<string[]>(`${BASE_URL}/api/v1/families`);
  return data;
};
