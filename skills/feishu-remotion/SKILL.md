---
name: feishu-remotion
description: 飞书会议视频生成 - 使用飞书 CLI 获取会议信息、日程和妙记，结合 Remotion 生成会议总结视频。当用户需要：生成会议视频、将会议内容转为视频、制作会议回顾视频、从飞书会议生成视频摘要、使用 Remotion 处理飞书会议内容、下载会议妙记并生成视频、根据会议逐字稿制作视频时触发。支持用户提供会议链接或查询日程获取会议，自动提取逐字稿、生成精炼脚本、智能截图、最终合成视频。
---

# 飞书会议视频生成 (Feishu Remotion)

## 概述

将飞书会议内容自动转换为精美的总结视频。核心流程：

1. **获取会议**：通过会议链接或查询日程获取会议信息
2. **提取内容**：读取妙记逐字稿，使用 LLM 提炼生成精炼脚本
3. **智能截图**：根据脚本内容判断是否需要截图，下载妙记视频并用 ffmpeg 截取关键帧
4. **视频合成**：使用 Remotion 将脚本和截图合成为最终视频

## 前置条件

1. 安装飞书 CLI：`npm install -g @larksuite/cli`
2. 初始化配置：`lark-cli config init`
3. 登录：`lark-cli auth login --recommend`
4. 安装 Remotion：`npm install remotion @remotion/cli`
5. 安装 ffmpeg（用于截图）：`brew install ffmpeg` 或 `apt-get install ffmpeg`
6. Node.js 18+，Python 3.8+

## 核心架构

```
feishu-remotion
├── 数据获取层 (Data Layer)
│   ├── get_meeting_by_link     — 通过会议链接获取会议信息
│   ├── get_schedule_by_date    — 查询某天日程获取会议列表
│   ├── get_meeting_minutes     — 获取会议妙记和逐字稿
│   └── download_meeting_video  — 下载妙记视频
│
├── 内容处理层 (Content Layer)
│   ├── extract_transcript      — 提取逐字稿文本
│   ├── generate_script         — 使用 LLM 生成精炼脚本
│   ├── analyze_screenshot_needs — 分析是否需要截图
│   └── capture_screenshots     — 使用 ffmpeg 截取关键帧
│
└── 视频生成层 (Video Layer)
    ├── prepare_remotion_project — 准备 Remotion 项目结构
    ├── create_composition       — 创建 Remotion Composition
    ├── render_video             — 渲染最终视频
    └── package_output          — 打包输出
```

## 快速开始

### 1. 通过会议链接生成视频

```bash
# 用户提供会议链接
python scripts/generate_meeting_video.py \
  --meeting-link "https://vc.feishu.cn/j/123456789" \
  --output-dir ./output \
  --style "summary"
```

### 2. 通过日程查询生成视频

```bash
# 查询今天日程，选择会议生成视频
python scripts/generate_meeting_video.py \
  --date "2024-01-15" \
  --output-dir ./output \
  --style "summary"
```

### 3. 完整流程示例

```bash
# Step 1: 获取会议信息
python scripts/get_meeting_info.py \
  --meeting-link "https://vc.feishu.cn/j/123456789" \
  --output ./tmp/meeting.json

# Step 2: 获取妙记和逐字稿
python scripts/get_meeting_minutes.py \
  --meeting-id "123456789" \
  --output ./tmp/transcript.json

# Step 3: 生成精炼脚本
python scripts/generate_script.py \
  --transcript ./tmp/transcript.json \
  --output ./tmp/script.json \
  --style "summary" \
  --max-duration 180 \
  --provider deepseek

# Step 4: 下载妙记视频并截图（如需要）
python scripts/capture_screenshots.py \
  --meeting-id "123456789" \
  --script ./tmp/script.json \
  --output-dir ./tmp/screenshots

# Step 5: 生成 Remotion 视频
python scripts/render_video.py \
  --script ./tmp/script.json \
  --screenshots ./tmp/screenshots \
  --output ./output/meeting-summary.mp4
```

### 4. 真实使用示例

以会议 `https://vc.feishu.cn/j/206594528` 为例：

```bash
# 1. 获取会议信息
python scripts/get_meeting_info.py \
  --meeting-link "https://vc.feishu.cn/j/206594528" \
  --output ./tmp/meeting.json

# 输出:
# {
#   "meeting_id": "206594528",
#   "topic": "2050新生论坛线上返场 WaytoAGI分享会",
#   "start_time": "2026-05-05T20:00:00+08:00",
#   "end_time": "2026-05-05T22:00:00+08:00",
#   "organizer": "🌈AJ",
#   "has_recording": true,
#   "has_minutes": true
# }

# 2. 获取逐字稿（实际通过飞书 docx API 读取）
# 脚本会自动调用 vc +notes 获取 verbatim_doc_token，
# 然后通过 docx API 读取完整逐字稿内容
python scripts/get_meeting_minutes.py \
  --meeting-id "206594528" \
  --output ./tmp/transcript.json

# 3. 生成视频脚本（使用 DeepSeek LLM）
python scripts/generate_script.py \
  --transcript ./tmp/transcript.json \
  --output ./tmp/script.json \
  --style "summary" \
  --provider deepseek

# 4. 生成视频（跳过截图，因为录制需要组织者权限）
python scripts/generate_meeting_video.py \
  --meeting-link "https://vc.feishu.cn/j/206594528" \
  --output-dir ./output \
  --style "summary" \
  --skip-screenshots
```

**实际测试数据：**
- 会议时长：2小时13分钟（19:55 - 22:08）
- 参会人数：363人
- 逐字稿：389行，含时间戳和发言人标记
- 智能纪要：76行结构化摘要，包含5个主题（AI安全、AI设计、AI创业、OPC实践、投资）
- 录制视频：❌ 需要组织者权限（HTTP 403）
- 逐字稿：✅ 成功获取
- 智能纪要：✅ 成功获取

## 详细流程

### 阶段 1：获取会议信息

#### 方式 A：用户提供会议链接

```bash
# 解析会议链接获取会议 ID
python scripts/get_meeting_info.py --meeting-link "https://vc.feishu.cn/j/123456789"
```

输出格式：
```json
{
  "meeting_id": "123456789",
  "topic": "产品周会",
  "start_time": "2024-01-15T10:00:00+08:00",
  "end_time": "2024-01-15T11:30:00+08:00",
  "organizer": "张三",
  "participants": ["李四", "王五"],
  "has_recording": true,
  "has_minutes": true
}
```

#### 方式 B：查询日程获取会议

```bash
# 查询某天的日程
lark-cli calendar +agenda --date "2024-01-15" --format json

# 或通过主脚本的 --date 参数自动查询日程
python scripts/generate_meeting_video.py --date "2026-01-15" --output-dir ./output
```

输出格式：
```json
{
  "date": "2024-01-15",
  "events": [
    {
      "event_id": "evt_123",
      "summary": "产品周会",
      "start_time": "10:00",
      "end_time": "11:30",
      "meeting_link": "https://vc.feishu.cn/j/123456789",
      "has_recording": true
    }
  ]
}
```

### 阶段 2：获取妙记和逐字稿

```bash
# 搜索妙记
lark-cli minutes +search --query "产品周会" --format json

# 或直接使用会议 ID 获取
python scripts/get_meeting_minutes.py --meeting-id "123456789"
```

输出格式：
```json
{
  "meeting_id": "123456789",
  "minutes_id": "min_456",
  "transcript": [
    {
      "speaker": "张三",
      "start_time": "00:00:15",
      "end_time": "00:00:45",
      "text": "大家好，今天我们讨论 Q1 的产品规划..."
    },
    {
      "speaker": "李四",
      "start_time": "00:00:46",
      "end_time": "00:01:20",
      "text": "我觉得优先级最高的是移动端优化..."
    }
  ],
  "summary": "本次会议讨论了 Q1 产品规划...",
  "video_url": "https://example.com/video.mp4"
}
```

### 阶段 3：生成精炼脚本

```bash
# 使用 LLM 提炼逐字稿为视频脚本
python scripts/generate_script.py \
  --transcript ./tmp/transcript.json \
  --output ./tmp/script.json \
  --style "summary" \
  --max-duration 180 \
  --provider deepseek
```

脚本格式：
```json
{
  "title": "产品周会总结",
  "duration_seconds": 180,
  "scenes": [
    {
      "scene_id": 1,
      "type": "title",
      "content": "产品周会 - Q1 规划",
      "duration": 3,
      "visual": "title_card"
    },
    {
      "scene_id": 2,
      "type": "content",
      "content": "本次会议确定了三个核心目标：移动端优化、性能提升、用户体验改进",
      "duration": 8,
      "visual": "bullet_points",
      "screenshot_needed": false
    },
    {
      "scene_id": 3,
      "type": "content",
      "content": "技术团队展示了最新的架构设计图",
      "duration": 6,
      "visual": "screenshot",
      "screenshot_needed": true,
      "screenshot_time": "00:15:30"
    }
  ]
}
```

### 阶段 4：智能截图

```bash
# 分析脚本，下载视频并截取关键帧
python scripts/capture_screenshots.py \
  --meeting-id "123456789" \
  --script ./tmp/script.json \
  --output-dir ./tmp/screenshots
```

截图逻辑：
1. 读取脚本中 `screenshot_needed: true` 的场景
2. 下载妙记视频（如果尚未下载）
3. 使用 ffmpeg 在指定时间点截取关键帧：
   ```bash
   ffmpeg -ss 00:15:30 -i meeting_video.mp4 -vframes 1 -q:v 2 screenshot_1.jpg
   ```
4. 将截图路径写回脚本

### 阶段 5：Remotion 视频合成

```bash
# 渲染视频（自动准备 Remotion 项目）
python scripts/render_video.py \
  --script ./tmp/script.json \
  --screenshots ./tmp/screenshots \
  --output ./output/meeting-summary.mp4
```

## Remotion 项目结构

> 以下结构由 `render_video.py` 动态生成，组件文件自动创建。

```
remotion-project/
├── src/
│   ├── index.tsx           # 入口文件
│   ├── Root.tsx            # Composition 注册
│   ├── compositions/
│   │   └── MeetingSummary.tsx    # 主视频组件（含所有场景类型）
│   └── data/
│       └── script.json           # 脚本数据
├── public/
│   └── screenshots/        # 截图资源
├── package.json
└── tsconfig.json
```

支持的场景类型：`title`（标题卡）、`content`（要点展示）、`screenshot`（截图展示）、`speaker`（发言人卡片）、`ending`（结束画面）。

## Composition 配置

```typescript
// src/Root.tsx
import { Composition } from 'remotion';
import { MeetingSummary } from './compositions/MeetingSummary';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MeetingSummary"
      component={MeetingSummary}
      durationInFrames={5400}  // 180秒 @ 30fps
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        script: require('./data/script.json'),
        screenshotsDir: './public/screenshots'
      }}
    />
  );
};
```

## 视频风格模板

### 1. 总结风格 (summary)
- 简洁的标题卡片
- 要点逐条展示（打字机效果）
- 关键截图淡入
- 总时长：2-3 分钟

### 2. 详细风格 (detailed)
- 完整的会议流程展示
- 每个发言者单独展示
- 更多截图和图表
- 总时长：5-10 分钟

### 3. 快速风格 (quick)
- 仅展示核心结论
- 快节奏切换
- 无截图，纯文字
- 总时长：30-60 秒

## 配置文件

### config.yaml

```yaml
feishu:
  app_id: ${FEISHU_APP_ID}
  app_secret: ${FEISHU_APP_SECRET}

llm:
  provider: deepseek
  model: deepseek-chat
  api_key: ${DEEPSEEK_API_KEY}
  temperature: 0.7

remotion:
  fps: 30
  width: 1920
  height: 1080
  default_duration: 180
  
video:
  default_style: "summary"
  max_duration: 300
  screenshot_quality: 2
  
ffmpeg:
  path: "ffmpeg"  # 系统路径
  screenshot_format: "jpg"
```

## 依赖安装

```bash
# Python 依赖
pip install pyyaml requests pillow openai

# Node.js 依赖（用于 Remotion）
npm install remotion @remotion/cli @remotion/player
```

## 命令行工具

### 完整命令

```bash
# 基础用法：通过会议链接生成视频
python scripts/generate_meeting_video.py \
  --meeting-link "https://vc.feishu.cn/j/123456789" \
  --output-dir ./output \
  --style "summary" \
  --duration 180 \
  --config ./config.yaml

# 通过日程查询生成视频
python scripts/generate_meeting_video.py \
  --date "2026-05-05" \
  --output-dir ./output \
  --style "summary"

# 快速生成（跳过截图，纯文字）
python scripts/generate_meeting_video.py \
  --meeting-link "https://vc.feishu.cn/j/206594528" \
  --output-dir ./output \
  --style "quick" \
  --skip-screenshots

# 详细风格（包含所有发言人观点）
python scripts/generate_meeting_video.py \
  --meeting-link "https://vc.feishu.cn/j/206594528" \
  --output-dir ./output \
  --style "detailed" \
  --duration 600
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--meeting-link` | 会议链接（如 https://vc.feishu.cn/j/123456789） | - |
| `--date` | 查询日程日期（YYYY-MM-DD） | - |
| `--output-dir` | 输出目录 | `./output` |
| `--style` | 视频风格：`summary`/`detailed`/`quick` | `summary` |
| `--duration` | 最大时长（秒），0=使用默认值 | 180 |
| `--provider` | LLM 提供商：`deepseek`/`kimi`/`glm`/`volcengine` | `deepseek` |
| `--config` | 配置文件路径 | `./config.yaml` |
| `--skip-screenshots` | 跳过截图步骤 | false |

## 参考资料

- `references/feishu-cli-reference.md` — 飞书 CLI 命令参考
- `references/remotion-guide.md` — Remotion 使用指南
- `references/ffmpeg-commands.md` — ffmpeg 截图命令参考
- `references/script-format.md` — 脚本 JSON 格式规范
