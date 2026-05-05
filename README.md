# Skills Collection

飞书宠物 (Feishu Pet) — 智能聊天机器人 + 动画精灵表生成

```bash
cd skills/feishu-pet
python scripts/pet_daemon.py start --config pet-config.yaml
```

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
└── feishu-pet/               # Feishu Pet skill
    ├── SKILL.md              # 核心技能定义
    ├── LICENSE.txt
    ├── config.example.yaml   # 配置模板
    ├── agents/openai.yaml
    ├── assets/               # 静态资源
    ├── references/           # 技能参考文档
    ├── scripts/              # Python 脚本 (18 个)
    └── evals/               # 测试用例
```
