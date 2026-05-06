import React, { useState, useEffect } from 'react';
import { fetchNotes } from '../services/apiService';

interface Props {
  selected: string[];
  onToggle: (note: string) => void;
}

const MAX_SHOWN = 30;
const MAX_SELECTED = 10;

const NoteSelector: React.FC<Props> = ({ selected, onToggle }) => {
  const [allNotes, setAllNotes] = useState<string[]>([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetchNotes().then(setAllNotes).catch(() => {});
  }, []);

  if (allNotes.length === 0) return null;

  const query = filter.trim().toLowerCase();
  const suggestions = query
    ? allNotes.filter(n => n.toLowerCase().includes(query)).slice(0, MAX_SHOWN)
    : [];
  const atMax = selected.length >= MAX_SELECTED;

  return (
    <div className="note-selector">
      {selected.length > 0 && (
        <div className="note-selector-selected" role="group" aria-label="Pinned notes">
          {selected.map(note => (
            <button
              key={note}
              type="button"
              className="note-chip"
              onClick={() => onToggle(note)}
              aria-label={`Remove ${note}`}
            >
              {note} <span aria-hidden="true">×</span>
            </button>
          ))}
        </div>
      )}
      <input
        className="note-selector-filter"
        type="text"
        value={filter}
        onChange={e => setFilter(e.target.value)}
        placeholder={atMax ? 'Max 10 notes pinned' : 'Pin a note… e.g. oud, bergamot, vetiver'}
        disabled={atMax}
        aria-label="Search notes to pin"
      />
      {suggestions.length > 0 && (
        <div className="note-options-list" role="listbox" aria-label="Note suggestions">
          {suggestions.map(note => {
            const isSelected = selected.includes(note);
            return (
              <button
                key={note}
                type="button"
                role="option"
                aria-selected={isSelected}
                className={`note-option${isSelected ? ' selected' : ''}`}
                onClick={() => {
                  onToggle(note);
                  if (!isSelected) setFilter('');
                }}
                disabled={atMax && !isSelected}
              >
                {note}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default NoteSelector;
