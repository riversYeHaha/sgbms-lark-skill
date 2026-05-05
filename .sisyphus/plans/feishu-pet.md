---
name: feishu-pet
description: 飞书智能宠物 - 通过 WebSocket 长连接实时监听飞书消息，自动响应@提及、加急消息和私聊，支持多 LLM 提供商（DeepSeek/Kimi/GLM/火山引擎），可生成独特宠物形象（火山引擎/万相生图API）。当用户需要飞书机器人自动回复、智能客服、消息监听、群聊助手或生成宠物头像时使用。触发关键词：飞书宠物、消息监听、自动回复、群聊机器人、飞书助手、宠物头像、生成形象。
---

# 飞书宠物 (Feishu Pet)

## 概述

创建一个在飞书环境中运行的智能宠物，能够：
- 通过 WebSocket 长连接实时监听消息
- 自动响应 @提及、加急消息和私聊
- 基于大模型进行智能对话
- 支持多种 LLM 提供商（DeepSeek、Kimi、GLM、火山引擎）
- 生成独特的宠物形象（支持火山引擎、万相等生图 API）

## 前置条件

1. 安装飞书 CLI：`npm install -g @larksuite/cli`
2. 初始化配置：`lark-cli config init`
3. 登录：`lark-cli auth login --recommend`
4. 在飞书开放平台配置事件订阅（长连接模式）

## 核心组件

### 1. 宠物守护进程 (Pet Daemon)

主进程，管理宠物生命周期：
- 启动/停止事件监听
- 协调各组件工作
- 信号处理（优雅退出）

```python
class FeishuPetDaemon:
    def __init__(self, config_path):
        self.config = ConfigManager.load(config_path)
        self.state = StateManager(self.config.state_file)
        self.llm = LLMClient(self.config.llm)
        self.handler = MessageHandler(self.llm, self.state)
        self.listener = EventListener(self.handler)
    
    def start(self):
        self.state.load()
        self.listener.start()
        
        try:
            while self.running:
                event = self.listener.get_event()
                if event:
                    self.handler.handle(event)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        self.running = False
        self.listener.stop()
        self.state.save()
```

### 2. 事件监听器 (Event Listener)

封装飞书 CLI 的 `event +subscribe`：

```bash
lark-cli event +subscribe \
  --event-types im.message.receive_v1 \
  --compact --quiet
```

```python
class EventListener:
    def __init__(self, handler, event_types=None):
        self.handler = handler
        self.event_types = event_types or ["im.message.receive_v1"]
        self.process = None
        self.queue = Queue()
    
    def start(self):
        cmd = [
            "lark-cli", "event", "+subscribe",
            "--event-types", ",".join(self.event_types),
            "--compact", "--quiet"
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        Thread(target=self._read_events).start()
    
    def _read_events(self):
        for line in self.process.stdout:
            event = json.loads(line)
            self.queue.put(event)
    
    def get_event(self, timeout=1):
        try:
            return self.queue.get(timeout=timeout)
        except Empty:
            return None
    
    def stop(self):
        if self.process:
            self.process.terminate()
```

### 3. 消息处理器 (Message Handler)

消息解析、路由和处理：

```python
class MessageHandler:
    def __init__(self, llm_client, state_manager):
        self.llm = llm_client
        self.state = state_manager
        self.pet_name = state_manager.get_pet_name()
    
    def handle(self, event):
        msg = self._parse_event(event)
        
        if not self._should_respond(msg):
            return
        
        context = self._build_context(msg)
        response = self.llm.chat(context)
        self._send_reply(msg, response)
        self.state.update_conversation(msg.chat_id, msg, response)
    
    def _should_respond(self, msg):
        # @提及
        if f"@{self.pet_name}" in msg.content:
            return True
        
        # 加急消息
        if msg.is_urgent:
            return True
        
        # P2P 私聊
        if msg.chat_type == "p2p":
            return True
        
        return False
    
    def _build_context(self, msg):
        history = self.state.get_conversation(msg.chat_id)
        
        messages = []
        for h in history[-10:]:
            messages.append({"role": "user", "content": h["user"]})
            messages.append({"role": "assistant", "content": h["assistant"]})
        
        messages.append({"role": "user", "content": msg.content})
        
        return messages
    
    def _send_reply(self, msg, response):
        cmd = [
            "lark-cli", "im", "+messages-reply",
            "--message-id", msg.message_id,
            "--content", response,
            "--as", "bot"
        ]
        subprocess.run(cmd)
```

### 4. LLM 客户端 (LLM Client)

统一的多提供商 LLM 接口：

```python
class LLMClient:
    PROVIDERS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "models": ["deepseek-chat", "deepseek-reasoner"]
        },
        "kimi": {
            "base_url": "https://api.moonshot.cn/v1",
            "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
        },
        "glm": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "models": ["glm-4", "glm-4-plus"]
        },
        "volcengine": {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "models": ["doubao-pro", "doubao-lite"]
        }
    }
    
    def __init__(self, config):
        self.provider = config.provider
        self.model = config.model
        self.api_key = config.api_key
        self.base_url = config.base_url or self.PROVIDERS[provider]["base_url"]
        self.temperature = config.temperature or 0.7
        self.max_tokens = config.max_tokens or 2000
    
    def chat(self, messages, system_prompt=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if system_prompt:
            data["messages"].insert(0, {
                "role": "system",
                "content": system_prompt
            })
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
        )
        
        return response.json()["choices"][0]["message"]["content"]
```

### 5. 状态管理器 (State Manager)

JSON 文件状态管理：

```python
class StateManager:
    def __init__(self, state_file):
        self.state_file = state_file
        self.state = {}
    
    def load(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = self._default_state()
    
    def save(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _default_state(self):
        return {
            "pet_name": "小 Lark",
            "status": "online",
            "conversations": {},
            "stats": {
                "total_messages": 0,
                "total_replies": 0,
                "urgent_handled": 0
            }
        }
    
    def get_conversation(self, chat_id):
        return self.state["conversations"].get(chat_id, [])
    
    def update_conversation(self, chat_id, msg, response):
        if chat_id not in self.state["conversations"]:
            self.state["conversations"][chat_id] = []
        
        self.state["conversations"][chat_id].append({
            "timestamp": datetime.now().isoformat(),
            "user": msg.content,
            "assistant": response
        })
        
        # 限制历史长度
        self.state["conversations"][chat_id] = \
            self.state["conversations"][chat_id][-50:]
        
        # 更新统计
        self.state["stats"]["total_messages"] += 1
        self.state["stats"]["total_replies"] += 1
```

### 6. 配置管理器 (Config Manager)

YAML 配置管理：

```python
class ConfigManager:
    @staticmethod
    def load(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # 环境变量替换
        config = ConfigManager._resolve_env(config)
        
        return Config(
            pet=config.get("pet", {}),
            llm=config.get("llm", {}),
            feishu=config.get("feishu", {}),
            behavior=config.get("behavior", {}),
            state_file=config.get("state_file", "./pet-state.json")
        )
    
    @staticmethod
    def _resolve_env(obj):
        if isinstance(obj, dict):
            return {k: ConfigManager._resolve_env(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ConfigManager._resolve_env(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            default = None
            if ":" in env_var:
                env_var, default = env_var.split(":", 1)
            return os.getenv(env_var, default)
        return obj
```

## 配置文件

### pet-config.yaml

```yaml
pet:
  name: "小 Lark"
  personality: "活泼、乐于助人、技术专家"
  avatar: "./assets/pet-avatar.svg"
  
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
  
behavior:
  auto_reply: true
  reply_delay: 1
  context_window: 10
  trigger_keywords:
    - "@小 Lark"
    - "加急"
  
state_file: "./pet-state.json"
```

## 使用流程

### 1. 初始化

```bash
# 创建配置文件
cp config.example.yaml pet-config.yaml
# 编辑配置文件，填入 API keys

# 初始化宠物
python scripts/pet_daemon.py --init --config pet-config.yaml
```

### 2. 启动

```bash
# 前台运行
python scripts/pet_daemon.py --config pet-config.yaml

# 后台运行
nohup python scripts/pet_daemon.py --config pet-config.yaml > pet.log 2>&1 &
```

### 3. 交互示例

```
User: @小 Lark 今天天气怎么样？
Pet: 今天北京天气晴朗，气温 15-25°C，适合外出哦！☀️

User: (加急) @小 Lark 紧急！系统出错了！
Pet: 🚨 收到加急！我已经记录了这个问题，正在为您查找解决方案...
```

## 安全考虑

1. **API Key 管理**: 使用环境变量，不硬编码
2. **消息过滤**: 过滤敏感信息
3. **速率限制**: 防止 API 滥用
4. **权限控制**: 只响应授权用户

## 宠物形象生成 (Pet Avatar Generation)

### 概述

飞书宠物支持生成独特的宠物形象，**完整还原 hatch-pet 的生成流程和效果**，包括：
- 动画精灵表 (8x9 atlas, 192x208 cells)
- 9种动画状态 (idle, running-right, running-left, waving, jumping, failed, waiting, running, review)
- 色度键背景去除
- 帧提取和图集合成
- QA 验证和修复流程
- 预览视频生成

### 生成流程

#### 1. 准备生成任务

```bash
python scripts/prepare_pet_run.py \
  --pet-name "小 Lark" \
  --description "一只活泼的蓝色小鸟，喜欢帮助人" \
  --style "cute cartoon mascot, flat design" \
  --output-dir ./pet-run \
  --force
```

**输出结构**:
```
pet-run/
├── pet_request.json          # 宠物请求配置
├── imagegen-jobs.json        # 生成任务清单
├── prompts/
│   ├── base.md              # 基础形象提示词
│   └── rows/
│       ├── idle.md
│       ├── running-right.md
│       ├── running-left.md
│       ├── waving.md
│       ├── jumping.md
│       ├── failed.md
│       ├── waiting.md
│       ├── running.md
│       └── review.md
├── references/
│   ├── canonical-base.png   # 标准基础形象
│   └── layout-guides/       # 布局引导图
│       ├── idle.png
│       ├── running-right.png
│       └── ...
└── decoded/                 # 解码后的帧
```

#### 2. 生成基础形象

使用火山引擎或万相 API 生成基础宠物形象：

```python
# generate_pet_images.py
class PetImageGenerator:
    PROVIDERS = {
        "volcengine": {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "models": ["doubao-vision-pro"]
        },
        "wanxiang": {
            "base_url": "https://dashscope.aliyuncs.com/api/v1",
            "models": ["wanx-v1"]
        }
    }
    
    def generate_base(self, prompt, provider="volcengine"):
        """生成基础宠物形象"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "size": "1536x1536",  # 高分辨率用于后续裁剪
            "n": 4  # 生成4张供选择
        }
        
        response = requests.post(
            f"{self.base_url}/images/generations",
            headers=headers,
            json=data
        )
        
        return response.json()["data"]
```

#### 3. 提示词模板

**基础形象提示词** (base.md):
```markdown
# Base Pet

A cute digital pet mascot for Feishu (Lark) workspace, [pet-description],
compact chibi proportions, chunky readable silhouette,
thick dark 1-2 px outline, visible stepped/pixel edges,
limited palette, flat cel shading,
simple expressive face, tiny limbs,
friendly expression, centered composition,
solid color background (chroma key: #00FF00),
suitable for sprite animation, 1:1 aspect ratio

## Style Rules
- Pixel-art-adjacent low-resolution mascot sprite
- Avoid polished illustration, painterly rendering, 3D render
- No soft gradients, realistic fur, or complex accessories
- Keep design simple and readable at small sizes
```

**行提示词** (idle.md):
```markdown
# Idle Row

Generate a horizontal strip of 6 frames showing [pet-name] in idle animation.

## Requirements
- 6 frames, each 192x208 pixels
- Neutral breathing/blinking loop
- Frames arranged left-to-right
- Pure chroma key (#00FF00) background between frames
- Large gaps of pure chroma key between slots

## Style
- Same pet identity as canonical base
- Same head shape, face, markings, palette
- Same body proportions, outline weight
- No detached effects, no shadows
```

#### 4. 帧提取

```python
# extract_strip_frames.py
class FrameExtractor:
    CELL_WIDTH = 192
    CELL_HEIGHT = 208
    ROW_FRAME_COUNTS = {
        "idle": 6,
        "running-right": 8,
        "running-left": 8,
        "waving": 4,
        "jumping": 5,
        "failed": 8,
        "waiting": 6,
        "running": 6,
        "review": 6,
    }
    
    def extract_frames(self, strip_image, state, chroma_key=(0, 255, 0)):
        """从行条中提取帧"""
        frames = []
        frame_count = self.ROW_FRAME_COUNTS[state]
        
        for i in range(frame_count):
            left = i * self.CELL_WIDTH
            right = left + self.CELL_WIDTH
            frame = strip_image.crop((left, 0, right, self.CELL_HEIGHT))
            
            # 去除色度键背景
            frame = self.remove_chroma_background(frame, chroma_key)
            frames.append(frame)
        
        return frames
    
    def remove_chroma_background(self, image, chroma_key, threshold=30):
        """去除色度键背景"""
        rgba = image.convert("RGBA")
        pixels = rgba.load()
        
        for y in range(rgba.height):
            for x in range(rgba.width):
                r, g, b, a = pixels[x, y]
                distance = math.sqrt(
                    (r - chroma_key[0])**2 +
                    (g - chroma_key[1])**2 +
                    (b - chroma_key[2])**2
                )
                if distance <= threshold:
                    pixels[x, y] = (r, g, b, 0)
        
        return rgba
```

#### 5. 图集合成

```python
# compose_atlas.py
class AtlasComposer:
    COLUMNS = 8
    ROWS = 9
    CELL_WIDTH = 192
    CELL_HEIGHT = 208
    ATLAS_WIDTH = COLUMNS * CELL_WIDTH  # 1536
    ATLAS_HEIGHT = ROWS * CELL_HEIGHT   # 1872
    
    ROW_SPECS = [
        ("idle", 0, 6),
        ("running-right", 1, 8),
        ("running-left", 2, 8),
        ("waving", 3, 4),
        ("jumping", 4, 5),
        ("failed", 5, 8),
        ("waiting", 6, 6),
        ("running", 7, 6),
        ("review", 8, 6),
    ]
    
    def compose(self, frames_root):
        """合成精灵表"""
        atlas = Image.new("RGBA", (self.ATLAS_WIDTH, self.ATLAS_HEIGHT), (0, 0, 0, 0))
        
        for state, row, frame_count in self.ROW_SPECS:
            frames = self.load_frames(frames_root / state, frame_count)
            
            for column, frame in enumerate(frames):
                # 居中放置
                left = column * self.CELL_WIDTH + (self.CELL_WIDTH - frame.width) // 2
                top = row * self.CELL_HEIGHT + (self.CELL_HEIGHT - frame.height) // 2
                atlas.alpha_composite(frame, (left, top))
        
        return atlas
    
    def save(self, atlas, output_path, webp_path=None):
        """保存图集"""
        atlas.save(output_path, "PNG")
        
        if webp_path:
            atlas.save(webp_path, format="WEBP", lossless=True, quality=100, method=6)
```

#### 6. QA 验证

```python
# validate_atlas.py
class AtlasValidator:
    def validate(self, atlas_path):
        """验证图集"""
        errors = []
        warnings = []
        
        with Image.open(atlas_path) as img:
            # 检查尺寸
            if img.size != (1536, 1872):
                errors.append(f"尺寸错误: {img.size}, 应为 (1536, 1872)")
            
            # 检查格式
            if img.format not in {"PNG", "WEBP"}:
                errors.append(f"格式错误: {img.format}")
            
            # 检查透明度
            if "A" not in img.mode:
                errors.append("缺少透明通道")
            
            # 检查每个单元格
            for row in range(9):
                state, frame_count = self.ROW_BY_INDEX[row]
                for column in range(8):
                    cell = img.crop((
                        column * 192, row * 208,
                        (column + 1) * 192, (row + 1) * 208
                    ))
                    
                    nontransparent = self.count_nontransparent(cell)
                    used = column < frame_count
                    
                    if used and nontransparent < 50:
                        errors.append(f"{state} row {row} col {column} 太稀疏")
                    
                    if not used and nontransparent != 0:
                        errors.append(f"{state} row {row} col {column} 应为透明")
        
        return {
            "ok": not errors,
            "errors": errors,
            "warnings": warnings
        }
```

#### 7. 预览生成

```python
# make_contact_sheet.py
class ContactSheetMaker:
    def make(self, atlas_path, output_path, scale=0.5):
        """生成联系表"""
        with Image.open(atlas_path) as atlas:
            atlas = atlas.convert("RGBA")
        
        cell_w = int(192 * scale)
        cell_h = int(208 * scale)
        label_h = 22
        
        width = 8 * cell_w
        height = 9 * (cell_h + label_h)
        
        sheet = Image.new("RGB", (width, height), "#f7f7f7")
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.load_default()
        
        for row in range(9):
            y = row * (cell_h + label_h)
            
            # 绘制标签
            draw.rectangle((0, y, width, y + label_h - 1), fill="#111111")
            draw.text((6, y + 5), f"row {row}: {self.ROW_NAMES[row]}", fill="#ffffff", font=font)
            
            for column in range(8):
                # 提取帧
                crop = atlas.crop((
                    column * 192, row * 208,
                    (column + 1) * 192, (row + 1) * 208
                ))
                crop = crop.resize((cell_w, cell_h), Image.LANCZOS)
                
                # 绘制棋盘格背景
                bg = self.checker((cell_w, cell_h))
                bg.paste(crop, (0, 0), crop)
                
                x = column * cell_w
                sheet.paste(bg, (x, y + label_h))
                
                # 绘制边框
                outline = "#18a058" if column < self.USED_COUNTS[row] else "#cc3344"
                draw.rectangle(
                    (x, y + label_h, x + cell_w - 1, y + label_h + cell_h - 1),
                    outline=outline
                )
        
        sheet.save(output_path)
```

#### 8. 动画视频生成

```python
# render_animation_videos.py
class AnimationRenderer:
    STATES = {
        "idle": (0, [280, 110, 110, 140, 140, 320]),
        "running-right": (1, [120, 120, 120, 120, 120, 120, 120, 220]),
        "running-left": (2, [120, 120, 120, 120, 120, 120, 120, 220]),
        "waving": (3, [140, 140, 140, 280]),
        "jumping": (4, [140, 140, 140, 140, 280]),
        "failed": (5, [140, 140, 140, 140, 140, 140, 140, 240]),
        "waiting": (6, [150, 150, 150, 150, 150, 260]),
        "running": (7, [120, 120, 120, 120, 120, 220]),
        "review": (8, [150, 150, 150, 150, 150, 280]),
    }
    
    def render(self, atlas_path, output_dir, loops=4, scale=2):
        """渲染动画视频"""
        with Image.open(atlas_path) as atlas:
            atlas = atlas.convert("RGBA")
        
        for state, (row, durations) in self.STATES.items():
            self.render_state(atlas, state, row, durations, output_dir, loops, scale)
    
    def render_state(self, atlas, state, row, durations, output_dir, loops, scale):
        """渲染单个状态动画"""
        # 提取帧
        frames = []
        for column in range(len(durations)):
            crop = atlas.crop((
                column * 192, row * 208,
                (column + 1) * 192, (row + 1) * 208
            )).convert("RGBA")
            frames.append(crop)
        
        # 使用 ffmpeg 生成视频
        # ... (ffmpeg 命令)
```

### 完整工作流

```bash
# 1. 准备生成任务
python scripts/prepare_pet_run.py \
  --pet-name "小 Lark" \
  --description "一只活泼的蓝色小鸟" \
  --output-dir ./pet-run

# 2. 生成基础形象
python scripts/generate_pet_images.py \
  --run-dir ./pet-run \
  --provider volcengine \
  --model doubao-vision-pro \
  --states base

# 3. 记录结果
python scripts/record_imagegen_result.py \
  --run-dir ./pet-run \
  --job-id base \
  --source ./generated/base.png

# 4. 生成行条
python scripts/generate_pet_images.py \
  --run-dir ./pet-run \
  --provider volcengine \
  --states idle,running-right,waving

# 5. 提取帧
python scripts/extract_strip_frames.py \
  --run-dir ./pet-run \
  --states all

# 6. 合成图集
python scripts/compose_atlas.py \
  --frames-root ./pet-run/frames \
  --output ./pet-run/final/spritesheet.png \
  --webp-output ./pet-run/final/spritesheet.webp

# 7. 验证
python scripts/validate_atlas.py \
  ./pet-run/final/spritesheet.png \
  --json-out ./pet-run/final/validation.json

# 8. 生成联系表
python scripts/make_contact_sheet.py \
  ./pet-run/final/spritesheet.png \
  --output ./pet-run/qa/contact-sheet.png

# 9. 生成预览视频
python scripts/render_animation_videos.py \
  ./pet-run/final/spritesheet.png \
  --output-dir ./pet-run/qa/videos

# 10. 打包
python scripts/package_custom_pet.py \
  --run-dir ./pet-run \
  --output-dir ~/.codex/pets/小-lark
```

### 修复工作流

```bash
# 如果验证失败，修复特定行
python scripts/queue_pet_repairs.py \
  --run-dir ./pet-run

# 重新生成失败的行
python scripts/generate_pet_images.py \
  --run-dir ./pet-run \
  --states failed

# 重新提取和合成
python scripts/extract_strip_frames.py --run-dir ./pet-run --states failed
python scripts/compose_atlas.py --frames-root ./pet-run/frames --output ./pet-run/final/spritesheet.png
```

### 输出文件

```
pet-run/
├── pet_request.json
├── imagegen-jobs.json
├── prompts/
│   ├── base.md
│   └── rows/
│       ├── idle.md
│       ├── running-right.md
│       └── ...
├── references/
│   ├── canonical-base.png
│   └── layout-guides/
├── decoded/
│   ├── base.png
│   ├── idle.png
│   ├── running-right.png
│   └── ...
├── frames/
│   ├── idle/
│   │   ├── 000.png
│   │   ├── 001.png
│   │   └── ...
│   ├── running-right/
│   └── ...
├── final/
│   ├── spritesheet.png
│   ├── spritesheet.webp
│   └── validation.json
└── qa/
    ├── contact-sheet.png
    ├── review.json
    ├── run-summary.json
    └── videos/
        ├── idle.mp4
        ├── running-right.mp4
        └── ...
```

### 配置文件

```yaml
pet:
  name: "小 Lark"
  description: "一只活泼的蓝色小鸟，喜欢帮助人"
  
image_generation:
  provider: "volcengine"  # 或 "wanxiang"
  model: "doubao-vision-pro"
  api_key: ${VOLCENGINE_API_KEY}
  
  # 生成参数
  temperature: 0.7
  max_tokens: 2000
  
  # 图集参数
  atlas:
    columns: 8
    rows: 9
    cell_width: 192
    cell_height: 208
    background: "transparent"
  
  # 色度键
  chroma_key: "#00FF00"
  chroma_threshold: 30
  
  # 动画帧率
  animation:
    idle: [280, 110, 110, 140, 140, 320]
    running-right: [120, 120, 120, 120, 120, 120, 120, 220]
    running-left: [120, 120, 120, 120, 120, 120, 120, 220]
    waving: [140, 140, 140, 280]
    jumping: [140, 140, 140, 140, 280]
    failed: [140, 140, 140, 140, 140, 140, 140, 240]
    waiting: [150, 150, 150, 150, 150, 260]
    running: [120, 120, 120, 120, 120, 220]
    review: [150, 150, 150, 150, 150, 280]
```

### 与 hatch-pet 的对比

| 特性 | hatch-pet | feishu-pet |
|------|-----------|------------|
| **输出格式** | 动画精灵表 (8x9) | 动画精灵表 (8x9) |
| **用途** | Codex 应用内宠物 | 飞书宠物/表情包 |
| **生成数量** | 10张 (基础+9个动作) | 10张 (基础+9个动作) |
| **后处理** | 帧提取、图集合成 | 帧提取、图集合成 |
| **API** | $imagegen | 火山引擎/万相 |
| **风格** | 像素艺术 | 像素艺术/扁平卡通 |
| **QA** | 几何验证、视觉检查 | 几何验证、视觉检查 |
| **预览** | 联系表、视频 | 联系表、视频 |
| **修复** | 行级修复 | 行级修复 |

## 项目结构

```
feishu-pet/
├── SKILL.md                          # 核心技能定义
├── LICENSE.txt
├── agents/
│   └── openai.yaml                   # OpenAI 配置
├── assets/
│   ├── README.md                     # 静态资源说明
│   ├── spritesheet.png               # 精灵表 (1536x1872)
│   ├── spritesheet.webp              # WebP 格式精灵表
│   └── pet.json                      # 宠物配置文件
├── references/
│   ├── feishu-event-reference.md    # 飞书事件参考
│   ├── feishu-im-reference.md       # 飞书 IM 参考
│   ├── llm-providers.md             # LLM 提供商配置
│   └── avatar-generation.md         # 头像生成参考
├── scripts/
│   ├── pet_daemon.py                # 宠物守护进程
│   ├── message_handler.py           # 消息处理器
│   ├── llm_client.py                # LLM 客户端
│   ├── state_manager.py             # 状态管理器
│   ├── config_manager.py            # 配置管理器
│   ├── prepare_pet_run.py           # 准备生成任务
│   ├── generate_pet_images.py       # 生成宠物图片
│   ├── record_imagegen_result.py    # 记录生成结果
│   ├── extract_strip_frames.py      # 提取帧
│   ├── compose_atlas.py             # 合成图集
│   ├── validate_atlas.py            # 验证图集
│   ├── make_contact_sheet.py        # 生成联系表
│   ├── render_animation_videos.py   # 渲染动画视频
│   ├── queue_pet_repairs.py         # 修复队列
│   ├── derive_running_left.py       # 生成 running-left
│   └── package_custom_pet.py        # 打包宠物
└── evals/
    └── evals.json                   # 测试用例
```

## 扩展功能

### P1 (近期)
- [ ] 定时任务（提醒、日报）
- [ ] 文件处理（接收、解析）
- [ ] 多群聊上下文隔离
- [ ] 宠物头像生成

### P2 (中期)
- [ ] 知识库集成
- [ ] 工作流集成（审批、任务）
- [ ] 多模态（图片、语音）
- [ ] 表情包生成

### P3 (远期)
- [ ] Web 管理界面
- [ ] 多宠物实例
- [ ] 插件系统
- [ ] 动画头像
