# 形象生成参考

## hatch-pet 风格流程

```
1. 准备 (prepare_pet_run)     → 创建运行目录、提示词、任务清单
2. 基础 (base)               → 生成宠物基础形象
3. 动作行 (rows)             → 生成 9 种动画状态的横向帧条
4. 记录 (record)             → 记录生成结果和 SHA256 校验
5. 帧提取 (extract)          → 从行条中提取 192x208 帧，去除色度键背景
6. 图集合成 (compose)        → 合成 8x9 图集（1536x1872）
7. 验证 (validate)           → 检查尺寸、透明度、帧完整性
8. 联系表 (contact_sheet)    → 生成可视化联系表
9. 视频 (render_videos)      → 为每个状态生成动画预览视频
10. 修复 (repair)            → 行级修复流程
11. 打包 (package)           → 输出 spritesheet + pet.json
```

## 精灵表规格

```
8 列 × 9 行
单元格: 192 × 208 像素
总尺寸: 1536 × 1872 像素
背景: 透明
未使用单元格: 完全透明
```

## 动画行

| 行 | 状态 | 帧数 | 每帧时长 (ms) |
|----|------|------|--------------|
| 0 | idle | 6 | 280, 110, 110, 140, 140, 320 |
| 1 | running-right | 8 | 120×7, 220 |
| 2 | running-left | 8 | 120×7, 220 |
| 3 | waving | 4 | 140×3, 280 |
| 4 | jumping | 5 | 140×4, 280 |
| 5 | failed | 8 | 140×7, 240 |
| 6 | waiting | 6 | 150, 150, 150, 150, 150, 260 |
| 7 | running | 6 | 120, 120, 120, 120, 120, 220 |
| 8 | review | 6 | 150, 150, 150, 150, 150, 280 |

## 色度键

使用纯色作为背景，便于透明通道提取：
- 绿: `#00FF00`
- 洋红: `#FF00FF`
- 青: `#00FFFF`

## 火山引擎 API

```bash
curl -X POST https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "生成一个可爱的像素风宠物精灵",
    "sequential_image_generation": "disabled",
    "response_format": "url",
    "size": "2K",
    "stream": false,
    "watermark": true
  }'
```

**环境变量**: `ARK_API_KEY`
**获取 API Key**: https://console.volcengine.com/ark

## 万相 API (阿里云百炼)

```bash
curl --location 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation' \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $DASHSCOPE_API_KEY" \
  --data '{
    "model": "wan2.7-image-pro",
    "input": {
      "messages": [
        {"role": "user", "content": [{"text": "生成一个可爱的像素风宠物精灵"}]}
      ]
    },
    "parameters": {"size": "2K", "n": 1, "watermark": false, "thinking_mode": true}
  }'
```

**环境变量**: `DASHSCOPE_API_KEY`
**模型**: `wan2.7-image-pro` / `wan2.7-image`
**获取 API Key**: https://help.aliyun.com/zh/model-studio/get-api-key

## 风格要求

- 像素艺术风格的萌宠精灵
- 紧凑 Q 版比例
- 1-2 px 深色轮廓
- 有限调色板（3-5 色）
- 扁平 cel 着色
- 无分离特效、速度线、阴影
- 无文字、标签、网格线
