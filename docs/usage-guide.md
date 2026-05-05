# 使用指南

## 安装

### 前置依赖

```bash
# Python 3.8+
python3 --version

# 飞书 CLI
npm install -g @larksuite/cli

# Python 依赖
pip install pyyaml requests pillow

# ffmpeg（用于动画预览视频）
brew install ffmpeg  # macOS
# apt install ffmpeg # Linux
```

### 飞书配置

```bash
# 初始化飞书 CLI
lark-cli config init
# 按提示输入 App ID 和 App Secret

# 登录
lark-cli auth login --recommend
```

### 开放平台配置

1. 登录 [飞书开放平台](https://open.feishu.cn)
2. 创建企业自建应用
3. 事件与回调 → 订阅方式 → 选择「使用长连接接收事件」
4. 添加事件: `im.message.receive_v1`
5. 启用权限: `im:message:receive_as_bot`
6. 发布应用

---

## 配置

### 创建配置文件

```bash
cd skills/feishu-pet
python scripts/pet_daemon.py init --name "小飞" --personality "活泼的技术助手"
```

### 编辑 pet-config.yaml

```yaml
pet:
  name: "小飞"
  personality: "活泼、乐于助人、技术专家"

llm:
  provider: deepseek         # deepseek | kimi | glm | volcengine
  model: deepseek-chat
  api_key: ${DEEPSEEK_API_KEY}  # 或直接填写 key
  temperature: 0.7
  max_tokens: 2000

feishu:
  app_id: ${FEISHU_APP_ID}
  app_secret: ${FEISHU_APP_SECRET}
  event_types:
    - im.message.receive_v1

image_generation:
  # 火山引擎: doubao-seedream-5-0-260128, env: ARK_API_KEY
  # 万相: wan2.7-image-pro / wan2.7-image, env: DASHSCOPE_API_KEY
  provider: "volcengine"
  model: "doubao-seedream-5-0-260128"
  api_key: ${ARK_API_KEY}
  size: "2K"
  chroma_key: "#00FF00"
  chroma_threshold: 30

behavior:
  auto_reply: true
  reply_delay: 1
  context_window: 10

mood:
  enabled: true
  update_interval: 60

state_file: "./pet-state.json"
```

### 设置环境变量

```bash
export DEEPSEEK_API_KEY="sk-xxx"
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
export ARK_API_KEY="xxx"
```

---

## 启动宠物

### 前台运行

```bash
python scripts/pet_daemon.py start --config pet-config.yaml
```

输出:
```
[小飞] 宠物已上线！
[小飞] LLM: deepseek/deepseek-chat
[小飞] 情绪切换: 启用
[小飞] 正在监听消息... (Ctrl+C 退出)
[小飞] 心跳: 100 事件, 95 回复, 情绪: online
```

### 后台运行

```bash
nohup python scripts/pet_daemon.py start --config pet-config.yaml > pet.log 2>&1 &

# 查看日志
tail -f pet.log

# 查看状态
python scripts/pet_daemon.py status --config pet-config.yaml

# 停止
kill $(pgrep -f pet_daemon.py)
```

---

## 生成宠物形象

### 完整流程

```bash
# 1. 准备生成任务
python scripts/prepare_pet_run.py \
  --pet-name "小飞" \
  --description "一只蓝色的科技小鸟" \
  --output-dir ./pet-run

# 2. 生成基础形象
python scripts/generate_pet_images.py \
  --run-dir ./pet-run \
  --states base

# 3. 记录结果
python scripts/record_imagegen_result.py \
  --run-dir ./pet-run \
  --job-id base \
  --source ./generated/base.png

# 4. 生成所有动作行
python scripts/generate_pet_images.py \
  --run-dir ./pet-run \
  --states all

# 5. 记录所有结果（对每个 state 重复）
python scripts/record_imagegen_result.py \
  --run-dir ./pet-run \
  --job-id idle \
  --source ./generated/idle.png

# 6. 提取帧（去除色度键背景）
python scripts/extract_strip_frames.py \
  --run-dir ./pet-run \
  --states all

# 7. 合成图集
python scripts/compose_atlas.py \
  --frames-root ./pet-run/frames \
  --output ./pet-run/final/spritesheet.png \
  --webp-output ./pet-run/final/spritesheet.webp

# 8. 验证
python scripts/validate_atlas.py \
  ./pet-run/final/spritesheet.png \
  --json-out ./pet-run/final/validation.json

# 9. 生成联系表
python scripts/make_contact_sheet.py \
  ./pet-run/final/spritesheet.png \
  --output ./pet-run/qa/contact-sheet.png

# 10. 打包
python scripts/package_custom_pet.py \
  --run-dir ./pet-run
```

### 使用万相 API

```bash
python scripts/generate_pet_images.py \
  --run-dir ./pet-run \
  --provider wanxiang \
  --model wan2.7-image-pro \
  --api-key sk-xxx \
  --states base
```

---

## 在飞书中交互

### @提及

```
用户: @小飞 帮我查一下最近的部署记录
小飞: 好的，让我来帮你查看...
```

### 加急消息

```
用户: (加急) @小飞 紧急！服务器宕机了！
小飞: 🚨 收到加急！...
```

### 触发生图

```
用户: @小飞 生成一个新形象
小飞: 收到形象生成请求！🎨
      请通过命令行执行：...
```

### P2P 私聊

```
用户: (私聊小飞) 今天心情怎么样？
小飞: 今天状态不错，有什么可以帮你的吗？
```

---

## 排错

### 常见问题

**消息监听没有反应**
- 确认 `lark-cli auth whoami` 显示已登录
- 确认开放平台事件订阅已配置为「长连接模式」
- 确认 `im.message.receive_v1` 事件已添加

**LLM 无回复**
- 确认 API Key 正确设置
- 确认模型名称正确
- 检查 `pet.log` 中的错误信息

**生图失败**
- 火山引擎: 确认 `ARK_API_KEY` 设置
- 万相: 确认 `DASHSCOPE_API_KEY` 设置
- 检查 API 配额是否充足
- 图片 URL 有效期 24 小时，请及时下载
