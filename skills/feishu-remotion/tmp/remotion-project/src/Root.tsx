import { Composition } from 'remotion';
import { MeetingSummary } from './compositions/MeetingSummary';
import script from './data/script.json';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MeetingSummary"
      component={MeetingSummary}
      durationInFrames=3600
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        script: script
      }}
    />
  );
};
