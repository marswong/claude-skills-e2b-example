#!/usr/bin/env python3
"""
Sora 2 Text-to-Video 模块
整合 KIE.AI 的 Sora 2 API 到 ChatGPT Skill

功能:
- 根据文字描述生成AI视频
- 支持横向/竖向视频
- 支持10秒/15秒时长
- 可选去除水印

使用方法:
    from sora_video import SoraVideoClient

    client = SoraVideoClient(api_key="your-kie-api-key")
    video_url = client.generate("一只猫在草地上奔跑")
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import Optional, Literal


class SoraVideoClient:
    """Sora 2 Text-to-Video 客户端"""

    API_BASE = "https://api.kie.ai/api/v1/jobs"
    MODEL = "sora-2-text-to-video"

    # 支持的宽高比
    ASPECT_RATIOS = ["landscape", "portrait"]

    # 支持的时长
    DURATIONS = ["10", "15"]

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Sora Video 客户端

        Args:
            api_key: KIE.AI API Key，如果不提供则从环境变量或 .env 文件读取
        """
        self.api_key = api_key or self._load_api_key()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _load_api_key(self) -> str:
        """从环境变量或 .env 文件加载 API Key"""
        # 先检查环境变量
        api_key = os.environ.get('KIE_API_KEY') or os.environ.get('SORA_API_KEY')
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
                            if key in ['KIE_API_KEY', 'SORA_API_KEY']:
                                return value

        raise ValueError(
            "未找到 KIE_API_KEY\n"
            "请通过以下方式之一配置:\n"
            "1. 设置环境变量: export KIE_API_KEY='your-key'\n"
            "2. 在 ~/.env 文件中添加: KIE_API_KEY=your-key\n"
            "3. 从 https://kie.ai 获取 API Key"
        )

    def generate(
        self,
        prompt: str,
        aspect_ratio: Literal["landscape", "portrait"] = "landscape",
        duration: Literal["10", "15"] = "10",
        remove_watermark: bool = True,
        timeout: int = 300,
        poll_interval: int = 5,
        callback_url: Optional[str] = None
    ) -> str:
        """
        根据文字描述生成视频

        Args:
            prompt: 视频描述（最多10000字符）
            aspect_ratio: 宽高比 - "landscape"(横向) 或 "portrait"(竖向)
            duration: 视频时长 - "10"(10秒) 或 "15"(15秒)
            remove_watermark: 是否去除水印
            timeout: 超时时间（秒），默认300秒(5分钟)
            poll_interval: 轮询间隔（秒）
            callback_url: 完成后回调URL

        Returns:
            生成的视频 URL
        """
        if aspect_ratio not in self.ASPECT_RATIOS:
            raise ValueError(f"不支持的宽高比: {aspect_ratio}，支持: {self.ASPECT_RATIOS}")

        if duration not in self.DURATIONS:
            raise ValueError(f"不支持的时长: {duration}，支持: {self.DURATIONS}")

        # 创建任务
        payload = {
            "model": self.MODEL,
            "input": {
                "prompt": prompt[:10000],
                "aspect_ratio": aspect_ratio,
                "n_frames": duration,
                "remove_watermark": remove_watermark
            }
        }

        if callback_url:
            payload["callBackUrl"] = callback_url

        print(f"正在创建视频生成任务...")
        response = requests.post(
            f"{self.API_BASE}/createTask",
            headers=self.headers,
            json=payload
        )

        if response.status_code == 401:
            raise ValueError("API Key 无效，请检查 KIE_API_KEY")
        elif response.status_code == 402:
            raise ValueError("余额不足，请充值后重试")
        elif response.status_code == 429:
            raise ValueError("API 请求频率超限，请稍后重试")
        elif response.status_code != 200:
            raise ValueError(f"创建任务失败: {response.text}")

        result = response.json()
        task_id = result.get("data", {}).get("taskId")

        if not task_id:
            raise ValueError(f"未获取到 taskId: {result}")

        print(f"任务已创建: {task_id}")
        print(f"正在生成视频，预计需要1-5分钟...")

        # 轮询等待结果
        start_time = time.time()
        last_state = None
        while time.time() - start_time < timeout:
            status = self._check_status(task_id)
            state = status.get("state", "unknown")

            if state != last_state:
                print(f"状态: {state}")
                last_state = state

            if state == "success":
                cost_time = status.get("costTime", 0)
                print(f"生成完成! 耗时: {cost_time/1000:.1f}秒")
                return self._extract_video_url(status)
            elif state == "fail":
                fail_msg = status.get("failMsg", "未知错误")
                fail_code = status.get("failCode", "")
                raise ValueError(f"视频生成失败 [{fail_code}]: {fail_msg}")

            time.sleep(poll_interval)

        raise TimeoutError(f"视频生成超时（{timeout}秒）")

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
                    time.sleep(2)
                    continue
                raise ValueError(f"网络错误: {e}")

    def _extract_video_url(self, status: dict) -> str:
        """从状态结果中提取视频 URL"""
        result_json = status.get("resultJson")
        if result_json:
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            # 尝试不同的字段名
            for key in ["resultUrls", "video_url", "url", "output", "result", "videoUrl"]:
                if key in result_json:
                    url = result_json[key]
                    if isinstance(url, list) and len(url) > 0:
                        return url[0]
                    elif isinstance(url, str):
                        return url
        raise ValueError(f"无法从结果中提取视频 URL: {status}")

    def batch_generate(
        self,
        prompts: list,
        aspect_ratio: str = "landscape",
        duration: str = "10"
    ) -> list:
        """
        批量生成视频

        Args:
            prompts: 多个视频描述
            aspect_ratio: 宽高比
            duration: 时长

        Returns:
            生成的视频结果列表
        """
        results = []
        for i, prompt in enumerate(prompts, 1):
            print(f"\n[{i}/{len(prompts)}] 生成: {prompt[:50]}...")
            try:
                url = self.generate(prompt, aspect_ratio, duration)
                results.append({"prompt": prompt, "url": url, "success": True})
            except Exception as e:
                results.append({"prompt": prompt, "error": str(e), "success": False})
        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Sora 2 Text-to-Video 视频生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成横向视频 (10秒)
  python3 sora_video.py "一只猫在草地上奔跑"

  # 生成竖向视频 (适合手机/抖音)
  python3 sora_video.py "城市街道夜景" --aspect portrait

  # 生成15秒视频
  python3 sora_video.py "日落时的海滩" --duration 15

  # 保存视频
  python3 sora_video.py "星空延时摄影" --output starry_night.mp4

  # 完整选项
  python3 sora_video.py "航拍山脉云海" --aspect landscape --duration 15 --output video.mp4
"""
    )

    parser.add_argument("prompt", nargs="?", help="视频描述")
    parser.add_argument("--aspect", "-a", default="landscape",
                        choices=["landscape", "portrait"],
                        help="宽高比: landscape(横向) 或 portrait(竖向)")
    parser.add_argument("--duration", "-d", default="10",
                        choices=["10", "15"],
                        help="视频时长: 10秒 或 15秒")
    parser.add_argument("--watermark", "-w", action="store_true",
                        help="保留水印 (默认去除)")
    parser.add_argument("--output", "-o", help="下载视频到指定路径")
    parser.add_argument("--timeout", "-t", type=int, default=300,
                        help="超时时间秒 (默认: 300)")

    args = parser.parse_args()

    if not args.prompt:
        parser.print_help()
        return

    try:
        client = SoraVideoClient()

        video_url = client.generate(
            prompt=args.prompt,
            aspect_ratio=args.aspect,
            duration=args.duration,
            remove_watermark=not args.watermark,
            timeout=args.timeout
        )

        print(f"\n{'='*60}")
        print(f"视频生成成功!")
        print(f"{'='*60}")
        print(f"URL: {video_url}")

        # 下载视频
        if args.output:
            print(f"\n正在下载视频...")
            response = requests.get(video_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            with open(args.output, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"\r下载进度: {percent:.1f}%", end="")

            print(f"\n已保存到: {args.output}")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
