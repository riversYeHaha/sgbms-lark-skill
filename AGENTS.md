# AGENTS.md — Feishu Skills Collection

OpenCode skills 仓库，包含飞书相关的自动化技能。技能是独立的一等公民，每个技能目录自包含。

## 仓库结构

```
skills/<skill-name>/          ← 每个 skill 一个目录
  SKILL.md                    ← 核心定义（触发条件、工作流、配置）
  scripts/                    ← Python 3.8+ 脚本（命令行调用，不做包导入）
  references/                 ← 参考文档
  evals/evals.json            ← skill-creator 测试用例
  tests/                      ← Python unittest 单元测试（当前被 .gitignore 屏蔽）
  config.example.yaml         ← 配置模板（不含密钥，被 git 跟踪）
feishu-pet.skill              ← 打包的 skill 文件（提交到仓库）
feishu-remotion.skill         ← 打包的 skill 文件（提交到仓库）
dist/                         ← 打包产物 .zip（gitignored，不提交）
.sisyphus/plans/              ← Prometheus 规划文件
.sisyphus/drafts/             ← 设计草稿
docs/                         ← 技术文档（架构、API 参考、使用指南）
```

## 技能列表

| 技能 | 功能 | 核心依赖 |
|------|------|---------|
| `feishu-pet` (20 scripts) | 飞书智能宠物：WebSocket 消息监听 + LLM 对话 + 精灵表生成 | `lark-cli`, LLM API, 生图 API |
| `feishu-remotion` (6 scripts) | 飞书会议→总结视频：获取妙记→脚本提炼→视频合成 | `lark-cli`, Remotion, ffmpeg |

## 开发命令

### 安装依赖

```
# 飞书 CLI（npm 全局依赖，所有 skill 的硬性前置）
npm install -g @larksuite/cli
lark-cli config init
lark-cli auth login --recommend

# Python 运行时依赖（无 requirements.txt，手动安装）
pip install pyyaml requests pillow openai

# Remotion 相关（仅 feishu-remotion）
npm install remotion @remotion/cli
brew install ffmpeg
```

### 运行技能脚本

```bash
# feishu-pet：启动宠物守护进程
cd skills/feishu-pet
cp config.example.yaml pet-config.yaml  # 编辑填入 API keys
python scripts/pet_daemon.py start --config pet-config.yaml

# feishu-remotion：通过会议链接生成视频（详细风格）
python skills/feishu-remotion/scripts/generate_meeting_video.py \
  --meeting-link "https://vc.feishu.cn/j/..." \
  --output-dir ./output \
  --style "summary"

# 快速模式（跳过截图，纯文字视频）
python skills/feishu-remotion/scripts/generate_meeting_video.py \
  --meeting-link "https://vc.feishu.cn/j/..." \
  --output-dir ./output \
  --style "quick" \
  --skip-screenshots
```

### 打包与测试

```bash
# 使用 skill-creator 打包 skill
python /path/to/skill-creator/scripts/package_skill.py skills/<name>

# 运行 evals 测试（skill-creator 框架）
python /path/to/skill-creator/scripts/run_evals.py \
  --skill skills/<name> \
  --evals skills/<name>/evals/evals.json

# 运行单元测试（在 skill 目录内）
cd skills/<name>
python -m unittest tests.test_remotion -v
```

**没有 `pip install -r requirements.txt`、`make`、`npm test` 或 CI 流程**。测试通过 skill-creator 的 evals 框架和 Python unittest 进行。

## 配置约定

### YAML 文件规则

`.gitignore` 屏蔽所有 `*.yaml` / `*.yml`，只有以下例外会被跟踪：

- `config.example.yaml` 和 `config.example.yml` — 配置模板（不含真实密钥）
- `agents/*.yaml` 和 `agents/*.yml` — agent 定义

**新 YAML 文件默认不被 git 跟踪**，除非需要作为模板提交。

### 环境变量替换

ConfigManager 支持 `${ENV_VAR}` 和 `${ENV_VAR:default_value}` 两种语法。每个技能使用的环境变量不同：

- `DEEPSEEK_API_KEY` — LLM (DeepSeek)
- `MOONSHOT_API_KEY` — LLM (Kimi/Moonshot)
- `GLM_API_KEY` — LLM (智谱 GLM)
- `ARK_API_KEY` — 火山引擎（生图/LLM）
- `FEISHU_APP_ID`, `FEISHU_APP_SECRET` — 飞书应用凭证
- `DASHSCOPE_API_KEY` — 万相生图

### LLM 提供商

所有 LLM 使用 OpenAI-compatible REST API，支持四种提供商：DeepSeek、Kimi (Moonshot)、GLM (智谱)、火山引擎。Base URL 和模型名参见 `docs/api-reference.md`。

## 技能开发约定

1. **每个 skill 自包含**：所有脚本、配置、文档在一个目录下，不跨 skill 引用代码。
2. **脚本通过命令行调用**：不要假设脚本会被 Python `import`；它们设计为 `python scripts/xxx.py --arg value` 独立运行。
3. **SKILL.md 格式**：YAML frontmatter (`name`, `description`) + Markdown 正文。`description` 包含触发关键词列表。
4. **新增 skill**：在 `skills/` 下创建目录，最小结构为 `SKILL.md` + `scripts/`。参考现有 skill 的结构。
5. **打包产物**：`.skill` 文件提交到仓库根目录；`.zip` 放到 `dist/`（gitignored）。

## Git 约定

- **Commit 风格**：PLAIN English，无 semantic prefix。示例：`Add feishu-remotion Python automation scripts`、`Update LICENSE files with proper copyright year`
- **Co-author**：每个 commit 附带 `Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>`
- **分支策略**：功能分支 → merge 到 `main`（fast-forward），分支惯例为 `skill-<name>`
- **Worktree**：大功能开发使用 `git worktree` 隔离，完成后清理

## 已知陷阱

### 飞书 CLI 命令

- **飞书 CLI 是 npm 全局工具，不是 Python 包**。如果遇到 `lark-cli: command not found`，用 `npm install -g @larksuite/cli` 安装。
- **大部分命令需要用户授权**。`vc +search`、`vc +notes`、`vc +recording`、`minutes +search` 等命令仅支持 `--as user` 身份（Bot 不可用）。若遇到 `need_user_authorization` 错误，需要 `lark-cli auth login --recommend` 以用户身份重新登录。
- **`vc +detail` 不存在**。获取会议信息应使用 `vc +search --query <meeting_id>`，返回结构为 `{"meetings": [{...}]}`。
- **`vc +notes` 返回的是 doc token**，不是完整内容。获取逐字稿需要两步：先 `vc +notes --meeting-ids <id>` 获取 `verbatim_doc_token`，再用 docx API `/open-apis/docx/v1/documents/<token>/blocks` 读取内容。
- **`minutes +search` 可能搜不到**。如果空结果，使用 `vc +notes` 作为替代路径。
- **`vc +recording --meeting-ids` 是 `--meeting-ids`**（复数），不是 `--meeting-id`。录制下载需要组织者权限，否则返回 HTTP 403。
- **`calendar +agenda` 使用 `--start` / `--end`**（ISO 8601 格式），不是 `--date`。

### 配置陷阱

- **YAML 配置文件默认不被 git 跟踪**。如果新增了应提交的 YAML 模板，需要在 `.gitignore` 中添加例外规则。
- **`*.json` 被 gitignore 屏蔽**，只有 `!evals/*.json` 例外。`tests/` 目录也被 `.gitignore` 屏蔽。
- **`scripts/__init__.py`** 包含 Python 脚本列表的 `__all__` 声明，新增脚本时需要同步更新。

### 系统依赖

- **ffmpeg 是系统级依赖**（通过 brew/apt 安装），不是 Python 包。feishu-remotion 的截图功能依赖它。
- **Remotion 渲染需要 Node.js 18+** 和浏览器环境（headless chromium）。
- **没有 requirements.txt** — Python 依赖通过文档说明，需要手动 `pip install`。
- **`openai` 包**是 feishu-remotion 的 `generate_script.py` 运行时依赖，容易遗漏。
