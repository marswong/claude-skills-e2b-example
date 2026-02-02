#!/usr/bin/env python3
"""
ChatGPT 对话脚本 - 支持多种模式的 OpenAI API 调用

功能:
- 单次对话
- 多轮对话（交互模式）
- 从文件读取 prompt
- 支持不同的 GPT 模型
- 支持流式输出
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Import shared utilities
try:
    from utils import get_openai_api_key, setup_logging
except ImportError:
    # Fallback if utils not available
    def get_openai_api_key():
        from pathlib import Path
        env_paths = [Path.home() / ".env", Path.home() / ".claude" / ".env", Path.cwd() / ".env"]
        for env_path in env_paths:
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() not in os.environ:
                                os.environ[key.strip()] = value.strip().strip('"').strip("'")
                break
        return os.environ.get('OPENAI_API_KEY')

    def setup_logging(name, level=None):
        import logging
        return logging.getLogger(name)

try:
    from openai import OpenAI
except ImportError:
    print("错误: 请先安装 openai 库")
    print("运行: pip3 install --break-system-packages openai")
    sys.exit(1)


def get_api_key():
    """获取 OpenAI API Key"""
    api_key = get_openai_api_key()
    if not api_key:
        print("错误: 未找到 OPENAI_API_KEY")
        print("\n请通过以下方式之一配置:")
        print("1. 设置环境变量: export OPENAI_API_KEY='your-key'")
        print("2. 在 ~/.env 文件中添加: OPENAI_API_KEY=your-key")
        print("3. 在 ~/.claude/.env 文件中添加: OPENAI_API_KEY=your-key")
        sys.exit(1)
    return api_key


def chat_single(prompt: str, model: str = "gpt-5.2", system: str = None,
                temperature: float = 0.7, max_tokens: int = None, stream: bool = True):
    """单次对话"""
    client = OpenAI(api_key=get_api_key())

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    if stream:
        response = client.chat.completions.create(**kwargs)
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print()  # 换行
        return full_response
    else:
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        print(content)
        return content


def chat_interactive(model: str = "gpt-5.2", system: str = None, temperature: float = 0.7):
    """多轮交互对话"""
    client = OpenAI(api_key=get_api_key())

    messages = []
    if system:
        messages.append({"role": "system", "content": system})

    print(f"ChatGPT 交互模式 (模型: {model})")
    print("输入 'exit' 或 'quit' 退出，输入 'clear' 清空对话历史")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见!")
            break

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit']:
            print("再见!")
            break

        if user_input.lower() == 'clear':
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            print("对话历史已清空")
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            print("\nChatGPT: ", end="", flush=True)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            print()

            messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            print(f"\n错误: {e}")
            messages.pop()  # 移除失败的用户消息


def chat_from_file(file_path: str, model: str = "gpt-5.2", system: str = None,
                   temperature: float = 0.7, output_file: str = None):
    """从文件读取 prompt 进行对话"""
    with open(file_path, 'r', encoding='utf-8') as f:
        prompt = f.read()

    result = chat_single(prompt, model, system, temperature)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"\n结果已保存到: {output_file}")

    return result


def list_models():
    """列出可用的模型"""
    models = [
        {"name": "gpt-5.2", "description": "最新最强模型 (2025.12)，专业知识工作"},
        {"name": "gpt-5", "description": "GPT-5 基础版 (2025.08)，通用对话"},
        {"name": "gpt-5-thinking", "description": "推理模型，复杂推理、数学"},
        {"name": "gpt-5-thinking-mini", "description": "轻量推理模型"},
        {"name": "gpt-5-thinking-nano", "description": "超轻量推理，快速低成本"},
        {"name": "gpt-4o", "description": "GPT-4 Omni，多模态"},
        {"name": "gpt-4o-mini", "description": "轻量版 GPT-4，速度快"},
        {"name": "gpt-4-turbo", "description": "GPT-4 Turbo，128K 上下文"},
        {"name": "gpt-3.5-turbo", "description": "GPT-3.5，速度最快、成本最低"},
    ]

    print("可用模型:")
    print("-" * 60)
    for m in models:
        print(f"  {m['name']:<20} {m['description']}")
    print("-" * 60)
    print("使用 --model 参数指定模型，如: --model gpt-4o-mini")


def main():
    parser = argparse.ArgumentParser(
        description="ChatGPT 对话工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单次对话
  python3 chat.py "你好，请介绍一下自己"

  # 使用指定模型
  python3 chat.py "解释量子计算" --model gpt-4o

  # 带系统提示
  python3 chat.py "写一首诗" --system "你是一位诗人"

  # 交互模式
  python3 chat.py --interactive

  # 从文件读取
  python3 chat.py --file prompt.txt --output result.txt

  # 列出可用模型
  python3 chat.py --list-models
"""
    )

    parser.add_argument("prompt", nargs="?", help="对话内容")
    parser.add_argument("-m", "--model", default="gpt-5.2", help="使用的模型 (默认: gpt-5.2)")
    parser.add_argument("-s", "--system", help="系统提示词")
    parser.add_argument("-t", "--temperature", type=float, default=0.7, help="温度参数 0-2 (默认: 0.7)")
    parser.add_argument("--max-tokens", type=int, help="最大输出 token 数")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    parser.add_argument("-f", "--file", help="从文件读取 prompt")
    parser.add_argument("-o", "--output", help="输出结果到文件")
    parser.add_argument("--no-stream", action="store_true", help="禁用流式输出")
    parser.add_argument("--list-models", action="store_true", help="列出可用模型")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    if args.interactive:
        chat_interactive(args.model, args.system, args.temperature)
        return

    if args.file:
        chat_from_file(args.file, args.model, args.system, args.temperature, args.output)
        return

    if not args.prompt:
        parser.print_help()
        return

    result = chat_single(
        args.prompt,
        args.model,
        args.system,
        args.temperature,
        args.max_tokens,
        stream=not args.no_stream
    )

    if args.json:
        print(json.dumps({"response": result}, ensure_ascii=False, indent=2))

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
