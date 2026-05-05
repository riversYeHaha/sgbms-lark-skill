import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

interface SpeakerSceneProps {
  speaker: string;
  content: string;
}

export const SpeakerScene: React.FC<SpeakerSceneProps> = ({ speaker, content }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [0, 1]);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#1a1a1a',
      opacity
    }}>
      <div style={{
        width: 120,
        height: 120,
        borderRadius: '50%',
        backgroundColor: '#667eea',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 48,
        color: 'white',
        marginBottom: 30
      }}>
        {speaker[0]}
      </div>
      <p style={{ fontSize: 28, color: 'rgba(255,255,255,0.6)', marginBottom: 20 }}>{speaker}</p>
      <p style={{ fontSize: 36, color: 'white', maxWidth: '80%', textAlign: 'center' }}>{content}</p>
    </div>
  );
};
