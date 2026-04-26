import React from 'react';
import { FragranceNote } from '../types/fragrance';

interface TierProps {
  label: string;
  notes: FragranceNote[];
  className: string;
}

const Tier: React.FC<TierProps> = ({ label, notes, className }) => (
  <div className={`pyramid-tier ${className}`}>
    <span className="tier-label">{label}</span>
    <div className="tier-notes">
      {notes.map((n) => (
        <span key={n.note} className="note-pill">
          {n.note} <span className="note-pct">{n.percentage}%</span>
        </span>
      ))}
    </div>
  </div>
);

interface Props {
  topNotes: FragranceNote[];
  middleNotes: FragranceNote[];
  baseNotes: FragranceNote[];
}

const NotesPyramid: React.FC<Props> = ({ topNotes, middleNotes, baseNotes }) => (
  <div className="notes-pyramid">
    <Tier label="Top" notes={topNotes} className="tier-top" />
    <Tier label="Heart" notes={middleNotes} className="tier-middle" />
    <Tier label="Base" notes={baseNotes} className="tier-base" />
  </div>
);

export default NotesPyramid;
