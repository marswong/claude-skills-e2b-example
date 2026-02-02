#!/usr/bin/env python3
"""
ChatGPT Vision 脚本 - 支持图片识别的 OpenAI API 调用

功能:
- 上传图片并识别
- 支持本地图片和URL
- 支持多图片分析
- 可结合文字提问
"""

import argparse
import base64
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("错误: 请先安装 openai 库")
    print("运行: pip3 install --break-system-packages openai")
    sys.exit(1)


def load_env_file():
    """从 .env 文件加载环境变量"""
    env_paths = [
        Path.home() / ".env",
        Path.home() / ".claude" / ".env",
        Path.cwd() / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key not in os.environ:
                            os.environ[key] = value
            break


def get_api_key():
    """获取 OpenAI API Key"""
    load_env_file()

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("错误: 未找到 OPENAI_API_KEY")
        print("\n请通过以下方式之一配置:")
        print("1. 设置环境变量: export OPENAI_API_KEY='your-key'")
        print("2. 在 ~/.env 文件中添加: OPENAI_API_KEY=your-key")
        sys.exit(1)

    return api_key


def encode_image(image_path: str) -> str:
    """将图片编码为 base64"""
    with open(image_path, "rb") as image_file:
        return base64.standard_b64encode(image_file.read()).decode("utf-8")


def get_image_mime_type(image_path: str) -> str:
    """获取图片的 MIME 类型"""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_types.get(ext, "image/jpeg")


def analyze_image(
    image_sources: list,
    prompt: str = "请描述这张图片的内容",
    model: str = "gpt-4o",
    detail: str = "auto",
    max_tokens: int = 1000,
    stream: bool = True
):
    """
    分析图片

    Args:
        image_sources: 图片路径或URL列表
        prompt: 用户提问
        model: 使用的模型 (gpt-4o, gpt-4-turbo)
        detail: 图片分析精度 (low, high, auto)
        max_tokens: 最大输出 token
        stream: 是否流式输出
    """
    client = OpenAI(api_key=get_api_key())

    # 构建消息内容
    content = []

    # 添加文字提问
    content.append({
        "type": "text",
        "text": prompt
    })

    # 添加图片
    for source in image_sources:
        if source.startswith(("http://", "https://")):
            # URL 图片
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": source,
                    "detail": detail
                }
            })
        else:
            # 本地图片 - 转为 base64
            if not os.path.exists(source):
                print(f"错误: 图片文件不存在: {source}")
                sys.exit(1)

            base64_image = encode_image(source)
            mime_type = get_image_mime_type(source)

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}",
                    "detail": detail
                }
            })

    messages = [
        {
            "role": "user",
            "content": content
        }
    ]

    try:
        if stream:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                stream=True
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    print(text, end="", flush=True)
                    full_response += text
            print()
            return full_response
        else:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )
            result = response.choices[0].message.content
            print(result)
            return result

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


def interactive_vision(model: str = "gpt-4o", detail: str = "auto"):
    """交互式图片分析模式"""
    print(f"ChatGPT Vision 交互模式 (模型: {model})")
    print("命令:")
    print("  /image <路径或URL>  - 添加图片")
    print("  /clear              - 清除已添加的图片")
    print("  /list               - 列出已添加的图片")
    print("  exit 或 quit        - 退出")
    print("-" * 50)

    images = []

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

        if user_input.startswith("/image "):
            img_path = user_input[7:].strip()
            if img_path.startswith(("http://", "https://")) or os.path.exists(img_path):
                images.append(img_path)
                print(f"已添加图片: {img_path}")
            else:
                print(f"错误: 图片不存在: {img_path}")
            continue

        if user_input == "/clear":
            images = []
            print("已清除所有图片")
            continue

        if user_input == "/list":
            if images:
                print("已添加的图片:")
                for i, img in enumerate(images, 1):
                    print(f"  {i}. {img}")
            else:
                print("暂无图片")
            continue

        # 发送分析请求
        if not images:
            print("请先使用 /image 命令添加图片")
            continue

        print("\nChatGPT: ", end="", flush=True)
        analyze_image(images, user_input, model, detail)


def main():
    parser = argparse.ArgumentParser(
        description="ChatGPT Vision - 图片识别工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析单张本地图片
  python3 chat_vision.py --image photo.jpg "这张图片里有什么?"

  # 分析网络图片
  python3 chat_vision.py --image "https://example.com/image.jpg" "描述这张图片"

  # 分析多张图片
  python3 chat_vision.py --image img1.jpg --image img2.png "比较这两张图片"

  # 高精度分析
  python3 chat_vision.py --image photo.jpg --detail high "详细描述图片内容"

  # 交互模式
  python3 chat_vision.py --interactive
"""
    )

    parser.add_argument("prompt", nargs="?", default="请描述这张图片的内容", help="提问内容")
    parser.add_argument("--image", "-img", action="append", dest="images", help="图片路径或URL (可多次使用)")
    parser.add_argument("--model", "-m", default="gpt-4o", help="模型 (默认: gpt-4o)")
    parser.add_argument("--detail", "-d", choices=["low", "high", "auto"], default="auto",
                        help="分析精度: low(快速), high(详细), auto(自动)")
    parser.add_argument("--max-tokens", type=int, default=1000, help="最大输出 token")
    parser.add_argument("--no-stream", action="store_true", help="禁用流式输出")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")

    args = parser.parse_args()

    if args.interactive:
        interactive_vision(args.model, args.detail)
        return

    if not args.images:
        print("错误: 请使用 --image 参数指定图片")
        print("示例: python3 chat_vision.py --image photo.jpg \"这是什么?\"")
        print("使用 --interactive 进入交互模式")
        sys.exit(1)

    analyze_image(
        args.images,
        args.prompt,
        args.model,
        args.detail,
        args.max_tokens,
        stream=not args.no_stream
    )


if __name__ == "__main__":
    main()
