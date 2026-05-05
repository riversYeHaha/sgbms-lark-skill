# 架构设计

## 整体架构

```
┌─────────────────────────────────────────────┐
│                  Feishu Pet                  │
├─────────────────┬───────────────────────────┤
│   聊天系统       │       生图系统            │
│   (Chat)        │       (Image Gen)         │
├─────────────────┼───────────────────────────┤
│ PetDaemon       │ prepare_pet_run           │
│  ├─EventListener│ generate_pet_images       │
│  ├─MessageHandler│ record_imagegen_result   │
│  ├─LLMClient    │ extract_strip_frames      │
│  ├─StateManager │ compose_atlas             │
│  └─ConfigManager│ validate_atlas            │
│                 │ make_contact_sheet         │
│                 │ render_animation_videos    │
│                 │ queue_pet_repairs          │
│                 │ derive_running_left        │
│                 └─ package_custom_pet        │
├─────────────────┴───────────────────────────┤
│              外部依赖                        │
│  lark-cli  │  LLM API  │  Image API         │
└─────────────────────────────────────────────┘
```

## 聊天系统数据流

```
┌──────────┐    NDJSON    ┌──────────────┐    event    ┌───────────────┐
│ lark-cli │─────────────▶│EventListener │───────────▶│MessageHandler │
│ +subscribe│             │  (queue)     │            │               │
└──────────┘              └──────────────┘            └───────┬───────┘
                                                             │
                              ┌──────────┐                   │
                              │  LLM API │◀──────────────────┤
                              └────┬─────┘    chat()         │
                                   │                         │
                                   ▼                         ▼
                              ┌──────────┐           ┌──────────────┐
                              │lark-cli  │           │ StateManager │
                              │+reply    │           │  (JSON)      │
                              └──────────┘           └──────────────┘
```

## 组件职责

### PetDaemon
- 应用入口，管理生命周期
- 协调 EventListener、MessageHandler、LLMClient
- 处理 SIGINT/SIGTERM 优雅退出
- 定时更新头像（情绪映射）
- 心跳日志

### EventListener
- 封装 `lark-cli event +subscribe --compact --quiet`
- 子进程管理 + stdout NDJSON 行读取
- 线程安全的 Queue 缓冲

### MessageHandler
- 解析 compact 格式事件
- 检测 @提及、加急关键词、P2P 私聊
- 意图识别（chat / generate / urgent / question）
- 构建 LLM 上下文（最近 N 条历史）
- 调用 `lark-cli im +messages-reply --as bot`

### LLMClient
- 多提供商统一接口（OpenAI-compatible）
- 情绪分析（mood detection）
- 意图识别（intent detection）

### StateManager
- JSON 文件读写
- 对话历史（按 chat_id 隔离，最多 50 条）
- 统计数据（消息数、回复数、加急数、生图数）
- 情绪状态和头像信息

### ConfigManager
- YAML 配置加载
- `${ENV_VAR}` 环境变量替换
- 支持 `${ENV_VAR:default_value}` 默认值

## 生图系统数据流

```
prepare ──▶ generate ──▶ record ──▶ extract ──▶ compose ──▶ validate
                                                              │
                                                              ▼
                  package ◀── repair ◀──▶ contact_sheet ──▶ videos
```

## 情绪到帧映射

```
情绪分析 (LLM) ──▶ mood: "happy" ──▶ config.mapping ──▶ "idle:1"
                                                           │
                    update_interval: 60s                    │
                                                           ▼
              spritesheet ──▶ crop(1*192, 0*208) ──▶ avatar-current.png
```

## 聊天触发生图流程

```
用户: @小Lark 生成新形象
        │
        ▼
MessageHandler.detect_intent() → "generate"
        │
        ▼
回复提示用户 + 记录到 state.stats.generations_triggered
        │
        ▼
用户手动执行: prepare → generate → ... → package
        │
        ▼
spritesheet 生成完毕 → 提取 idle:0 帧 → 更新飞书头像
```
