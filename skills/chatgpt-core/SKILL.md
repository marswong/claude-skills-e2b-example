---
name: chatgpt-core
description: OpenAI GPT API integration for single/multi-turn conversations, image analysis, and code generation. Supports GPT-5.2, GPT-4o and other models. Use when user needs AI chat, image recognition, or code generation via OpenAI.
---

# ChatGPT Core 对话核心 Skill

ChatGPT/OpenAI API 对话核心功能，包括单次对话、多轮交互、图片识别、代码生成。

## 快速开始

### 1. 安装依赖

```bash
pip3 install openai
```

### 2. 配置 API Key

在 `~/.env` 文件中添加：

```bash
OPENAI_API_KEY=sk-your-openai-key
```

### 3. 验证安装

```bash
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py "你好"
```

## 功能列表

### 1. 单次对话 (chat.py)

```bash
# 基本对话
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py "请解释什么是机器学习"

# 指定模型
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py "写一段代码" --model gpt-5.2

# 使用系统提示词
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py "写一首诗" --system "你是一位诗人，擅长写现代诗"

# 调整创造性 (温度 0-2)
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py "生成一个故事" --temperature 1.2

# 从文件读取 prompt
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py --file prompt.txt

# 保存结果到文件
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py --file prompt.txt --output result.txt
```

### 2. 多轮交互模式

```bash
# 进入交互模式
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py --interactive

# 带系统提示的交互
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py --interactive --system "你是一个编程助手"

# 交互模式中输入 'exit' 或 'quit' 退出
```

### 3. 图片识别 (chat_vision.py)

```bash
# 分析本地图片
python3 ~/.claude/skills/chatgpt-core/scripts/chat_vision.py --image photo.jpg "这张图片里有什么"

# 分析网络图片
python3 ~/.claude/skills/chatgpt-core/scripts/chat_vision.py --image https://example.com/img.jpg "描述这张图"

# 多图分析
python3 ~/.claude/skills/chatgpt-core/scripts/chat_vision.py --image img1.jpg --image img2.jpg "比较这两张图"

# 指定模型和最大 token
python3 ~/.claude/skills/chatgpt-core/scripts/chat_vision.py --image photo.jpg "详细描述" --model gpt-4o --max-tokens 1000

# 交互式图片分析
python3 ~/.claude/skills/chatgpt-core/scripts/chat_vision.py --image photo.jpg --interactive
```

### 4. 查看可用模型

```bash
python3 ~/.claude/skills/chatgpt-core/scripts/chat.py --list-models
```

## 支持模型

### GPT-5 系列 (推荐)

| 模型 | 说明 | 推荐场景 |
|------|------|----------|
| **gpt-5.2** | 最新最强模型 (2025.12) | 专业知识工作、复杂项目、图片分析 |
| **gpt-5** | GPT-5 基础版 (2025.08) | 通用对话、编码、写作 |
| **gpt-5-thinking** | 推理模型 | 复杂推理、数学、逻辑 |
| **gpt-5-thinking-mini** | 轻量推理模型 | 中等复杂度推理 |
| **gpt-5-thinking-nano** | 超轻量推理 | 快速推理、低成本 |

### GPT-4 系列 (旧版)

| 模型 | 说明 | 推荐场景 |
|------|------|----------|
| **gpt-4o** | 多模态模型 | 通用对话、图片理解 |
| **gpt-4o-mini** | 轻量版 GPT-4 | 快速响应、低成本 |
| **gpt-4-turbo** | 128K 上下文 | 长文档处理 |
| **gpt-3.5-turbo** | 速度最快 | 简单任务、原型开发 |

## 参数说明

### chat.py

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--model` | `-m` | 使用的模型 | gpt-5.2 |
| `--system` | `-s` | 系统提示词 | 无 |
| `--temperature` | `-t` | 温度参数 (0-2) | 0.7 |
| `--max-tokens` | | 最大输出 token | 无限制 |
| `--interactive` | `-i` | 交互模式 | - |
| `--file` | `-f` | 从文件读取 | - |
| `--output` | `-o` | 输出到文件 | - |
| `--no-stream` | | 禁用流式输出 | - |
| `--json` | | JSON 格式输出 | - |

### chat_vision.py

| 参数 | 说明 |
|------|------|
| `--image` | 图片路径或 URL (可多次使用) |
| `--model` | 模型 (默认 gpt-5.2) |
| `--max-tokens` | 最大输出 token |
| `--interactive` | 交互式分析模式 |

## Python 模块使用 (chatgpt_module.py)

```python
from chatgpt_module import ChatGPTClient, chat, analyze_image

# 方式1: 使用客户端类
client = ChatGPTClient()

# 文本对话
response = client.chat("你好")
response = client.chat("分析这个问题", system="你是一个专家")

# 流式输出
for chunk in client.chat_stream("讲个故事"):
    print(chunk, end="", flush=True)

# 图片分析
response = client.analyze_image("/path/to/image.jpg", "描述这张图片")

# 多图分析
response = client.analyze_images(
    ["/path/to/img1.jpg", "/path/to/img2.jpg"],
    "比较这两张图片"
)

# 方式2: 使用快捷函数
response = chat("你好")
response = analyze_image("photo.jpg", "这是什么?")
```

### 支持的方法

| 方法 | 功能 |
|------|------|
| `chat()` | 文本对话 |
| `chat_stream()` | 流式文本对话 |
| `analyze_image()` | 单张图片分析 |
| `analyze_images()` | 多张图片分析 |
| `analyze_image_stream()` | 流式图片分析 |

## 代码生成工具 (generate_code.py)

一键生成 ChatGPT 集成的后端代码：

```bash
# 生成 Flask API
python3 ~/.claude/skills/chatgpt-core/scripts/generate_code.py flask -o chatgpt_api.py

# 生成 FastAPI
python3 ~/.claude/skills/chatgpt-core/scripts/generate_code.py fastapi -o chatgpt_api.py

# 生成 Python 模块
python3 ~/.claude/skills/chatgpt-core/scripts/generate_code.py module -o chatgpt.py
```

### 生成的 API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/chat` | POST | 单次对话 |
| `/chat/stream` | POST | 流式输出 (SSE) |
| `/chat/multi` | POST | 多轮对话 |

### 前端调用示例

```javascript
// 单次对话
const response = await fetch('/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: '你好',
    system: '你是一个友好的助手'
  })
});
const data = await response.json();
console.log(data.response);

// 流式输出
const eventSource = new EventSource('/chat/stream?message=你好');
eventSource.onmessage = (e) => {
  if (e.data === '[DONE]') {
    eventSource.close();
  } else {
    console.log(e.data);
  }
};
```

## API Key 配置位置

按以下优先级查找：

1. 环境变量 `OPENAI_API_KEY`
2. `~/.env` 文件
3. `~/.claude/.env` 文件
4. 当前目录 `.env` 文件

## 常见问题

### openai 库未安装

```bash
pip3 install openai
```

### API Key 未配置

确保在 `~/.env` 文件中添加了正确的 API Key。

### 模型不可用

某些模型（如 o1）可能需要特定的 API 权限，请检查 OpenAI 账户权限。

### 速率限制

如果遇到速率限制错误，请稍后重试或升级 OpenAI 账户。

---

**费用**: 付费 (OpenAI API)
**服务**: OpenAI GPT-4o / o1
**依赖**: openai
