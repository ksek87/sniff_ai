import React, { useState, useEffect, useRef } from 'react';
import { FragranceComposition, SharedFragrance } from '../types/fragrance';
import { shareFragrance } from '../services/apiService';

interface Props {
  description: string;
  composition: FragranceComposition;
}

type ShareState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; url: string }
  | { status: 'copied'; url: string }
  | { status: 'error' };

const IDLE: ShareState = { status: 'idle' };

function getButtonLabel(state: ShareState): string {
  if (state.status === 'loading') return 'Creating link…';
  if (state.status === 'copied')  return '✓ Copied to clipboard';
  if (state.status === 'error')   return 'Failed — try again';
  if (state.status === 'ready')   return 'Copy share message';
  return 'Share this fragrance';
}

function buildShareMessage(name: string, url: string): string {
  return `I created "${name}" with Sniff AI — a fragrance generated just from a description.\n\n${url}`;
}

function buildShareUrl(token: string): string {
  return `${window.location.origin}${window.location.pathname}?share=${token}`;
}

async function writeToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      // fall through to execCommand for iOS Safari
    }
  }
  const el = document.createElement('textarea');
  el.value = text;
  el.style.cssText = 'position:fixed;opacity:0;pointer-events:none';
  document.body.appendChild(el);
  el.select();
  document.execCommand('copy');
  document.body.removeChild(el);
}

const ShareButton: React.FC<Props> = ({ description, composition }) => {
  const [state, setState] = useState<ShareState>(IDLE);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { setState(IDLE); }, [composition]);
  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  const scheduleTransition = (next: ShareState, delay: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setState(next), delay);
  };

  const handleShare = async () => {
    const activeUrl =
      state.status === 'ready' || state.status === 'copied' ? state.url : null;

    if (activeUrl) {
      try {
        await writeToClipboard(buildShareMessage(composition.name, activeUrl));
        setState({ status: 'copied', url: activeUrl });
        scheduleTransition({ status: 'ready', url: activeUrl }, 2000);
      } catch {
        setState({ status: 'ready', url: activeUrl });
      }
      return;
    }

    setState({ status: 'loading' });
    try {
      const payload: SharedFragrance = { input_description: description, composition };
      const token = await shareFragrance(payload);
      const url = buildShareUrl(token);
      try {
        await writeToClipboard(buildShareMessage(composition.name, url));
        setState({ status: 'copied', url });
        scheduleTransition({ status: 'ready', url }, 2000);
      } catch {
        // Share saved — clipboard failed (iOS Safari); show URL for manual copy
        setState({ status: 'ready', url });
      }
    } catch {
      setState({ status: 'error' });
      scheduleTransition(IDLE, 3000);
    }
  };

  const shareUrl =
    state.status === 'ready' || state.status === 'copied' ? state.url : null;

  return (
    <div className="share-container">
      <button
        className="share-btn"
        onClick={handleShare}
        disabled={state.status === 'loading'}
      >
        {getButtonLabel(state)}
      </button>
      {shareUrl && <p className="share-url">{shareUrl}</p>}
    </div>
  );
};

export default ShareButton;
