# API 参考

## LLM API

所有 LLM 提供商使用 OpenAI-compatible 接口。

### 通用请求格式

```bash
curl -X POST {base_url}/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "model-name",
    "messages": [
      {"role": "system", "content": "system prompt"},
      {"role": "user", "content": "user message"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

### DeepSeek

| 项目 | 值 |
|------|-----|
| Base URL | `https://api.deepseek.com/v1` |
| 模型 | `deepseek-chat`, `deepseek-reasoner` |
| 环境变量 | `DEEPSEEK_API_KEY` |
| 获取 Key | https://platform.deepseek.com |

### Kimi (Moonshot)

| 项目 | 值 |
|------|-----|
| Base URL | `https://api.moonshot.cn/v1` |
| 模型 | `moonshot-v1-8k`, `moonshot-v1-32k`, `moonshot-v1-128k` |
| 环境变量 | `MOONSHOT_API_KEY` |
| 获取 Key | https://platform.moonshot.cn |

### GLM (智谱)

| 项目 | 值 |
|------|-----|
| Base URL | `https://open.bigmodel.cn/api/paas/v4` |
| 模型 | `glm-4`, `glm-4-plus` |
| 环境变量 | `GLM_API_KEY` |
| 获取 Key | https://open.bigmodel.cn |

### 火山引擎

| 项目 | 值 |
|------|-----|
| Base URL | `https://ark.cn-beijing.volces.com/api/v3` |
| 模型 | `doubao-pro`, `doubao-lite` |
| 环境变量 | `VOLCENGINE_API_KEY` |
| 获取 Key | https://console.volcengine.com/ark |

---

## 生图 API

### 火山引擎 (seedream)

```bash
curl -X POST https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "a cute pixel-art pet mascot, compact chibi proportions, ...",
    "sequential_image_generation": "disabled",
    "response_format": "url",
    "size": "2K",
    "stream": false,
    "watermark": true
  }'
```

**响应**:
```json
{
  "data": [
    {"url": "https://ark-result.oss-cn-beijing.aliyuncs.com/xxx.png?Expires=xxx"}
  ]
}
```

**环境变量**: `ARK_API_KEY`

**支持的 size**: `1K` (1024x1024), `2K` (2048x2048), `4K` (4096x4096)

### 万相2.7 (阿里云百炼)

```bash
curl --location 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation' \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $DASHSCOPE_API_KEY" \
  --data '{
    "model": "wan2.7-image-pro",
    "input": {
      "messages": [
        {"role": "user", "content": [{"text": "a cute pixel-art pet mascot"}]}
      ]
    },
    "parameters": {
      "size": "2K",
      "n": 1,
      "watermark": false,
      "thinking_mode": true
    }
  }'
```

**响应**:
```json
{
  "output": {
    "choices": [
      {
        "finish_reason": "stop",
        "message": {
          "role": "assistant",
          "content": [
            {"image": "https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/xxx.png?Expires=xxx", "type": "image"}
          ]
        }
      }
    ]
  },
  "usage": {"image_count": 1, "size": "2048*2048"}
}
```

**环境变量**: `DASHSCOPE_API_KEY`

**模型**: `wan2.7-image-pro` (专业版，支持4K), `wan2.7-image` (速度版，最大2K)

**支持的 size**: `1K` (1024x1024), `2K` (2048x2048), `4K` (仅wan2.7-image-pro文生图)

**image URL 有效期**: 24 小时

---

## 飞书 CLI

### 事件订阅

```bash
# 订阅消息事件
lark-cli event +subscribe \
  --event-types im.message.receive_v1 \
  --compact --quiet

# 查看帮助
lark-cli event --help
```

### 发送消息

```bash
# 回复消息
lark-cli im +messages-reply \
  --message-id om_xxx \
  --content "回复内容" \
  --as bot

# 发送到群
lark-cli im +messages-send \
  --chat-id oc_xxx \
  --content "消息内容" \
  --as bot
```

### 身份管理

```bash
# 初始化配置
lark-cli config init

# 登录
lark-cli auth login --recommend

# 查看当前身份
lark-cli auth whoami
```

### compact 事件格式

```json
{
  "type": "im.message.receive_v1",
  "message_id": "om_xxx",
  "chat_id": "oc_xxx",
  "chat_type": "p2p",
  "message_type": "text",
  "content": "消息文本内容",
  "sender_id": "ou_xxx",
  "create_time": "1773491924409"
}
```
