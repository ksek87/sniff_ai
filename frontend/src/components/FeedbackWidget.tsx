import React, { useState, useEffect } from 'react';
import { FragranceComposition } from '../types/fragrance';
import { submitFeedback } from '../services/apiService';

interface Props {
  sessionId: string;
  description: string;
  composition: FragranceComposition;
}

type Phase = 'rating' | 'commenting' | 'submitting' | 'done';

const FeedbackWidget: React.FC<Props> = ({ sessionId, description, composition }) => {
  const [phase, setPhase] = useState<Phase>('rating');
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState('');

  useEffect(() => {
    setPhase('rating');
    setRating(0);
    setHover(0);
    setComment('');
  }, [composition]);

  const handleStar = (star: number) => {
    setRating(star);
    setPhase('commenting');
  };

  const handleSubmit = async () => {
    setPhase('submitting');
    try {
      await submitFeedback({
        session_id: sessionId,
        input_description: description,
        composition,
        rating,
        comment: comment.trim() || undefined,
      });
    } catch (err) {
      console.error('Feedback submission failed:', err);
    }
    setPhase('done');
  };

  if (phase === 'done') {
    return (
      <div className="feedback-widget">
        <p className="feedback-thanks">Thank you for your feedback.</p>
      </div>
    );
  }

  const active = hover || rating;

  return (
    <div className="feedback-widget">
      <p className="feedback-label">Rate this composition</p>
      <div className="star-row" role="group" aria-label="Star rating">
        {[1, 2, 3, 4, 5].map(n => (
          <button
            key={n}
            type="button"
            className={`star-btn${n <= active ? ' filled' : ''}`}
            onClick={() => handleStar(n)}
            onMouseEnter={() => setHover(n)}
            onMouseLeave={() => setHover(0)}
            aria-label={`${n} star${n !== 1 ? 's' : ''}`}
            disabled={phase === 'submitting'}
          >
            ★
          </button>
        ))}
      </div>
      {phase === 'commenting' && (
        <div className="feedback-comment-row">
          <textarea
            className="feedback-comment"
            placeholder="Any thoughts? (optional)"
            value={comment}
            onChange={e => setComment(e.target.value)}
            rows={2}
            maxLength={500}
          />
          <button
            type="button"
            className="feedback-submit-btn"
            onClick={handleSubmit}
          >
            Submit
          </button>
        </div>
      )}
    </div>
  );
};

export default FeedbackWidget;
