import React from 'react';
import { useCurrentFrame } from 'remotion';
import { useTypewriter } from '../../components/Typewriter';

interface ContentSceneProps {
  content: string;
  bulletPoints: string[];
}

export const ContentScene: React.FC<ContentSceneProps> = ({ content, bulletPoints }) => {
  const frame = useCurrentFrame();
  const displayedText = useTypewriter(content);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      padding: 80,
      backgroundColor: '#1a1a1a'
    }}>
      <p style={{ fontSize: 48, color: 'white', marginBottom: 40 }}>
        {displayedText}
        <span style={{ opacity: frame % 30 < 15 ? 1 : 0 }}>|</span>
      </p>
      <ul>
        {bulletPoints.map((point, i) => (
          <li key={i} style={{ fontSize: 32, color: '#4CAF50', marginBottom: 16 }}>{point}</li>
        ))}
      </ul>
    </div>
  );
};
