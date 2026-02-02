---
name: tts
description: Convert text to speech using Microsoft Edge TTS with support for multiple languages (Chinese, English, Japanese, Korean, etc.) and voice styles. Use when user wants to generate audio from text or needs speech synthesis.
---

# TTS 语音合成 Skill

基于 Microsoft Edge TTS 的免费语音合成服务，支持多语言、多音色。

## 快速开始

### 安装依赖

```bash
pip3 install edge-tts
```

### 验证安装

```bash
python3 ~/.claude/skills/tts/scripts/tts_module.py speak "Hello, World!" --output hello.mp3
```

## 功能列表

### 1. 文字转语音

```bash
# 生成语音文件 (默认英语)
python3 ~/.claude/skills/tts/scripts/tts_module.py speak "Hello, how are you today?" --output hello.mp3

# 中文语音
python3 ~/.claude/skills/tts/scripts/tts_module.py speak "你好，世界" --voice zh-CN-XiaoxiaoNeural --output hello_cn.mp3

# 日语语音
python3 ~/.claude/skills/tts/scripts/tts_module.py speak "こんにちは" --voice ja-JP-NanamiNeural --output hello_jp.mp3
```

### 2. 直接播放 (需要系统支持)

```bash
python3 ~/.claude/skills/tts/scripts/tts_module.py speak "This will play immediately" --play
```

### 3. 查看可用语音

```bash
# 列出所有语音
python3 ~/.claude/skills/tts/scripts/tts_module.py voices

# 按语言筛选
python3 ~/.claude/skills/tts/scripts/tts_module.py voices --language zh
python3 ~/.claude/skills/tts/scripts/tts_module.py voices --language en
python3 ~/.claude/skills/tts/scripts/tts_module.py voices --language ja
```

### 4. 调整语音参数

```bash
# 调整语速 (0.5-2.0)
python3 ~/.claude/skills/tts/scripts/tts_module.py speak "慢速朗读" --voice zh-CN-XiaoxiaoNeural --rate 0.8 --output slow.mp3

# 调整音调 (-50 到 +50 Hz)
python3 ~/.claude/skills/tts/scripts/tts_module.py speak "高音调" --voice zh-CN-XiaoxiaoNeural --pitch +10Hz --output high.mp3

# 调整音量 (-50% 到 +50%)
python3 ~/.claude/skills/tts/scripts/tts_module.py speak "大声说" --voice zh-CN-XiaoxiaoNeural --volume +20% --output loud.mp3
```

## 常用语音列表

### 中文语音

| 语音 ID | 说明 |
|---------|------|
| zh-CN-XiaoxiaoNeural | 女声，活泼自然 |
| zh-CN-YunxiNeural | 男声，标准 |
| zh-CN-YunjianNeural | 男声，新闻播报风格 |
| zh-CN-XiaoyiNeural | 女声，温柔 |
| zh-TW-HsiaoChenNeural | 台湾女声 |
| zh-HK-HiuGaaiNeural | 香港女声 |

### 英语语音

| 语音 ID | 说明 |
|---------|------|
| en-US-JennyNeural | 美式女声，友好 |
| en-US-GuyNeural | 美式男声，标准 |
| en-US-AriaNeural | 美式女声，专业 |
| en-GB-SoniaNeural | 英式女声 |
| en-GB-RyanNeural | 英式男声 |
| en-AU-NatashaNeural | 澳式女声 |

### 其他语言

| 语音 ID | 说明 |
|---------|------|
| ja-JP-NanamiNeural | 日语女声 |
| ko-KR-SunHiNeural | 韩语女声 |
| fr-FR-DeniseNeural | 法语女声 |
| de-DE-KatjaNeural | 德语女声 |
| es-ES-ElviraNeural | 西语女声 |

## Python 模块使用

```python
from tts_module import TTSClient

client = TTSClient()

# 生成语音文件
await client.speak("你好，世界", voice="zh-CN-XiaoxiaoNeural", output="hello.mp3")

# 获取可用语音列表
voices = await client.list_voices(language="zh")
for v in voices:
    print(f"{v['name']}: {v['gender']}")

# 带参数的语音合成
await client.speak(
    "这是一段测试文本",
    voice="zh-CN-YunxiNeural",
    rate=1.2,
    pitch="+5Hz",
    volume="+10%",
    output="test.mp3"
)
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--voice` / `-v` | 语音 ID |
| `--output` / `-o` | 输出文件路径 |
| `--rate` / `-r` | 语速 (0.5-2.0) |
| `--pitch` / `-p` | 音调 (-50Hz 到 +50Hz) |
| `--volume` | 音量 (-50% 到 +50%) |
| `--play` | 直接播放 |
| `--language` / `-l` | 筛选语言 (voices 命令) |

## 支持的音频格式

- MP3 (默认)
- 根据输出文件扩展名自动选择

---

**费用**: 免费
**服务**: Microsoft Edge TTS
**依赖**: edge-tts
