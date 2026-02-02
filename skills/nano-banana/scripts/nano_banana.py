#!/usr/bin/env python3
"""
Nano-Banana 图片生成模块
整合 kie.ai 的 nano-banana API 到 ChatGPT Skill

功能:
- 根据文字描述生成图片
- 图片风格转换（结合 GPT-4o Vision 分析 + Nano-Banana 生成）
- 支持多种图片尺寸和格式

使用方法:
    from nano_banana import NanoBananaClient

    client = NanoBananaClient(api_key="your-kie-api-key")

    # 文字生成图片
    image_url = client.generate("一只可爱的猫咪，油画风格")

    # 图片风格转换
    image_url = client.style_transfer("photo.jpg", "梵高星空风格")
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import Optional

# 导入 ChatGPT 模块用于图片分析
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    from chatgpt_module import ChatGPTClient
except ImportError:
    ChatGPTClient = None


class NanoBananaClient:
    """Nano-Banana 图片生成客户端"""

    API_BASE = "https://api.kie.ai/api/v1/jobs"
    MODEL = "google/nano-banana"

    # 支持的图片尺寸
    SUPPORTED_SIZES = [
        "1:1",      # 正方形
        "16:9",     # 横向宽屏
        "9:16",     # 竖向长图
        "4:3",      # 传统横向
        "3:4",      # 传统竖向
        "3:2",      # 照片横向
        "2:3",      # 照片竖向
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Nano-Banana 客户端

        Args:
            api_key: KIE.AI API Key，如果不提供则从环境变量或 .env 文件读取
        """
        self.api_key = api_key or self._load_api_key()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 初始化 ChatGPT 客户端用于图片分析
        self.chatgpt = ChatGPTClient() if ChatGPTClient else None

    def _load_api_key(self) -> str:
        """从环境变量或 .env 文件加载 API Key"""
        # 先检查环境变量
        api_key = os.environ.get('KIE_API_KEY') or os.environ.get('NANO_BANANA_API_KEY')
        if api_key:
            return api_key

        # 从 .env 文件加载
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
                            if key in ['KIE_API_KEY', 'NANO_BANANA_API_KEY']:
                                return value

        raise ValueError(
            "未找到 KIE_API_KEY\n"
            "请通过以下方式之一配置:\n"
            "1. 设置环境变量: export KIE_API_KEY='your-key'\n"
            "2. 在 ~/.env 文件中添加: KIE_API_KEY=your-key\n"
            "3. 从 https://kie.ai/api-key 获取 API Key"
        )

    def generate(
        self,
        prompt: str,
        image_size: str = "1:1",
        output_format: str = "png",
        timeout: int = 120,
        poll_interval: int = 3
    ) -> str:
        """
        根据文字描述生成图片

        Args:
            prompt: 图片描述（最多20000字符）
            image_size: 图片尺寸比例 (1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3)
            output_format: 输出格式 (png 或 jpeg)
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）

        Returns:
            生成的图片 URL
        """
        if image_size not in self.SUPPORTED_SIZES:
            raise ValueError(f"不支持的尺寸: {image_size}，支持: {self.SUPPORTED_SIZES}")

        # 创建任务
        payload = {
            "model": self.MODEL,
            "input": {
                "prompt": prompt[:20000],
                "image_size": image_size,
                "output_format": output_format
            }
        }

        response = requests.post(
            f"{self.API_BASE}/createTask",
            headers=self.headers,
            json=payload
        )

        if response.status_code == 401:
            raise ValueError("API Key 无效，请检查 KIE_API_KEY")
        elif response.status_code == 429:
            raise ValueError("API 请求频率超限，请稍后重试")
        elif response.status_code != 200:
            raise ValueError(f"创建任务失败: {response.text}")

        result = response.json()
        task_id = result.get("data", {}).get("taskId")

        if not task_id:
            raise ValueError(f"未获取到 taskId: {result}")

        # 轮询等待结果
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self._check_status(task_id)

            if status["state"] == "success":
                return self._extract_image_url(status)
            elif status["state"] == "fail":
                raise ValueError(f"图片生成失败: {status.get('error', '未知错误')}")

            time.sleep(poll_interval)

        raise TimeoutError(f"图片生成超时（{timeout}秒）")

    def _check_status(self, task_id: str, max_retries: int = 3) -> dict:
        """检查任务状态（带重试）"""
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{self.API_BASE}/recordInfo",
                    headers=self.headers,
                    params={"taskId": task_id},
                    timeout=30
                )

                if response.status_code != 200:
                    raise ValueError(f"查询状态失败: {response.text}")

                return response.json().get("data", {})
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待后重试
                    continue
                raise ValueError(f"网络错误: {e}")

    def _extract_image_url(self, status: dict) -> str:
        """从状态结果中提取图片 URL"""
        result_json = status.get("resultJson")
        if result_json:
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            # 尝试不同的字段名
            for key in ["resultUrls", "image_url", "url", "output", "result"]:
                if key in result_json:
                    url = result_json[key]
                    if isinstance(url, list) and len(url) > 0:
                        return url[0]
                    elif isinstance(url, str):
                        return url
        raise ValueError(f"无法从结果中提取图片 URL: {status}")

    def style_transfer(
        self,
        image_source: str,
        style: str,
        image_size: str = "1:1",
        output_format: str = "png",
        timeout: int = 120
    ) -> str:
        """
        图片风格转换 - 结合 GPT-4o Vision 分析和 Nano-Banana 生成

        Args:
            image_source: 原始图片路径或 URL
            style: 目标风格描述（如 "油画风格"、"动漫风格"、"梵高星空"）
            image_size: 输出图片尺寸
            output_format: 输出格式
            timeout: 超时时间

        Returns:
            生成的新风格图片 URL
        """
        if not self.chatgpt:
            raise ValueError("需要 ChatGPT 模块来分析原始图片")

        # 使用 GPT-4o Vision 分析原始图片
        analysis_prompt = """请详细描述这张图片的内容，包括：
1. 主要物体/人物
2. 场景/背景
3. 颜色和光线
4. 构图和布局
5. 情绪/氛围

请用简洁但详细的英文描述，以便用于图片生成。"""

        description = self.chatgpt.analyze_image(
            image_source=image_source,
            prompt=analysis_prompt,
            detail="high"
        )

        # 构建风格转换 prompt
        style_prompt = f"""Create an image with the following content, rendered in {style} style:

{description}

Important: Maintain the same composition, subjects, and overall scene, but transform the visual style to {style}.
Make it artistic and visually striking while preserving the essence of the original scene."""

        # 使用 Nano-Banana 生成新风格图片
        return self.generate(
            prompt=style_prompt,
            image_size=image_size,
            output_format=output_format,
            timeout=timeout
        )

    def batch_generate(
        self,
        prompts: list,
        image_size: str = "1:1",
        output_format: str = "png"
    ) -> list:
        """
        批量生成图片

        Args:
            prompts: 多个图片描述
            image_size: 图片尺寸
            output_format: 输出格式

        Returns:
            生成的图片 URL 列表
        """
        results = []
        for prompt in prompts:
            try:
                url = self.generate(prompt, image_size, output_format)
                results.append({"prompt": prompt, "url": url, "success": True})
            except Exception as e:
                results.append({"prompt": prompt, "error": str(e), "success": False})
        return results


# 命令行接口
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Nano-Banana 图片生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 文字生成图片
  python3 nano_banana.py "一只可爱的猫咪在花园里玩耍，油画风格"

  # 指定尺寸
  python3 nano_banana.py "城市夜景" --size 16:9

  # 图片风格转换
  python3 nano_banana.py --style-transfer photo.jpg "梵高星空风格"

  # 下载生成的图片
  python3 nano_banana.py "美丽的风景" --output landscape.png
"""
    )

    parser.add_argument("prompt", nargs="?", help="图片描述或原始图片路径")
    parser.add_argument("--style-transfer", "-st", metavar="IMAGE",
                        help="风格转换模式：指定原始图片路径")
    parser.add_argument("--size", "-s", default="1:1",
                        choices=NanoBananaClient.SUPPORTED_SIZES,
                        help="图片尺寸 (默认: 1:1)")
    parser.add_argument("--format", "-f", default="png",
                        choices=["png", "jpeg"],
                        help="输出格式 (默认: png)")
    parser.add_argument("--output", "-o", help="下载图片到指定路径")
    parser.add_argument("--timeout", "-t", type=int, default=120,
                        help="超时时间秒 (默认: 120)")

    args = parser.parse_args()

    if not args.prompt and not args.style_transfer:
        parser.print_help()
        return

    try:
        client = NanoBananaClient()

        if args.style_transfer:
            # 风格转换模式
            print(f"正在分析原始图片: {args.style_transfer}")
            print(f"目标风格: {args.prompt}")
            image_url = client.style_transfer(
                image_source=args.style_transfer,
                style=args.prompt,
                image_size=args.size,
                output_format=args.format,
                timeout=args.timeout
            )
        else:
            # 文字生成模式
            print(f"正在生成图片: {args.prompt[:50]}...")
            image_url = client.generate(
                prompt=args.prompt,
                image_size=args.size,
                output_format=args.format,
                timeout=args.timeout
            )

        print(f"\n生成成功！")
        print(f"图片 URL: {image_url}")

        # 下载图片
        if args.output:
            response = requests.get(image_url)
            with open(args.output, 'wb') as f:
                f.write(response.content)
            print(f"已保存到: {args.output}")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
