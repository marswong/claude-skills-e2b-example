---
name: nano banana
description: Generate AI images from text descriptions or apply style transfer to photos using KIE.AI. Supports multiple aspect ratios (1:1, 16:9, 9:16). Use when user wants to create images, generate artwork, or transform photo styles.
---

# Nano Banana 图片生成 Skill

基于 KIE.AI 的 AI 图片生成服务，支持文字生成图片和风格转换。

## 快速开始

### 配置 API Key

在 `~/.env` 文件中添加：

```bash
KIE_API_KEY=your-kie-api-key
```

### 验证安装

```bash
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py generate "一只可爱的猫咪"
```

## 功能列表

### 1. 文字生成图片

```bash
# 基本用法
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py generate "一只可爱的猫咪，油画风格"

# 指定尺寸
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py generate "城市夜景" --size 16:9
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py generate "人物肖像" --size 9:16

# 指定输出路径
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py generate "风景画" --output landscape.png
```

### 2. 风格转换

```bash
# 将照片转换为艺术风格
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py style photo.jpg "梵高星空风格"
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py style photo.jpg "水彩画风格"
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py style photo.jpg "赛博朋克风格"
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py style photo.jpg "宫崎骏动画风格"

# 指定输出路径
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py style photo.jpg "油画风格" --output styled.png
```

### 3. 查看任务状态

```bash
python3 ~/.claude/skills/nano-banana/scripts/nano_banana.py status <task_id>
```

## 支持尺寸

| 比例 | 说明 | 适用场景 |
|------|------|----------|
| 1:1 | 正方形 | 头像、Logo |
| 16:9 | 横向宽屏 | 桌面壁纸、横幅 |
| 9:16 | 竖向长屏 | 手机壁纸、海报 |
| 4:3 | 横向标准 | 网页配图 |
| 3:4 | 竖向标准 | 杂志封面 |

## Python 模块使用

```python
from nano_banana import NanoBananaClient

client = NanoBananaClient()

# 文字生成图片
result = client.generate(
    prompt="一只可爱的猫咪，油画风格",
    size="1:1"
)
if result['success']:
    print(f"图片已保存: {result['image_path']}")

# 风格转换
result = client.style_transfer(
    image_path="photo.jpg",
    style="梵高星空风格"
)
if result['success']:
    print(f"图片已保存: {result['image_path']}")
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--size` / `-s` | 图片尺寸比例 (1:1, 16:9, 9:16, 4:3, 3:4) |
| `--output` / `-o` | 输出文件路径 |

## 提示词技巧

### 风格描述

- "油画风格"、"水彩画风格"、"素描风格"
- "梵高风格"、"莫奈风格"、"毕加索风格"
- "动漫风格"、"宫崎骏风格"、"迪士尼风格"
- "赛博朋克风格"、"蒸汽朋克风格"
- "极简风格"、"扁平化设计"

### 场景描述

- "一只猫咪在阳光下打盹"
- "城市夜景，霓虹灯闪烁"
- "森林中的小木屋，雾气缭绕"
- "未来城市的天际线"

### 质量修饰

- "高清"、"4K"、"8K"
- "精细细节"、"超写实"
- "柔和光线"、"戏剧性光影"

## 注意事项

1. **API Key**: 需要在 `~/.env` 中配置 `KIE_API_KEY`
2. **生成时间**: 图片生成需要一定时间，请耐心等待
3. **配额限制**: API 有使用配额限制
4. **图片格式**: 输出为 PNG 格式

---

**费用**: 付费 (KIE.AI API)
**服务**: KIE.AI
**依赖**: 无额外依赖
