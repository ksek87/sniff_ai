import axios from 'axios';
import { FragranceComposition, FeedbackPayload, Metrics, SharedFragrance } from '../types/fragrance';

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

export const fetchNotes = async (): Promise<string[]> => {
  const { data } = await axios.get<string[]>(`${BASE_URL}/api/v1/notes`);
  return data;
};

export const fetchMetrics = async (): Promise<Metrics> => {
  const { data } = await axios.get<Metrics>(`${BASE_URL}/api/v1/metrics`);
  return data;
};

export const shareFragrance = async (payload: SharedFragrance): Promise<string> => {
  const { data } = await axios.post<{ token: string }>(`${BASE_URL}/api/v1/share`, payload);
  return data.token;
};

export const fetchSharedFragrance = async (token: string, signal?: AbortSignal): Promise<SharedFragrance> => {
  const { data } = await axios.get<SharedFragrance>(`${BASE_URL}/api/v1/share/${token}`, { signal });
  return data;
};
