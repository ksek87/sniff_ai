import React, { useState, useEffect } from 'react';

const STAGES = [
  { label: 'Analyzing your description',      seconds: 0 },
  { label: 'Searching the fragrance database', seconds: 2 },
  { label: 'Consulting the perfumer',          seconds: 6 },
  { label: 'Composing your fragrance',         seconds: 18 },
];

function activeStageIndex(elapsed: number): number {
  let idx = 0;
  for (let i = 0; i < STAGES.length; i++) {
    if (elapsed >= STAGES[i].seconds) idx = i;
  }
  return idx;
}

const GenerationProgress: React.FC = () => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 500);
    return () => clearInterval(id);
  }, []);

  const activeIdx = activeStageIndex(elapsed);

  return (
    <div className="generation-progress" role="status" aria-live="polite">
      <ol className="progress-stages">
        {STAGES.map((stage, i) => {
          const done = i < activeIdx;
          const active = i === activeIdx;
          const className = ['progress-stage', done && 'done', active && 'active']
            .filter(Boolean)
            .join(' ');
          return (
            <li key={stage.label} className={className}>
              <span className="stage-icon" aria-hidden="true">
                {done ? '✓' : active ? <span className="stage-spinner" /> : '·'}
              </span>
              <span className="stage-label">{stage.label}</span>
            </li>
          );
        })}
      </ol>
      <p className="progress-elapsed">{elapsed}s</p>
    </div>
  );
};

export default GenerationProgress;
