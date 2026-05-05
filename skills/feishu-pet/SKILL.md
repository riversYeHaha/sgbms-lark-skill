---
name: feishu-pet
description: 飞书智能宠物 - 通过 WebSocket 长连接实时监听飞书消息，自动响应@提及、加急消息和私聊，支持多 LLM 提供商（DeepSeek/Kimi/GLM/火山引擎），可生成独特的宠物动画精灵表（火山引擎/万相生图API），头像随对话情绪自动切换。当用户需要飞书机器人自动回复、智能客服、消息监听、群聊助手或生成宠物形象时使用。触发关键词：飞书宠物、消息监听、自动回复、群聊机器人、飞书助手、宠物形象、生成头像。
---

# 飞书宠物 (Feishu Pet)

## 概述

创建一个在飞书环境中运行的智能宠物，具备两大核心能力：

1. **智能对话**：通过 WebSocket 长连接实时监听消息，自动响应 @提及、加急消息和私聊，基于大模型进行智能对话
2. **形象生成**：参考 hatch-pet 完整管线，生成动画精灵表 (8x9 atlas)，支持从飞书聊天中触发生图，头像随情绪自动切换

## 前置条件

1. 安装飞书 CLI：`npm install -g @larksuite/cli`
2. 初始化配置：`lark-cli config init`
3. 登录：`lark-cli auth login --recommend`
4. 在飞书开放平台配置事件订阅（长连接模式）
5. Python 3.8+，安装依赖：`pip install pyyaml requests pillow`

## 核心架构

### 两大系统

```
feishu-pet
├── 消息处理系统 (Chat System)
│   ├── PetDaemon      — 主进程，管理生命周期
│   ├── EventListener  — WebSocket 事件监听
│   ├── MessageHandler — 消息解析、路由、回复
│   ├── LLMClient      — 多 LLM 提供商统一接口
│   ├── StateManager   — JSON 状态持久化
│   └── ConfigManager  — YAML 配置管理
│
└── 形象生成系统 (Image System)
    ├── prepare_pet_run            — 准备生成任务
    ├── generate_pet_images        — 调用生图 API
    ├── record_imagegen_result     — 记录生成结果
    ├── extract_strip_frames       — 帧提取（色度键背景去除）
    ├── compose_atlas             — 图集合成 (8x9)
    ├── validate_atlas            — QA 验证
    ├── make_contact_sheet        — 联系表
    ├── render_animation_videos   — 动画预览
    ├── queue_pet_repairs         — 修复队列
    ├── derive_running_left       — 镜像生成 running-left
    └── package_custom_pet        — 打包
```

### 消息处理流程

```
WebSocket → Parse → Filter → Route → LLM → Reply → Update State
```

**触发条件**:
- `@宠物名称` — 提及
- 加急消息 — urgent flag
- P2P 私聊 — 无条件响应
- `@宠物 生成新形象` / `@宠物 换个造型` — 触发生图

### 形象生成流程

```
用户触发 → prepare_pet_run → generate_pet_images (基础+9行)
→ record_imagegen_result → extract_strip_frames
→ compose_atlas → validate_atlas → make_contact_sheet
→ render_animation_videos → package_custom_pet
→ 提取 idle 帧更新飞书头像
```

## 快速开始

### 1. 创建配置

```bash
cp config.example.yaml pet-config.yaml
# 编辑 pet-config.yaml，填入 API keys
```

### 2. 启动宠物

```bash
# 前台运行
python scripts/pet_daemon.py --config pet-config.yaml

# 后台运行
nohup python scripts/pet_daemon.py --config pet-config.yaml > pet.log 2>&1 &
```

### 3. 生成宠物形象

```bash
# 准备生成任务
python scripts/prepare_pet_run.py \
  --pet-name "小 Lark" \
  --description "一只活泼的蓝色小鸟" \
  --output-dir ./pet-run

# 生成基础形象
python scripts/generate_pet_images.py \
  --run-dir ./pet-run \
  --provider volcengine \
  --states base

# 记录结果
python scripts/record_imagegen_result.py \
  --run-dir ./pet-run \
  --job-id base \
  --source ./generated/base.png

# 生成所有行条
python scripts/generate_pet_images.py \
  --run-dir ./pet-run \
  --states all

# 提取帧
python scripts/extract_strip_frames.py \
  --run-dir ./pet-run \
  --states all

# 合成图集
python scripts/compose_atlas.py \
  --frames-root ./pet-run/frames \
  --output ./pet-run/final/spritesheet.png \
  --webp-output ./pet-run/final/spritesheet.webp

# 验证
python scripts/validate_atlas.py \
  ./pet-run/final/spritesheet.png \
  --json-out ./pet-run/final/validation.json
```

### 4. 聊天中触发生图

```
用户在飞书发送：@小Lark 给我生成一个新形象

宠物：收到！正在为您生成新形象...
      1/4 准备素材 ✅
      2/4 生成基础形象 ✅
      3/4 生成动画姿势 ✅
      4/4 合成并打包 ✅
      新形象已生成！🖼️
```

## 配置文件

### pet-config.yaml

```yaml
pet:
  name: "小 Lark"
  personality: "活泼、乐于助人、技术专家"

llm:
  provider: deepseek
  model: deepseek-chat
  api_key: ${DEEPSEEK_API_KEY}
  temperature: 0.7
  max_tokens: 2000

feishu:
  app_id: ${FEISHU_APP_ID}
  app_secret: ${FEISHU_APP_SECRET}
  event_types:
    - im.message.receive_v1

image_generation:
  provider: "volcengine"
  model: "doubao-seedream-5-0-260128"
  api_key: ${ARK_API_KEY}
  size: "2K"
  atlas:
    columns: 8
    rows: 9
    cell_width: 192
    cell_height: 208
  chroma_key: "#00FF00"
  chroma_threshold: 30

behavior:
  auto_reply: true
  reply_delay: 1
  context_window: 10

mood:
  enabled: true
  update_interval: 60
  mapping:
    online: "idle:0"
    happy: "idle:1"
    busy: "waiting:0"
    away: "idle:5"
    sad: "failed:0"
    thinking: "review:0"

state_file: "./pet-state.json"
```

## 情绪到精灵表帧映射

| 情绪 | 精灵表行 | 帧号 | 触发条件 |
|------|---------|------|---------|
| 在线 | idle (row 0) | 0 | 默认状态 |
| 开心 | idle (row 0) | 1-2 | 用户夸奖、积极消息 |
| 忙碌 | waiting (row 6) | 0 | 同时处理多个请求 |
| 离开 | idle (row 0) | 5 | 长时间未活动 |
| 难过 | failed (row 5) | 0 | 用户批评、错误 |
| 思考 | review (row 8) | 0 | 复杂问题需要时间 |

## 受支持的 LLM 提供商

| Provider | Base URL | 模型示例 |
|----------|----------|---------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat`, `deepseek-reasoner` |
| Kimi | `https://api.moonshot.cn/v1` | `moonshot-v1-8k`, `moonshot-v1-32k` |
| GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4`, `glm-4-plus` |
| 火山引擎 | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-pro`, `doubao-lite` |

## 受支持的生图提供商

| Provider | Base URL | 模型示例 |
|----------|----------|---------|
| 火山引擎 | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-seedream-5-0-260128` |
| 万相 | `https://dashscope.aliyuncs.com/api/v1` | `wan2.7-image-pro`, `wan2.7-image` |

### 火山引擎 API 示例

```bash
curl -X POST https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "生成一个可爱的像素风宠物精灵",
    "sequential_image_generation": "disabled",
    "response_format": "url",
    "size": "2K",
    "stream": false,
    "watermark": true
  }'
```

### 万相 API 示例

```bash
curl --location 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation' \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $DASHSCOPE_API_KEY" \
  --data '{
    "model": "wan2.7-image-pro",
    "input": {
      "messages": [
        {"role": "user", "content": [{"text": "生成一个可爱的像素风宠物精灵"}]}
      ]
    },
    "parameters": {"size": "2K", "n": 1, "watermark": false, "thinking_mode": true}
  }'
```

## 生成风格

遵循 hatch-pet 的 Codex 数字宠物风格：
- 像素艺术风格的萌宠精灵
- 紧凑 Q 版比例，厚实可读的剪影
- 1-2 px 深色轮廓，可见的阶梯/像素边缘
- 有限调色板，扁平 cel 着色
- 简洁的表情和迷你小肢体
- 色度键纯色背景（便于透明通道提取）

## 安全考虑

1. **API Key 管理**：使用环境变量，不硬编码
2. **消息过滤**：过滤敏感信息，不记录隐私数据
3. **速率限制**：防止 API 滥用
4. **权限控制**：只响应授权用户

## 参考资料

- `references/feishu-event-reference.md` — 飞书事件订阅详情
- `references/feishu-im-reference.md` — 飞书 IM API 详解
- `references/llm-providers.md` — LLM 提供商配置
- `references/avatar-generation.md` — 形象生成流程
