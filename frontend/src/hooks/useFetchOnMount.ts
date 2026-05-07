import { useState, useEffect } from 'react';

export function useFetchOnMount<T>(fetcher: () => Promise<T>, initial: T): T {
  const [data, setData] = useState<T>(initial);
  useEffect(() => {
    let active = true;
    fetcher()
      .then(result => { if (active) setData(result); })
      .catch(() => {});
    return () => { active = false; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return data;
}
