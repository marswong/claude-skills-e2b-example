---
name: sora-video
description: Generate AI videos from text descriptions or animate static images using Sora 2 via KIE.AI. Supports 10-20 second videos in landscape or portrait. Use when user wants to create videos or animate images.
---

# Sora Video 视频生成 Skill

基于 Sora 2 (KIE.AI) 的 AI 视频生成服务，支持文字生成视频和图片转视频。

## 快速开始

### 配置 API Key

在 `~/.env` 文件中添加：

```bash
KIE_API_KEY=your-kie-api-key
```

### 验证安装

```bash
python3 ~/.claude/skills/sora-video/scripts/sora_video.py generate "一只猫在草地上奔跑"
```

## 功能列表

### 1. 文字生成视频 (Text to Video)

```bash
# 基本用法
python3 ~/.claude/skills/sora-video/scripts/sora_video.py generate "一只猫在草地上奔跑"

# 指定时长 (10秒或15秒)
python3 ~/.claude/skills/sora-video/scripts/sora_video.py generate "海浪拍打沙滩" --duration 15

# 指定画面方向
python3 ~/.claude/skills/sora-video/scripts/sora_video.py generate "城市街道" --aspect landscape    # 横版
python3 ~/.claude/skills/sora-video/scripts/sora_video.py generate "瀑布流水" --aspect portrait     # 竖版

# 指定输出路径
python3 ~/.claude/skills/sora-video/scripts/sora_video.py generate "日落海滩" --output sunset.mp4
```

### 2. 图片转视频 (Image to Video)

```bash
# 基本转换
python3 ~/.claude/skills/sora-video/scripts/sora_img2video.py generate --image photo.jpg

# 添加动作描述
python3 ~/.claude/skills/sora-video/scripts/sora_img2video.py generate --image portrait.jpg "让人物微笑并眨眼"
python3 ~/.claude/skills/sora-video/scripts/sora_img2video.py generate --image landscape.jpg "云朵缓缓飘动，水面泛起涟漪"

# 指定时长和方向
python3 ~/.claude/skills/sora-video/scripts/sora_img2video.py generate --image scene.jpg --duration 15 --aspect landscape

# 指定输出路径
python3 ~/.claude/skills/sora-video/scripts/sora_img2video.py generate --image input.jpg --output output.mp4
```

### 3. 查看任务状态

```bash
# 查看任务状态
python3 ~/.claude/skills/sora-video/scripts/sora_video.py status <task_id>
python3 ~/.claude/skills/sora-video/scripts/sora_img2video.py status <task_id>
```

## 参数说明

### sora_video.py (文字生成视频)

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `--duration` / `-d` | 视频时长 | 10, 15 |
| `--aspect` / `-a` | 画面方向 | landscape, portrait |
| `--output` / `-o` | 输出文件路径 | - |

### sora_img2video.py (图片转视频)

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `--image` / `-i` | 输入图片路径 | - |
| `--duration` / `-d` | 视频时长 | 10, 15 |
| `--aspect` / `-a` | 画面方向 | landscape, portrait |
| `--output` / `-o` | 输出文件路径 | - |

## Python 模块使用

### 文字生成视频

```python
from sora_video import SoraVideoClient

client = SoraVideoClient()

# 生成视频
result = client.generate(
    prompt="一只猫在草地上奔跑，阳光明媚",
    duration=10,
    aspect="landscape"
)

if result['success']:
    print(f"视频已保存: {result['video_path']}")
```

### 图片转视频

```python
from sora_img2video import SoraImg2VideoClient

client = SoraImg2VideoClient()

# 转换视频
result = client.generate(
    image_path="photo.jpg",
    prompt="让人物微笑并眨眼",
    duration=10,
    aspect="portrait"
)

if result['success']:
    print(f"视频已保存: {result['video_path']}")
```

## 提示词技巧

### 文字生成视频

1. **描述场景**: "城市夜景，霓虹灯闪烁，车流穿梭"
2. **添加动作**: "一只猫在草地上奔跑，追逐蝴蝶"
3. **指定风格**: "水彩画风格的风景，山水画意境"
4. **描述光线**: "金色的夕阳，温暖的光线洒在海面上"

### 图片转视频

1. **人物**: "让人物微笑并眨眼"、"人物转头看向镜头"
2. **风景**: "云朵缓缓飘动"、"水面泛起涟漪"
3. **动物**: "让狗狗摇尾巴"、"小鸟扇动翅膀"
4. **镜头**: "缓慢推进镜头"、"镜头环绕拍摄"

## 注意事项

1. **API Key**: 需要在 `~/.env` 中配置 `KIE_API_KEY`
2. **生成时间**: 视频生成需要一定时间，请耐心等待
3. **配额限制**: API 有使用配额限制，请注意控制调用频率
4. **图片格式**: 支持 JPG、PNG 等常见图片格式
5. **视频格式**: 输出为 MP4 格式

---

**费用**: 付费 (KIE.AI API)
**服务**: Sora 2 (via KIE.AI)
**依赖**: 无额外依赖
