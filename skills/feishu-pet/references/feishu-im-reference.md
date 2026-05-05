# 飞书 IM API 参考

## 发送消息

```bash
# 发送文本消息到群
lark-cli im +messages-send --chat-id oc_xxx --content "Hello!"

# 发送到指定用户
lark-cli im +messages-send --user-id ou_xxx --content "Hello!"

# 发送 Markdown 消息
lark-cli im +messages-send --chat-id oc_xxx --content "**粗体** 和 [链接](https://example.com)"

# 以 bot 身份发送
lark-cli im +messages-send --chat-id oc_xxx --content "Hello!" --as bot
```

## 回复消息

```bash
# 回复消息
lark-cli im +messages-reply --message-id om_xxx --content "收到！"

# 以 bot 身份回复
lark-cli im +messages-reply --message-id om_xxx --content "收到！" --as bot
```

## 获取消息列表

```bash
# 获取群消息列表
lark-cli im +chat-messages-list --chat-id oc_xxx

# 获取 P2P 消息
lark-cli im +chat-messages-list --user-id ou_xxx

# 搜索消息
lark-cli im +messages-search --query "关键词"
```

## 关键概念

- **message_id** (om_xxx) - 消息 ID
- **chat_id** (oc_xxx) - 群/会话 ID
- **user_id** / **open_id** (ou_xxx) - 用户 ID
- **--as bot** - 以 bot 身份执行
- **--as user** - 以用户身份执行
