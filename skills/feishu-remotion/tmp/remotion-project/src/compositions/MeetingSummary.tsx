import React from 'react';
import { Sequence } from 'remotion';
import { TitleScene } from './scenes/TitleScene';
import { ContentScene } from './scenes/ContentScene';
import { ScreenshotScene } from './scenes/ScreenshotScene';
import { SpeakerScene } from './scenes/SpeakerScene';
import { EndingScene } from './scenes/EndingScene';

interface MeetingSummaryProps {
  script: any;
}

export const MeetingSummary: React.FC<MeetingSummaryProps> = ({ script }) => {
  return (
    <div style={{ width: '100%', height: '100%', backgroundColor: '#1a1a1a' }}>
      
        <Sequence from={0} durationInFrames={150}>
          <TitleScene title="Q2产品规划会议" subtitle="聚焦三大核心目标" />
        </Sequence>
        <Sequence from={150} durationInFrames={450}>
          <ContentScene content="背景与数据洞察" bulletPoints={["Q1完成基础框架搭建，用户反馈良好", "DAU增长15%，但留存率下降3个百分点", "新用户引导流程复杂，前3天流失率高"]} />
        </Sequence>
        <Sequence from={900} durationInFrames={600}>
          <ContentScene content="Q2三大核心目标" bulletPoints={["目标1：优化新用户引导流程（最优先）", "目标2：首页加载时间降至1秒以内", "目标3：完成移动端适配（剩余40%页面）"]} />
        </Sequence>
        <Sequence from={1500} durationInFrames={2100}>
          <EndingScene content="" />
        </Sequence>
    </div>
  );
};
