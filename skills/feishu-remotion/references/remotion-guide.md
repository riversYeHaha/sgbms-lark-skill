# Remotion 使用指南

## 基本概念

Remotion 是一个使用 React 生成视频的框架。核心概念：

- **Composition**：视频的定义，包含时长、帧率、尺寸等
- **Frame**：视频的每一帧，通过 `useCurrentFrame()` 获取当前帧号
- **Video Config**：通过 `useVideoConfig()` 获取视频的 fps、width、height、durationInFrames
- **Interpolation**：使用 `interpolate()` 函数在帧之间进行插值计算
- **Spring**：使用 `spring()` 函数创建弹性动画

## 项目结构

```
remotion-project/
├── src/
│   ├── index.tsx      # 入口，注册 Root
│   ├── Root.tsx       # 定义所有 Composition
│   └── compositions/  # 视频组件
├── public/            # 静态资源
└── package.json
```

## 核心组件示例

### 1. 打字机效果

```tsx
import { useCurrentFrame, useVideoConfig } from 'remotion';

export const Typewriter: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const charsPerSecond = 15;
  const charsToShow = Math.floor((frame / fps) * charsPerSecond);
  const displayedText = text.slice(0, charsToShow);
  
  return (
    <div style={{ fontSize: 48, color: 'white' }}>
      {displayedText}
      <span style={{ opacity: frame % 30 < 15 ? 1 : 0 }}>|</span>
    </div>
  );
};
```

### 2. 淡入效果

```tsx
import { useCurrentFrame, interpolate, Easing } from 'remotion';

export const FadeIn: React.FC<{ children: React.ReactNode; delay?: number }> = ({ 
  children, 
  delay = 0 
}) => {
  const frame = useCurrentFrame();
  
  const opacity = interpolate(
    frame,
    [delay, delay + 15],
    [0, 1],
    { easing: Easing.easeInOut }
  );
  
  return (
    <div style={{ opacity }}>
      {children}
    </div>
  );
};
```

### 3. 图片展示

```tsx
import { Img, staticFile } from 'remotion';

export const ScreenshotScene: React.FC<{ imagePath: string }> = ({ imagePath }) => {
  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#1a1a1a'
    }}>
      <Img 
        src={staticFile(imagePath)} 
        style={{ maxWidth: '90%', maxHeight: '90%' }}
      />
    </div>
  );
};
```

## Composition 定义

```tsx
// Root.tsx
import { Composition } from 'remotion';
import { MeetingSummary } from './compositions/MeetingSummary';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MeetingSummary"
      component={MeetingSummary}
      durationInFrames={5400}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        script: require('./data/script.json')
      }}
    />
  );
};
```

## 渲染命令

```bash
# 开发模式
npx remotion studio

# 渲染视频
npx remotion render src/index.tsx MeetingSummary output.mp4

# 指定帧范围
npx remotion render src/index.tsx MeetingSummary output.mp4 --frames=0-900

# 指定编码
npx remotion render src/index.tsx MeetingSummary output.mp4 --codec=h264
```

## 常用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--frames` | 帧范围 | `--frames=0-300` |
| `--codec` | 编码格式 | `--codec=h264`, `--codec=h265` |
| `--crf` | 质量 (0-51, 越小越好) | `--crf=18` |
| `--bitrate` | 比特率 | `--bitrate=10M` |

## 动画工具函数

### interpolate

在帧范围之间进行插值：

```tsx
const opacity = interpolate(
  frame,
  [0, 30],           // 输入帧范围
  [0, 1],            // 输出值范围
  { easing: Easing.easeInOut }
);
```

### spring

创建弹性动画：

```tsx
const scale = spring({
  frame,
  fps,
  config: {
    damping: 100,
    stiffness: 200,
    mass: 1
  }
});
```

### Sequence

按顺序播放多个组件：

```tsx
import { Sequence } from 'remotion';

<Sequence from={0} durationInFrames={90}>
  <TitleScene title="会议总结" />
</Sequence>

<Sequence from={90} durationInFrames={180}>
  <ContentScene content="要点1..." />
</Sequence>
```
