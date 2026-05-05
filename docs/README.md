# 飞书宠物 (Feishu Pet) 技术文档

## 项目概述

飞书宠物是一个 OpenCode skill，将智能聊天机器人与动画精灵表生成系统整合为一体。

### 两大系统

| 系统 | 功能 | 核心依赖 |
|------|------|---------|
| 聊天系统 | WebSocket 消息监听、@提及响应、加急处理、LLM 对话 | `lark-cli`, DeepSeek/Kimi/GLM/火山引擎 |
| 生图系统 | hatch-pet 风格动画精灵表生成 (8x9 atlas) | 火山引擎 seedream / 万相2.7 |

### 文档索引

| 文档 | 内容 |
|------|------|
| [architecture.md](./architecture.md) | 架构设计、组件关系、数据流 |
| [api-reference.md](./api-reference.md) | LLM API、生图 API、飞书 CLI 完整参考 |
| [usage-guide.md](./usage-guide.md) | 安装、配置、启动、生成、排错 |
| [hatch-pet-pipeline.md](./hatch-pet-pipeline.md) | 精灵表生成管线详解 |

## 快速开始

```bash
# 安装
pip install pyyaml requests pillow

# 初始化配置
cd skills/feishu-pet
cp config.example.yaml pet-config.yaml

# 编辑 pet-config.yaml，填入 API keys:
#   - DEEPSEEK_API_KEY (LLM)
#   - FEISHU_APP_ID / FEISHU_APP_SECRET (飞书)
#   - ARK_API_KEY (火山引擎生图) 或 DASHSCOPE_API_KEY (万相)

# 启动宠物
python scripts/pet_daemon.py start --config pet-config.yaml
```

## 技术栈

| 层次 | 技术 |
|------|------|
| 运行时 | Python 3.8+ |
| CLI 封装 | `lark-cli` (npm: `@larksuite/cli`) |
| 消息监听 | WebSocket 长连接 |
| LLM | REST API (OpenAI-compatible) |
| 生图 | REST API (火山引擎 seedream / 万相2.7) |
| 图像处理 | Pillow (PIL) |
| 视频渲染 | ffmpeg |
| 配置 | YAML |
| 状态持久化 | JSON 文件 |
