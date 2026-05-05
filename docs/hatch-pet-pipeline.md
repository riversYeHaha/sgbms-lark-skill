# Hatch-Pet 精灵表生成管线

## 概述

飞书宠物的生图系统完整还原了 hatch-pet 的生成管线，由 11 个确定性脚本组成，分 6 个阶段：

```
准备 → 生成 → 提取 → 合成 → 验证 → 打包
```

## 精灵表规格

```
┌─────────────────────────────────────────────────┐
│  8 列 × 9 行 = 72 个单元格                       │
│  单元格: 192 × 208 像素                          │
│  总尺寸: 1536 × 1872 像素                        │
│  背景: 透明（PNG RGBA）                          │
│  未使用单元格: 完全透明                           │
└─────────────────────────────────────────────────┘
```

## 动画行布局

| 行 | 状态 | 帧数 | 描述 | 每帧时长 (ms) |
|----|------|:----:|------|---------------|
| 0 | idle | 6 | 呼吸/眨眼循环 | 280, 110, 110, 140, 140, 320 |
| 1 | running-right | 8 | 向右跑动 | 120×7, 220 |
| 2 | running-left | 8 | 向左跑动 | 120×7, 220 |
| 3 | waving | 4 | 打招呼 | 140×3, 280 |
| 4 | jumping | 5 | 跳跃 | 140×4, 280 |
| 5 | failed | 8 | 失败/难过 | 140×7, 240 |
| 6 | waiting | 6 | 等待 | 150×5, 260 |
| 7 | running | 6 | 原地跑动 | 120×5, 220 |
| 8 | review | 6 | 审视/思考 | 150×5, 280 |

## 阶段详解

### 阶段 1: 准备 (prepare_pet_run.py)

**输入**: 宠物名称、描述、参考图片（可选）

**输出**:
```
pet-run/
├── pet_request.json          # 宠物请求配置
├── imagegen-jobs.json        # 生成任务清单
├── prompts/
│   ├── base.md              # 基础形象提示词
│   └── rows/
│       ├── idle.md
│       ├── running-right.md
│       └── ... (9 个)
└── references/
    └── layout-guides/       # 布局引导图 (9 个)
```

**提示词模板** (base.md):
```markdown
# Base Pet: 小飞

Generate a single centered full-body sprite of 小飞.

Style: Codex digital pet sprite style: pixel-art-adjacent low-resolution
mascot sprite, compact chibi proportions, chunky whole-body silhouette,
thick dark 1-2px outline, visible stepped/pixel edges, limited palette,
flat cel shading...

Requirements:
- Centered full-body sprite against a flat uniform chroma-key background
  (green, #00FF00)
- No shadows, gradients, or decorations on the background
- The background must be pure flat #00FF00 with no variation
```

### 阶段 2: 生成 (generate_pet_images.py)

**第一步: 生成基础形象**

调用生图 API 生成宠物基础形象，输出 `decoded/base.png`。

```
输入: prompts/base.md (纯文本)
API: 火山引擎 seedream / 万相2.7
输出: decoded/base.png (2K 分辨率)
```

**第二步: 记录结果 (record_imagegen_result.py)**

验证 SHA256，复制到 `decoded/base.png` 和 `references/canonical-base.png`。

**第三步: 生成动作行**

对每个状态 (9 个) 生成横向帧条:

```
输入: prompts/rows/{state}.md
输出: decoded/{state}.png
尺寸: {frame_count * 192} × 208 像素
```

| 状态 | 帧数 | 条尺寸 |
|------|:----:|--------|
| idle | 6 | 1152×208 |
| running-right | 8 | 1536×208 |
| running-left | 8 | 1536×208 |
| waving | 4 | 768×208 |
| jumping | 5 | 960×208 |
| failed | 8 | 1536×208 |
| waiting | 6 | 1152×208 |
| running | 6 | 1152×208 |
| review | 6 | 1152×208 |

### 阶段 3: 提取 (extract_strip_frames.py)

从横向帧条中提取单个帧，并使用色度键去除背景:

```
decoded/idle.png ──▶ frames/idle/000.png  (192×208, RGBA, 透明背景)
                     frames/idle/001.png
                     ...
                     frames/idle/005.png
```

**色度键算法**:
```python
def remove_chroma_background(image, chroma_key, threshold):
    rgba = image.convert("RGBA")
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            distance = sqrt(
                (r - chroma_key[0])**2 +
                (g - chroma_key[1])**2 +
                (b - chroma_key[2])**2
            )
            if distance <= threshold:
                pixels[x, y] = (r, g, b, 0)  # 透明
    return rgba
```

### 阶段 4: 合成 (compose_atlas.py)

将提取的帧按行布局合成最终的 8×9 图集:

```
frames/idle/000.png ──▶ cell (0,0)
frames/idle/001.png ──▶ cell (1,0)
...
frames/review/005.png ──▶ cell (5,8)
```

**输出**:
- `final/spritesheet.png` — PNG 格式 (1536×1872)
- `final/spritesheet.webp` — WebP 无损格式

### 阶段 5: 验证 (validate_atlas.py)

自动检查:
1. 尺寸: 必须为 1536×1872
2. 格式: PNG 或 WebP
3. 透明度: 已使用帧不能为空 (< 50px)
4. 透明度: 未使用帧必须完全透明
5. 边缘像素、帧重叠、色度键残留

### 阶段 6: 打包 (package_custom_pet.py)

```
packaged/小飞/
├── pet.json          # 宠物元信息
├── spritesheet.webp  # WebP 精灵表
└── contact-sheet.png # 联系表 (预览用)
```

**pet.json**:
```json
{
  "id": "小飞",
  "displayName": "小飞",
  "description": "一只蓝色的科技小鸟",
  "spritesheetPath": "spritesheet.webp"
}
```

## running-left 镜像推导

如果宠物设计是对称的（没有单侧面标记、文字、道具），可以从 running-right 镜像生成 running-left:

```bash
python scripts/derive_running_left.py \
  --run-dir ./pet-run \
  --confirm-appropriate-mirror \
  --decision-note "宠物设计对称，镜像保留了完整标识"
```

## 修复流程

如果 QA 验证失败，针对失败的行进行修复:

```bash
# 1. 分析失败原因
python scripts/queue_pet_repairs.py --run-dir ./pet-run

# 2. 重新生成失败的行
python scripts/generate_pet_images.py --run-dir ./pet-run --states failed

# 3. 只对修复的行重新提取帧
python scripts/extract_strip_frames.py --run-dir ./pet-run --states failed

# 4. 重新合成
python scripts/compose_atlas.py --frames-root ./pet-run/frames --output ./pet-run/final/spritesheet.png
```

## 风格要求

所有生成必须遵循 Codex 数字宠物风格:

- 像素艺术风格的萌宠精灵
- 紧凑 Q 版比例 (chibi proportions)
- 1-2 px 深色轮廓，阶梯/像素边缘
- 有限调色板 (3-5 色)，扁平 cel 着色
- 简洁表情，迷你肢体
- 无分离特效、速度线、阴影
- 无文字、标签、网格线
- 纯色色度键背景

## 禁止项

生成和 QA 阶段必须拒绝:
- 波浪标记、运动弧线、速度线、拖尾、残影、模糊
- 分离的星星、浮动符号、独立阴影
- 文字、标签、帧号、网格、对话框
- 色度键色出现在角色本身上
- 帧重叠、裁剪、跨帧
- 色度键深色/浅色变体作为阴影
