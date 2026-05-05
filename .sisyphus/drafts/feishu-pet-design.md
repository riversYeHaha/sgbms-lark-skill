# 飞书宠物 (Feishu Pet) - 详细设计方案

## 项目结构

```
feishu-pet/
├── SKILL.md                          # 核心技能定义
├── LICENSE.txt
├── agents/
│   └── openai.yaml                   # OpenAI 配置
├── assets/
│   ├── icon.png                      # 宠物图标
│   └── pet-avatar.svg               # 宠物头像
├── references/
│   ├── feishu-event-reference.md    # 飞书事件参考
│   ├── feishu-im-reference.md       # 飞书 IM 参考
│   └── llm-providers.md             # 大模型提供商配置
├── scripts/
│   ├── pet_daemon.py                # 宠物守护进程
│   ├── message_handler.py           # 消息处理器
│   ├── llm_client.py                # LLM 客户端
│   ├── state_manager.py             # 状态管理器
│   └── config_manager.py            # 配置管理器
└── evals/
    └── evals.json                   # 测试用例
```

## 核心组件设计

### 1. Pet Daemon (pet_daemon.py)

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
        # 加载状态
        self.state.load()
        
        # 启动事件监听
        self.listener.start()
        
        # 主循环
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

### 2. Event Listener (event_listener.py)

封装飞书 CLI 的 `event +subscribe`：

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
        
        # 启动读取线程
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

### 3. Message Handler (message_handler.py)

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
        
        # 构建上下文
        context = self._build_context(msg)
        
        # 调用 LLM
        response = self.llm.chat(context)
        
        # 发送回复
        self._send_reply(msg, response)
        
        # 更新状态
        self.state.update_conversation(msg.chat_id, msg, response)
    
    def _should_respond(self, msg):
        # 检查是否是 @提及
        if f"@{self.pet_name}" in msg.content:
            return True
        
        # 检查是否是加急消息
        if msg.is_urgent:
            return True
        
        # 检查是否是 P2P 私聊
        if msg.chat_type == "p2p":
            return True
        
        return False
    
    def _build_context(self, msg):
        # 获取历史上下文
        history = self.state.get_conversation(msg.chat_id)
        
        # 构建消息列表
        messages = []
        for h in history[-10:]:  # 最近 10 条
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

### 4. LLM Client (llm_client.py)

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

### 5. State Manager (state_manager.py)

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

### 6. Config Manager (config_manager.py)

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

## 配置文件示例

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

## 扩展功能

### P1 (近期)
- [ ] 定时任务（提醒、日报）
- [ ] 文件处理（接收、解析）
- [ ] 多群聊上下文隔离

### P2 (中期)
- [ ] 知识库集成
- [ ] 工作流集成（审批、任务）
- [ ] 多模态（图片、语音）

### P3 (远期)
- [ ] Web 管理界面
- [ ] 多宠物实例
- [ ] 插件系统
