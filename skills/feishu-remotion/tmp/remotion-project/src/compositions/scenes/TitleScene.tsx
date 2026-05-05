import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

interface TitleSceneProps {
  title: string;
  subtitle: string;
}

export const TitleScene: React.FC<TitleSceneProps> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1]);
  const scale = interpolate(frame, [0, 15], [0.8, 1]);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      opacity,
      transform: `scale(${scale})`
    }}>
      <h1 style={{ fontSize: 72, color: 'white', marginBottom: 20 }}>{title}</h1>
      <p style={{ fontSize: 36, color: 'rgba(255,255,255,0.8)' }}>{subtitle}</p>
    </div>
  );
};
