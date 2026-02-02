#!/usr/bin/env python3
"""
生成 ChatGPT 集成代码模板

支持:
- Flask
- FastAPI
- 纯 Python 模块
"""

import argparse
import sys

FLASK_TEMPLATE = '''"""
Flask ChatGPT 集成模块
"""
from flask import Flask, request, jsonify, Response
from openai import OpenAI
import os

app = Flask(__name__)

# 从环境变量获取 API Key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@app.route("/chat", methods=["POST"])
def chat():
    """
    单次对话接口

    请求体:
    {
        "message": "用户消息",
        "system": "系统提示词（可选）",
        "model": "gpt-4o（可选）"
    }

    响应:
    {
        "response": "ChatGPT 回复"
    }
    """
    data = request.json
    message = data.get("message", "")
    system = data.get("system", "")
    model = data.get("model", "gpt-4o")

    if not message:
        return jsonify({"error": "message is required"}), 400

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        return jsonify({
            "response": response.choices[0].message.content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    """
    流式对话接口 (Server-Sent Events)

    请求体同 /chat
    响应: SSE 流
    """
    data = request.json
    message = data.get("message", "")
    system = data.get("system", "")
    model = data.get("model", "gpt-4o")

    if not message:
        return jsonify({"error": "message is required"}), 400

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})

    def generate():
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\\n\\n"
        yield "data: [DONE]\\n\\n"

    return Response(generate(), mimetype="text/event-stream")


# 多轮对话存储（生产环境建议使用 Redis）
conversations = {}


@app.route("/chat/multi", methods=["POST"])
def chat_multi():
    """
    多轮对话接口

    请求体:
    {
        "conversation_id": "会话ID（可选，不传则创建新会话）",
        "message": "用户消息",
        "system": "系统提示词（仅首次有效）",
        "model": "gpt-4o（可选）"
    }

    响应:
    {
        "conversation_id": "会话ID",
        "response": "ChatGPT 回复"
    }
    """
    data = request.json
    conv_id = data.get("conversation_id")
    message = data.get("message", "")
    system = data.get("system", "")
    model = data.get("model", "gpt-4o")

    if not message:
        return jsonify({"error": "message is required"}), 400

    # 获取或创建会话
    if conv_id and conv_id in conversations:
        messages = conversations[conv_id]
    else:
        import uuid
        conv_id = str(uuid.uuid4())
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        conversations[conv_id] = messages

    # 添加用户消息
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        assistant_message = response.choices[0].message.content

        # 保存助手回复
        messages.append({"role": "assistant", "content": assistant_message})

        return jsonify({
            "conversation_id": conv_id,
            "response": assistant_message
        })
    except Exception as e:
        messages.pop()  # 移除失败的用户消息
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
'''

FASTAPI_TEMPLATE = '''"""
FastAPI ChatGPT 集成模块
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from typing import Optional
import os
import uuid

app = FastAPI(title="ChatGPT API")

# 从环境变量获取 API Key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class ChatRequest(BaseModel):
    message: str
    system: Optional[str] = None
    model: str = "gpt-4o"


class MultiChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    system: Optional[str] = None
    model: str = "gpt-4o"


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    单次对话接口
    """
    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.message})

    try:
        response = client.chat.completions.create(
            model=req.model,
            messages=messages,
            temperature=0.7,
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    流式对话接口 (Server-Sent Events)
    """
    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.message})

    async def generate():
        response = client.chat.completions.create(
            model=req.model,
            messages=messages,
            temperature=0.7,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\\n\\n"
        yield "data: [DONE]\\n\\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# 多轮对话存储（生产环境建议使用 Redis）
conversations = {}


@app.post("/chat/multi")
async def chat_multi(req: MultiChatRequest):
    """
    多轮对话接口
    """
    conv_id = req.conversation_id

    # 获取或创建会话
    if conv_id and conv_id in conversations:
        messages = conversations[conv_id]
    else:
        conv_id = str(uuid.uuid4())
        messages = []
        if req.system:
            messages.append({"role": "system", "content": req.system})
        conversations[conv_id] = messages

    # 添加用户消息
    messages.append({"role": "user", "content": req.message})

    try:
        response = client.chat.completions.create(
            model=req.model,
            messages=messages,
            temperature=0.7,
        )
        assistant_message = response.choices[0].message.content

        # 保存助手回复
        messages.append({"role": "assistant", "content": assistant_message})

        return {
            "conversation_id": conv_id,
            "response": assistant_message
        }
    except Exception as e:
        messages.pop()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

PYTHON_MODULE_TEMPLATE = '''"""
ChatGPT 对话模块 - 可直接导入使用
"""
from openai import OpenAI
from typing import Optional, List, Dict, Generator
import os


class ChatGPT:
    """ChatGPT 对话类"""

    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        """
        初始化 ChatGPT 客户端

        Args:
            api_key: OpenAI API Key，不传则从环境变量获取
            model: 默认使用的模型
        """
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model
        self.conversation: List[Dict] = []

    def chat(self, message: str, system: str = None,
             temperature: float = 0.7, stream: bool = False) -> str | Generator:
        """
        单次对话

        Args:
            message: 用户消息
            system: 系统提示词
            temperature: 温度参数
            stream: 是否流式输出

        Returns:
            ChatGPT 回复（stream=True 时返回生成器）
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        if stream:
            return self._stream_response(messages, temperature)
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content

    def _stream_response(self, messages: List[Dict],
                         temperature: float) -> Generator[str, None, None]:
        """流式响应生成器"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def start_conversation(self, system: str = None):
        """开始新的多轮对话"""
        self.conversation = []
        if system:
            self.conversation.append({"role": "system", "content": system})

    def send(self, message: str, temperature: float = 0.7) -> str:
        """
        多轮对话发送消息

        Args:
            message: 用户消息
            temperature: 温度参数

        Returns:
            ChatGPT 回复
        """
        self.conversation.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation,
            temperature=temperature,
        )

        assistant_message = response.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def clear_conversation(self):
        """清空对话历史"""
        system_msg = None
        if self.conversation and self.conversation[0]["role"] == "system":
            system_msg = self.conversation[0]
        self.conversation = [system_msg] if system_msg else []


# 便捷函数
def quick_chat(message: str, system: str = None, model: str = "gpt-4o") -> str:
    """
    快速单次对话

    Example:
        response = quick_chat("你好")
        response = quick_chat("写代码", system="你是Python专家")
    """
    gpt = ChatGPT(model=model)
    return gpt.chat(message, system=system)


# 使用示例
if __name__ == "__main__":
    # 单次对话
    gpt = ChatGPT()
    response = gpt.chat("你好，介绍一下自己")
    print(response)

    # 多轮对话
    gpt.start_conversation(system="你是一个友好的助手")
    print(gpt.send("你好"))
    print(gpt.send("你记得我刚才说了什么吗？"))

    # 流式输出
    for chunk in gpt.chat("讲个笑话", stream=True):
        print(chunk, end="", flush=True)
'''


def generate_code(framework: str, output_file: str = None):
    """生成代码"""
    templates = {
        "flask": FLASK_TEMPLATE,
        "fastapi": FASTAPI_TEMPLATE,
        "module": PYTHON_MODULE_TEMPLATE,
    }

    if framework not in templates:
        print(f"错误: 不支持的框架 '{framework}'")
        print(f"支持的框架: {', '.join(templates.keys())}")
        sys.exit(1)

    code = templates[framework]

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"代码已生成到: {output_file}")
    else:
        print(code)


def main():
    parser = argparse.ArgumentParser(
        description="生成 ChatGPT 集成代码",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成 Flask 代码
  python3 generate_code.py flask

  # 生成 FastAPI 代码并保存
  python3 generate_code.py fastapi -o chatgpt_api.py

  # 生成 Python 模块
  python3 generate_code.py module -o chatgpt.py
"""
    )

    parser.add_argument("framework", choices=["flask", "fastapi", "module"],
                        help="目标框架: flask, fastapi, module")
    parser.add_argument("-o", "--output", help="输出文件路径")

    args = parser.parse_args()
    generate_code(args.framework, args.output)


if __name__ == "__main__":
    main()
