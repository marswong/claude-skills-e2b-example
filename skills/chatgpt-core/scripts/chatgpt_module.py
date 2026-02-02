#!/usr/bin/env python3
"""
ChatGPT Skill - 可复用模块
提供文本对话和图片识别功能，供其他应用导入使用

使用方法:
    from chatgpt_module import ChatGPTClient

    client = ChatGPTClient()

    # 文本对话
    response = client.chat("你好")

    # 带系统提示的对话
    response = client.chat("分析这个问题", system="你是一个专家")

    # 图片分析
    response = client.analyze_image("/path/to/image.jpg", "描述这张图片")

    # 多图片分析
    response = client.analyze_images(["/path/to/img1.jpg", "/path/to/img2.jpg"], "比较这两张图")
"""

import base64
import os
from pathlib import Path
from typing import List, Optional, Union

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("请先安装 openai: pip3 install openai")


class ChatGPTClient:
    """ChatGPT 客户端类，封装 OpenAI API 调用"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5.2"):
        """
        初始化 ChatGPT 客户端

        Args:
            api_key: OpenAI API Key，如果不提供则从环境变量或 .env 文件读取
            model: 默认使用的模型
        """
        self.api_key = api_key or self._load_api_key()
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def _load_api_key(self) -> str:
        """从环境变量或 .env 文件加载 API Key"""
        # 先检查环境变量
        api_key = os.environ.get('OPENAI_API_KEY')
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
                            if key == 'OPENAI_API_KEY':
                                return value

        raise ValueError(
            "未找到 OPENAI_API_KEY\n"
            "请通过以下方式之一配置:\n"
            "1. 设置环境变量: export OPENAI_API_KEY='your-key'\n"
            "2. 在 ~/.env 文件中添加: OPENAI_API_KEY=your-key"
        )

    def chat(
        self,
        message: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        conversation_history: Optional[List[dict]] = None
    ) -> str:
        """
        发送文本消息并获取回复

        Args:
            message: 用户消息
            system: 系统提示词
            model: 使用的模型，默认使用初始化时指定的模型
            temperature: 温度参数 (0-2)
            max_tokens: 最大输出 token 数
            conversation_history: 对话历史记录

        Returns:
            ChatGPT 的回复文本
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        kwargs = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            kwargs["max_completion_tokens"] = max_tokens

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def chat_stream(
        self,
        message: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        conversation_history: Optional[List[dict]] = None
    ):
        """
        流式发送文本消息

        Yields:
            逐个返回的文本片段
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @staticmethod
    def _encode_image(image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    @staticmethod
    def _get_mime_type(image_path: str) -> str:
        """获取图片 MIME 类型"""
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
        self,
        image_source: str,
        prompt: str = "请描述这张图片的内容",
        system: Optional[str] = None,
        model: Optional[str] = None,
        detail: str = "auto",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        分析单张图片

        Args:
            image_source: 图片路径或 URL
            prompt: 用户提问
            system: 系统提示词
            model: 使用的模型
            detail: 分析精度 (low, high, auto)
            max_tokens: 最大输出 token
            temperature: 温度参数

        Returns:
            分析结果文本
        """
        return self.analyze_images([image_source], prompt, system, model, detail, max_tokens, temperature)

    def analyze_images(
        self,
        image_sources: List[str],
        prompt: str = "请描述这些图片的内容",
        system: Optional[str] = None,
        model: Optional[str] = None,
        detail: str = "auto",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        分析多张图片

        Args:
            image_sources: 图片路径或 URL 列表
            prompt: 用户提问
            system: 系统提示词
            model: 使用的模型
            detail: 分析精度 (low, high, auto)
            max_tokens: 最大输出 token
            temperature: 温度参数

        Returns:
            分析结果文本
        """
        # 构建消息内容
        content = [{"type": "text", "text": prompt}]

        for source in image_sources:
            if source.startswith(("http://", "https://")):
                # URL 图片
                content.append({
                    "type": "image_url",
                    "image_url": {"url": source, "detail": detail}
                })
            else:
                # 本地图片
                if not os.path.exists(source):
                    raise FileNotFoundError(f"图片文件不存在: {source}")

                base64_image = self._encode_image(source)
                mime_type = self._get_mime_type(source)

                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}",
                        "detail": detail
                    }
                })

        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": content})

        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            max_completion_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

    def analyze_image_stream(
        self,
        image_source: str,
        prompt: str = "请描述这张图片的内容",
        system: Optional[str] = None,
        model: Optional[str] = None,
        detail: str = "auto",
        max_tokens: int = 1000
    ):
        """
        流式分析图片

        Yields:
            逐个返回的文本片段
        """
        content = [{"type": "text", "text": prompt}]

        if image_source.startswith(("http://", "https://")):
            content.append({
                "type": "image_url",
                "image_url": {"url": image_source, "detail": detail}
            })
        else:
            if not os.path.exists(image_source):
                raise FileNotFoundError(f"图片文件不存在: {image_source}")

            base64_image = self._encode_image(image_source)
            mime_type = self._get_mime_type(image_source)

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}",
                    "detail": detail
                }
            })

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})

        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            max_completion_tokens=max_tokens,
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 便捷函数，无需实例化即可使用
_default_client = None

def _get_client():
    global _default_client
    if _default_client is None:
        _default_client = ChatGPTClient()
    return _default_client

def chat(message: str, system: str = None, **kwargs) -> str:
    """快速文本对话"""
    return _get_client().chat(message, system, **kwargs)

def analyze_image(image_source: str, prompt: str = "请描述这张图片", system: str = None, **kwargs) -> str:
    """快速图片分析"""
    return _get_client().analyze_image(image_source, prompt, system, **kwargs)

def analyze_images(image_sources: List[str], prompt: str = "请描述这些图片", system: str = None, **kwargs) -> str:
    """快速多图片分析"""
    return _get_client().analyze_images(image_sources, prompt, system, **kwargs)
