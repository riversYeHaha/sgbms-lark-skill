import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

interface FadeInProps {
  children: React.ReactNode;
  startFrame?: number;
  durationFrames?: number;
}

export const FadeIn: React.FC<FadeInProps> = ({
  children,
  startFrame = 0,
  durationFrames = 15,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );
  return <div style={{ opacity }}>{children}</div>;
};
