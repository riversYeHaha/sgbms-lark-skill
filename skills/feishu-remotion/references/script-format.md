# 脚本 JSON 格式规范

## 概述

脚本 JSON 是连接飞书会议内容和 Remotion 视频的桥梁。由 LLM 根据逐字稿生成，驱动视频渲染。

## 完整格式

```json
{
  "version": "1.0",
  "metadata": {
    "title": "产品周会总结",
    "meeting_id": "123456789",
    "meeting_topic": "产品周会",
    "meeting_date": "2024-01-15",
    "duration_seconds": 180,
    "style": "summary",
    "total_scenes": 5
  },
  "scenes": [
    {
      "scene_id": 1,
      "type": "title",
      "title": "产品周会 - Q1 规划",
      "subtitle": "2024年1月15日",
      "duration": 3,
      "transition": "fade_in",
      "visual": {
        "type": "title_card",
        "background": "gradient_dark",
        "animation": "scale_up"
      }
    },
    {
      "scene_id": 2,
      "type": "content",
      "content": "本次会议确定了三个核心目标",
      "bullet_points": [
        "移动端优化",
        "性能提升",
        "用户体验改进"
      ],
      "duration": 8,
      "transition": "slide_in",
      "visual": {
        "type": "bullet_points",
        "animation": "typewriter",
        "highlight_color": "#4CAF50"
      }
    },
    {
      "scene_id": 3,
      "type": "screenshot",
      "content": "技术团队展示了最新的架构设计图",
      "screenshot": {
        "needed": true,
        "timestamp": "00:15:30",
        "path": "./screenshots/screenshot_001.jpg",
        "caption": "系统架构图"
      },
      "duration": 6,
      "transition": "fade_in",
      "visual": {
        "type": "image_show",
        "animation": "zoom_in",
        "caption_position": "bottom"
      }
    },
    {
      "scene_id": 4,
      "type": "speaker",
      "speaker": "张三",
      "content": "我们的目标是提升用户留存率到 80%",
      "duration": 5,
      "transition": "slide_in",
      "visual": {
        "type": "quote_card",
        "animation": "fade_in",
        "avatar": true
      }
    },
    {
      "scene_id": 5,
      "type": "ending",
      "content": "感谢参与，下周见！",
      "duration": 3,
      "transition": "fade_out",
      "visual": {
        "type": "ending_card",
        "animation": "fade_out"
      }
    }
  ]
}
```

## 字段说明

### 根级别

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | 是 | 脚本版本，当前 "1.0" |
| `metadata` | object | 是 | 元数据 |
| `scenes` | array | 是 | 场景列表 |

### Metadata

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 视频标题 |
| `meeting_id` | string | 否 | 会议 ID |
| `meeting_topic` | string | 否 | 会议主题 |
| `meeting_date` | string | 否 | 会议日期 (YYYY-MM-DD) |
| `duration_seconds` | number | 是 | 预计视频时长（秒） |
| `style` | string | 是 | 视频风格 |
| `total_scenes` | number | 是 | 场景总数 |

### Scene

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scene_id` | number | 是 | 场景序号 |
| `type` | string | 是 | 场景类型 |
| `content` | string | 是 | 场景内容/文案 |
| `duration` | number | 是 | 场景时长（秒） |
| `transition` | string | 否 | 转场效果 |
| `visual` | object | 是 | 视觉配置 |

### Scene Types

| 类型 | 说明 | 额外字段 |
|------|------|----------|
| `title` | 标题场景 | `title`, `subtitle` |
| `content` | 内容场景 | `bullet_points` |
| `screenshot` | 截图场景 | `screenshot` |
| `speaker` | 发言人场景 | `speaker` |
| `ending` | 结尾场景 | - |

### Visual Config

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 视觉类型 |
| `animation` | string | 是 | 动画效果 |
| `background` | string | 否 | 背景样式 |
| `highlight_color` | string | 否 | 高亮颜色 |

### Screenshot Config

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `needed` | boolean | 是 | 是否需要截图 |
| `timestamp` | string | 条件 | 视频时间点 (HH:MM:SS) |
| `path` | string | 条件 | 截图文件路径 |
| `caption` | string | 否 | 截图说明 |

## 风格模板

### summary (总结)

```json
{
  "style": "summary",
  "duration_seconds": 180,
  "scenes": [
    { "type": "title", "duration": 3 },
    { "type": "content", "duration": 8 },
    { "type": "screenshot", "duration": 6 },
    { "type": "content", "duration": 8 },
    { "type": "ending", "duration": 3 }
  ]
}
```

特点：
- 2-3 分钟
- 核心要点展示
- 少量关键截图
- 快节奏

### detailed (详细)

```json
{
  "style": "detailed",
  "duration_seconds": 600,
  "scenes": [
    { "type": "title", "duration": 5 },
    { "type": "content", "duration": 15 },
    { "type": "speaker", "duration": 10 },
    { "type": "screenshot", "duration": 10 },
    { "type": "content", "duration": 15 },
    { "type": "speaker", "duration": 10 },
    { "type": "ending", "duration": 5 }
  ]
}
```

特点：
- 5-10 分钟
- 完整内容展示
- 多个发言人
- 详细截图

### quick (快速)

```json
{
  "style": "quick",
  "duration_seconds": 45,
  "scenes": [
    { "type": "title", "duration": 2 },
    { "type": "content", "duration": 5 },
    { "type": "ending", "duration": 2 }
  ]
}
```

特点：
- 30-60 秒
- 仅核心结论
- 无截图
- 极简风格

## 转场效果

| 效果 | 说明 |
|------|------|
| `fade_in` | 淡入 |
| `fade_out` | 淡出 |
| `slide_in` | 滑入 |
| `slide_out` | 滑出 |
| `scale_up` | 放大 |
| `scale_down` | 缩小 |

## 动画效果

| 效果 | 说明 |
|------|------|
| `typewriter` | 打字机 |
| `fade_in` | 淡入 |
| `slide_in` | 滑入 |
| `zoom_in` | 放大 |
| `scale_up` | 放大出现 |
| `bounce` | 弹跳 |

## 视觉类型

| 类型 | 说明 |
|------|------|
| `title_card` | 标题卡片 |
| `bullet_points` | 要点列表 |
| `image_show` | 图片展示 |
| `quote_card` | 引用卡片 |
| `ending_card` | 结尾卡片 |
