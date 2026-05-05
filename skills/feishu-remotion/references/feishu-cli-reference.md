# 飞书 CLI 命令参考

## 认证相关

```bash
# 初始化配置
lark-cli config init

# 登录
lark-cli auth login --recommend

# 查看当前登录状态
lark-cli auth status

# 登出
lark-cli auth logout
```

## 会议相关 (VC)

```bash
# 获取会议录制（支持批量，逗号分隔）
lark-cli vc +recording --meeting-ids "123456789" --format json

# 获取会议笔记（支持批量）
lark-cli vc +notes --meeting-ids "123456789" --format json

# 搜索会议
lark-cli vc +search --query "产品周会" --format json
```

## 日程相关 (Calendar)

```bash
# 查看日程
lark-cli calendar +agenda --date "2024-01-15" --format json

# 查看某段时间的日程
lark-cli calendar +agenda --start "2024-01-15T00:00:00" --end "2024-01-15T23:59:59" --format json

# 创建日程
lark-cli calendar +create-event --summary "会议" --start "2024-01-15T10:00:00" --end "2024-01-15T11:00:00"
```

## 妙记相关 (Minutes)

```bash
# 搜索妙记（需要用户授权）
lark-cli minutes +search --query "产品周会" --format json

# 下载妙记音频/视频
lark-cli minutes +download --minute-tokens "token_abc" --output-dir ./output

# 注意：minutes 没有 +detail 子命令，详情通过 +search 获取
```

## API 原始调用

```bash
# GET 请求
lark-cli api GET /open-apis/calendar/v4/calendars/primary/events

# POST 请求
lark-cli api POST /open-apis/im/v1/messages \
  --body '{"receive_id":"user_123","msg_type":"text","content":"{\"text\":\"hello\"}"}'
```

## 身份类型

```bash
# 以用户身份执行（访问个人会议/妙记需要）
lark-cli vc +search --query "产品周会" --as user

# 以 Bot 身份执行（默认）
lark-cli vc +search --query "产品周会" --as bot
```

## 输出格式

```bash
# JSON 格式
lark-cli calendar +agenda --format json

# 表格格式
lark-cli calendar +agenda --format table

#  pretty 格式
lark-cli calendar +agenda --format pretty
```

## 已知限制

- `vc +recording` / `vc +notes` / `minutes +search` 需要 **用户授权**（`--as user`），Bot 身份无法访问
- 若遇到 `need_user_authorization` 错误，请使用 `lark-cli auth login --recommend` 以用户身份登录
