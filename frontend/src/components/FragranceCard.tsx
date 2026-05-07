import React from 'react';
import { FragranceComposition } from '../types/fragrance';
import { toPercent } from '../utils/format';
import NotesPyramid from './NotesPyramid';

interface Props {
  composition: FragranceComposition;
}

const FragranceCard: React.FC<Props> = ({ composition }) => (
  <div className="fragrance-card">
    <div className="card-header">
      <h2 className="fragrance-name">{composition.name}</h2>
      <span className="scent-family-badge">{composition.scent_family}</span>
    </div>

    <NotesPyramid
      topNotes={composition.top_notes}
      middleNotes={composition.middle_notes}
      baseNotes={composition.base_notes}
    />

    <blockquote className="poetic-description">
      {composition.poetic_description}
    </blockquote>

    {composition.similar_fragrances.length > 0 && (
      <div className="similar-fragrances">
        <h4>Similar fragrances</h4>
        <div className="similar-list">
          {composition.similar_fragrances.map(sf => (
            <span key={`${sf.brand}-${sf.name}`} className="similar-chip">
              {sf.brand} — {sf.name}
              <span className="similarity-score">{toPercent(sf.similarity_score)} match</span>
            </span>
          ))}
        </div>
      </div>
    )}

    <div className="card-footer">
      <span className="confidence">Confidence: {toPercent(composition.confidence_score)}</span>
    </div>
  </div>
);

export default FragranceCard;
