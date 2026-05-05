# Feishu Skills Collection

飞书技能集合，包含智能宠物聊天机器人和会议总结视频生成两个核心技能。

## 🐾 Feishu Pet（飞书宠物）

智能聊天机器人 + 动画精灵表生成 + **桌面宠物**

```bash
# 启动后台守护进程（飞书消息监听）
cd skills/feishu-pet
python scripts/pet_daemon.py start --config pet-config.yaml

# 启动桌面宠物（macOS）
python scripts/desktop_pet_app.py --config pet-config.yaml
```

**主要功能**：
- ✅ WebSocket 实时消息监听
- ✅ LLM 智能对话响应
- ✅ 精灵表生成管线（AI 生图 → 帧提取 → Atlas 合成）
- ✅ **桌面宠物**（透明窗口、常驻顶层、动画播放）

## 🎬 Feishu Remotion（飞书会议视频）

会议总结视频生成：获取妙记 → 脚本提炼 → 视频合成

```bash
python skills/feishu-remotion/scripts/generate_meeting_video.py \
  --meeting-link "https://vc.feishu.cn/j/..." \
  --output-dir ./output
```

**主要功能**：
- ✅ 飞书会议信息获取
- ✅ 妙记内容提取
- ✅ 脚本自动生成
- ✅ Remotion 视频渲染

## 文档

| 文档 | 描述 |
|------|------|
| [docs/README.md](./docs/README.md) | 项目概述和快速开始 |
| [docs/architecture.md](./docs/architecture.md) | 架构设计和数据流 |
| [docs/api-reference.md](./docs/api-reference.md) | LLM API、生图 API、飞书 CLI |
| [docs/usage-guide.md](./docs/usage-guide.md) | 安装、配置、启动、排错 |
| [docs/hatch-pet-pipeline.md](./docs/hatch-pet-pipeline.md) | 精灵表生成管线详解 |

## 目录结构

```
skills/
├── feishu-pet/               # Feishu Pet skill (19 个脚本)
│   ├── SKILL.md              # 核心技能定义
│   ├── LICENSE.txt
│   ├── config.example.yaml   # 配置模板
│   ├── agents/openai.yaml
│   ├── assets/               # 静态资源
│   ├── references/           # 技能参考文档
│   ├── scripts/              # Python 脚本
│   │   ├── pet_daemon.py     # 后台守护进程
│   │   ├── desktop_pet_app.py # 桌面宠物主程序
│   │   ├── pet_display.py    # PyGame 宠物显示模块
│   │   └── ...               # 精灵表生成管线
│   └── evals/               # 测试用例
│
└── feishu-remotion/          # Feishu Remotion skill (6 个脚本)
    ├── SKILL.md
    ├── config.example.yaml
    ├── references/           # 参考文档
    ├── scripts/              # Python 脚本
    └── tmp/remotion-project/ # Remotion 视频项目
```

## 技能脚本清单

### feishu-pet (19 个脚本)

| 脚本 | 功能 |
|------|------|
| `pet_daemon.py` | 后台守护进程，管理宠物生命周期 |
| `desktop_pet_app.py` | 桌面宠物主程序（macOS） |
| `pet_display.py` | PyGame 透明窗口宠物显示 |
| `config_manager.py` | 配置文件管理 |
| `state_manager.py` | 状态持久化管理 |
| `llm_client.py` | LLM API 客户端 |
| `event_listener.py` | 飞书事件监听 |
| `message_handler.py` | 消息处理和响应 |
| `prepare_pet_run.py` | 准备宠物生成任务 |
| `generate_pet_images.py` | AI 生图 |
| `record_imagegen_result.py` | 记录生成结果 |
| `extract_strip_frames.py` | 提取帧序列 |
| `compose_atlas.py` | 合成精灵表 |
| `validate_atlas.py` | 验证精灵表 |
| `make_contact_sheet.py` | 生成联系表 |
| `render_animation_videos.py` | 渲染动画视频 |
| `derive_running_left.py` | 生成向左跑帧 |
| `package_custom_pet.py` | 打包自定义宠物 |
| `queue_pet_repairs.py` | 队列修复管理 |

### feishu-remotion (6 个脚本)

| 脚本 | 功能 |
|------|------|
| `generate_meeting_video.py` | 生成会议总结视频主入口 |
| `get_meeting_info.py` | 获取会议信息 |
| `get_meeting_minutes.py` | 获取妙记内容 |
| `generate_script.py` | 生成视频脚本 |
| `capture_screenshots.py` | 截图捕获 |
| `render_video.py` | Remotion 视频渲染 |

## 快速开始

```bash
# 1. 安装依赖
npm install -g @larksuite/cli
pip install pyyaml requests pillow pygame

# 2. 配置飞书 CLI
lark-cli config init
lark-cli auth login --recommend

# 3. 配置技能
cd skills/feishu-pet
cp config.example.yaml pet-config.yaml
# 编辑 pet-config.yaml 填入 API keys

# 4. 启动桌面宠物
python scripts/desktop_pet_app.py --config pet-config.yaml
```

## 许可证

MIT License - 详见 [LICENSE](./LICENSE)