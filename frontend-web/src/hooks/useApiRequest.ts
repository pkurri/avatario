"use client";

import { useState, useCallback } from 'react';

interface ApiRequestState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiRequestReturn<T> extends ApiRequestState<T> {
  execute: (fn: () => Promise<T>) => Promise<T | null>;
  reset: () => void;
}

export function useApiRequest<T>(): UseApiRequestReturn<T> {
  const [state, setState] = useState<ApiRequestState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async (fn: () => Promise<T>): Promise<T | null> => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const result = await fn();
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred';
      console.error(err);
      setState(prev => ({ ...prev, loading: false, error: msg }));
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return { ...state, execute, reset };
}
