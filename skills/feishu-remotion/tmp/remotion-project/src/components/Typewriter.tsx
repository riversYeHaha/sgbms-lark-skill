import { useCurrentFrame, useVideoConfig } from 'remotion';

export const useTypewriter = (text: string, charsPerSecond: number = 15): string => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const charsToShow = Math.floor((frame / fps) * charsPerSecond);
  return text.slice(0, charsToShow);
};
