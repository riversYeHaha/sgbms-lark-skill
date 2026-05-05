import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

interface EndingSceneProps {
  content: string;
}

export const EndingScene: React.FC<EndingSceneProps> = ({ content }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [0, 1]);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      opacity
    }}>
      <p style={{ fontSize: 48, color: 'white' }}>{content}</p>
    </div>
  );
};
