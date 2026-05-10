import React, { useState } from 'react';
import { FragranceComposition } from '../types/fragrance';
import { shareFragrance } from '../services/apiService';

interface Props {
  description: string;
  composition: FragranceComposition;
}

type ShareState = 'idle' | 'loading' | 'ready' | 'copied' | 'error';

function buildShareMessage(name: string, url: string): string {
  return `I created "${name}" with Sniff AI — a fragrance generated just from a description.\n\n${url}`;
}

function buildShareUrl(token: string): string {
  return `${window.location.origin}${window.location.pathname}?share=${token}`;
}

const ShareButton: React.FC<Props> = ({ description, composition }) => {
  const [state, setState] = useState<ShareState>('idle');
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  const handleShare = async () => {
    if (shareUrl) {
      await navigator.clipboard.writeText(buildShareMessage(composition.name, shareUrl));
      setState('copied');
      setTimeout(() => setState('ready'), 2000);
      return;
    }

    setState('loading');
    try {
      const token = await shareFragrance({ input_description: description, composition });
      const url = buildShareUrl(token);
      setShareUrl(url);
      await navigator.clipboard.writeText(buildShareMessage(composition.name, url));
      setState('copied');
      setTimeout(() => setState('ready'), 2000);
    } catch {
      setState('error');
      setTimeout(() => setState('idle'), 3000);
    }
  };

  const buttonLabel =
    state === 'loading' ? 'Creating link…' :
    state === 'copied'  ? '✓ Copied to clipboard' :
    state === 'error'   ? 'Failed — try again' :
    shareUrl            ? 'Copy share message' :
    'Share this fragrance';

  return (
    <div className="share-container">
      <button
        className="share-btn"
        onClick={handleShare}
        disabled={state === 'loading'}
      >
        {buttonLabel}
      </button>
      {shareUrl && (
        <p className="share-url">{shareUrl}</p>
      )}
    </div>
  );
};

export default ShareButton;
