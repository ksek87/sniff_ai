import React, { useState, useEffect } from 'react';

const STAGES = [
  { label: 'Analyzing your description',     threshold: 0 },
  { label: 'Searching the fragrance database', threshold: 2 },
  { label: 'Consulting the perfumer',          threshold: 6 },
  { label: 'Composing your fragrance',         threshold: 18 },
];

const GenerationProgress: React.FC = () => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 500);
    return () => clearInterval(id);
  }, []);

  const currentStage = STAGES.reduce(
    (acc, s, i) => (elapsed >= s.threshold ? i : acc),
    0
  );

  return (
    <div className="generation-progress" role="status" aria-live="polite">
      <ol className="progress-stages">
        {STAGES.map((s, i) => {
          const done   = i < currentStage;
          const active = i === currentStage;
          return (
            <li key={s.label} className={`progress-stage${done ? ' done' : active ? ' active' : ''}`}>
              <span className="stage-icon" aria-hidden="true">
                {done ? '✓' : active ? <span className="stage-spinner" /> : '·'}
              </span>
              <span className="stage-label">{s.label}</span>
            </li>
          );
        })}
      </ol>
      <p className="progress-elapsed">{elapsed}s</p>
    </div>
  );
};

export default GenerationProgress;
