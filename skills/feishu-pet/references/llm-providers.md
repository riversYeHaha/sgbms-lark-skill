# LLM 提供商配置

## DeepSeek

```yaml
llm:
  provider: deepseek
  model: deepseek-chat
  api_key: ${DEEPSEEK_API_KEY}
  base_url: https://api.deepseek.com/v1
```

**模型**:
- `deepseek-chat` - 通用聊天
- `deepseek-reasoner` - 推理增强

**获取 API Key**: https://platform.deepseek.com

## Kimi (Moonshot)

```yaml
llm:
  provider: kimi
  model: moonshot-v1-32k
  api_key: ${MOONSHOT_API_KEY}
  base_url: https://api.moonshot.cn/v1
```

**模型**:
- `moonshot-v1-8k` - 8K 上下文
- `moonshot-v1-32k` - 32K 上下文
- `moonshot-v1-128k` - 128K 上下文

**获取 API Key**: https://platform.moonshot.cn

## GLM (智谱)

```yaml
llm:
  provider: glm
  model: glm-4
  api_key: ${GLM_API_KEY}
  base_url: https://open.bigmodel.cn/api/paas/v4
```

**模型**:
- `glm-4` - 通用
- `glm-4-plus` - 增强版

**获取 API Key**: https://open.bigmodel.cn

## 火山引擎

```yaml
llm:
  provider: volcengine
  model: doubao-pro
  api_key: ${VOLCENGINE_API_KEY}
  base_url: https://ark.cn-beijing.volces.com/api/v3
```

**模型**:
- `doubao-pro` - 专业版
- `doubao-lite` - 轻量版

**获取 API Key**: https://console.volcengine.com/ark
