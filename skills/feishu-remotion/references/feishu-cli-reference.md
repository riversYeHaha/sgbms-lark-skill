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
# 获取会议录制
lark-cli vc +recording --meeting-id "123456789" --format json

# 获取会议笔记
lark-cli vc +notes --meeting-id "123456789" --format json

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
# 搜索妙记
lark-cli minutes +search --query "产品周会" --format json

# 下载妙记
lark-cli minutes +download --minutes-id "min_456" --output ./output

# 获取妙记详情
lark-cli minutes +detail --minutes-id "min_456" --format json
```

## API 原始调用

```bash
# GET 请求
lark-cli api GET /open-apis/calendar/v4/calendars/primary/events

# POST 请求
lark-cli api POST /open-apis/im/v1/messages \
  --body '{"receive_id":"user_123","msg_type":"text","content":"{\"text\":\"hello\"}"}'
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
