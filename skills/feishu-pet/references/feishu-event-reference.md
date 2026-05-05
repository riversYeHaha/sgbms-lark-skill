# 飞书事件订阅参考

## 概述

飞书 CLI 通过 `event +subscribe` 命令支持 WebSocket 长连接事件订阅。

## 命令

```bash
# 订阅所有已注册事件（catch-all 模式）
lark-cli event +subscribe

# 订阅特定事件类型
lark-cli event +subscribe --event-types im.message.receive_v1

# Agent 友好格式（精简输出）
lark-cli event +subscribe --event-types im.message.receive_v1 --compact --quiet

# 正则过滤器
lark-cli event +subscribe --filter "^im\."

# 路由到文件
lark-cli event +subscribe --route '^im\.message=dir:./im-events/'

# 预检查
lark-cli event +subscribe --dry-run
```

## compact 格式输出

IM 消息事件的 compact 格式：
```json
{
  "type": "im.message.receive_v1",
  "message_id": "om_xxx",
  "chat_id": "oc_xxx",
  "chat_type": "p2p",
  "message_type": "text",
  "content": "Hello",
  "sender_id": "ou_xxx",
  "create_time": "1773491924409"
}
```

## 常用事件类型

| 事件类型 | 说明 |
|---------|------|
| `im.message.receive_v1` | 收到消息 |
| `im.message.message_read_v1` | 消息已读 |
| `im.message.reaction.created_v1` | 表情回复添加 |
| `im.chat.member.user.added_v1` | 用户加入群 |
| `im.chat.disbanded_v1` | 群解散 |

## 平台配置

1. 飞书开放平台 → 事件与回调 → 订阅方式 → 选择"使用长连接接收事件"
2. 添加需要的事件（如 `im.message.receive_v1`）
3. 启用对应权限（如 `im:message:receive_as_bot`）
