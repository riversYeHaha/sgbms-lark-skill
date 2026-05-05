import React from 'react';
import { useCurrentFrame, interpolate, Img, staticFile } from 'remotion';

interface ScreenshotSceneProps {
  imagePath: string;
  caption: string;
}

export const ScreenshotScene: React.FC<ScreenshotSceneProps> = ({ imagePath, caption }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1]);

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
      <Img src={staticFile(imagePath)} style={{ maxWidth: '90%', maxHeight: '80%' }} />
      <p style={{ fontSize: 24, color: 'rgba(255,255,255,0.7)', marginTop: 20 }}>{caption}</p>
    </div>
  );
};
