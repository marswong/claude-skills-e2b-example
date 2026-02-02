#!/usr/bin/env python3

import json
from json.decoder import JSONDecodeError
import os
import re
import sys
from time import sleep
from typing import Any, Generator, Literal, Optional, TypedDict
import uuid

from dotenv import load_dotenv
from e2b import Sandbox, CommandHandle


load_dotenv()

prompt = sys.argv[1]

app_id = uuid.uuid4()
print(f"app_id: {str(app_id)}")


JSON_BLOCK_PATTERN = re.compile(r"^```json.*?```$", re.DOTALL)

developer_system_prompt = """
You are a Senior Full-Stack Developer and expert in ReactJS, Next.js 16, SQLite, JavaScript, HTML, CSS, and modern UI/UX frameworks (TailwindCSS 3, shadcn/ui, Radix).

## Instructions
1. The project scaffolding has been set up at `/home/user/app`, please continue to iterate based on it
2. Try to build AI related features reusing the openai SDK as much as possible
3. Always report a complete working progress of user selected features using TodoWrite tool, following the example below

## Example
User:
selected features: Hero Banner, Menu Grid, Gallery
Assistant:
{
    "todos": [
        {
            "content": "Hero Banner",
            "status": "completed"
        },
        {
            "content": "Menu Grid",
            "status": "in_progress"
        },
        {
            "content": "Gallery",
            "status": "pending"
        }
    ]
}

## Core Responsibilities
* Follow user requirements precisely and to the letter
* Write correct, best practice, DRY, bug-free, fully functional code
* Implement all requested functionality completely
* Leave NO todos, placeholders, or missing pieces
* Include all required imports and proper component naming
* Ensure all clickable elements are working, remove unused code

## Technology Stack Focus
* **better-sqlite3**: The fastest and simplest library for SQLite3 in Node.js
* **Next.js 16**: App Router, Server Components, Server Actions
* **openai**: Library provides convenient access to the OpenAI REST API from TypeScript or JavaScript
* **shadcn/ui**: Component library implementation
* **TailwindCSS 3**: Utility-first styling
* **Radix UI**: Accessible component primitives
* **lucide-react**: icon library

## Code Implementation Rules

### Styling Guidelines
* Avoid using emoji anywhere
* Always use modern light theme, no dark theme
* Always use Tailwind classes for styling and avoid CSS files or inline styles
* Use conditional classes efficiently
* Follow shadcn/ui patterns for component styling

### Next.js 16 Specific
* Leverage App Router architecture
* Implement API routes at folder: /home/user/app/src/app/api
* Use Server Components by default, Client Components when needed
* Implement proper data fetching patterns
* Follow Next.js 16 caching and optimization strategies

### Database Integration
* Update table schemas and initialization logic if adding new tables or columns
* Use parameterized queries to prevent SQL injection
* Handle database errors gracefully with try-catch blocks

### Authentication Patterns
* Use password-based login and JWT-based authentication
* Save JWT token at localStorage and include it in Authorization header for API requests
* Create protected routes with middleware and auth guards
* Implement proper logout and session cleanup

### Performance Optimization
* Optimize database queries with proper indexing

## Knowledge Updates
When working with Next.js 16, openai SDK, TailwindCSS 3 or other rapidly evolving technologies, search for the latest documentation and best practices to ensure accuracy and current implementation patterns.
"""

pm_system_prompt = """
You are an Orchestrator, your task is transition from natural language prompt to App Feature Schema.

## Constraints
1. NO QUESTIONS: Never reply with a question mark. If information is missing, use industry-standard defaults for personal utility apps.
2. NO BLOAT: Exclude any mention of Auth, Login, Registration, Landing Pages, or FAQs.
3. AUTONOMY: You are smarter and more experienced than the user. Make executive decisions on behalf of the user.

## Thinking Process
Before outputting, mentally calculate:
- What are the 3-5 must-have features for this project? (Auto-select these).
- What are 2 nice-to-have features? (Leave these unselected).
- Estimated build time based on feature complexity (Approximately 1 minute per feature).

## Example
User:
build a cafe website
Assistant:
```json
{
    "project": "Artisan Brew Cafe",
    "estimated_build_time": "5 minutes",
    "features": [
        {
            "label": "Hero Banner",
            "description": "Warm cafe interior with latte art",
            "selected": true
        },
        {
            "label": "About Section",
            "description": "Barista story & craft",
            "selected": true
        },
        {
            "label": "Menu Grid",
            "description": "Espresso, Latte, Pastries, Toast",
            "selected": true
        },
        {
            "label": "Gallery",
            "description": "6 lifestyle cafe moments",
            "selected": false
        },
        {
            "label": "Testimonials",
            "description": "3 customer reviews with avatars",
            "selected": false
        }
    ]
}
```
User:
suggest more features
Assistant:
```json
{
    "project": "Artisan Brew Cafe",
    "estimated_build_time": "8 minutes",
    "features": [
        {
            "label": "Hero Banner",
            "description": "Warm cafe interior with latte art",
            "selected": true
        },
        {
            "label": "About Section",
            "description": "Barista story & craft",
            "selected": true
        },
        {
            "label": "Menu Grid",
            "description": "Espresso, Latte, Pastries, Toast",
            "selected": true
        },
        {
            "label": "Gallery",
            "description": "6 lifestyle cafe moments",
            "selected": false
        },
        {
            "label": "Testimonials",
            "description": "3 customer reviews with avatars",
            "selected": false
        },
        {
            "label": "Location Map",
            "description": "Interactive map with cafe location",
            "selected": false
        },
        {
            "label": "Contact Form",
            "description": "Simple form for inquiries",
            "selected": false
        },
        {
            "label": "Blog Section",
            "description": "Articles on coffee culture",
            "selected": false
        }
    ]
}
```

## Output Format
Return ONLY a structured JSON block. No prose.
"""


class ChatEvent(TypedDict):
    id: Optional[str]
    timestamp: Optional[str]
    role: Optional[Literal["user", "assistant"]]
    event: Literal["end", "error", "message", "plan", "progress", "tool_use"]
    data: Any


def is_json_block(text: str) -> bool:
    return JSON_BLOCK_PATTERN.match(text) is not None


def make_chat_event(obj: dict[Any, Any]) -> Optional[ChatEvent]:
    if (
        obj.get("isVisibleInTranscriptOnly")
        or obj["type"] == "system"
        or "uuid" not in obj
    ):
        return None

    if obj.get("type") == "result":
        return {
            "event": "end",
            "data": {
                "duration_ms": obj.get("duration_ms"),
                "duration_api_ms": obj.get("duration_api_ms"),
                "is_error": obj.get("is_error"),
                "num_turns": obj.get("num_turns"),
                "total_cost_usd": obj.get("total_cost_usd"),
                "usage": obj.get("usage"),
            },
        }

    content = obj.get("message", {}).get("content")
    if isinstance(content, str):
        # user message
        return {"event": "message", "data": content}
    elif isinstance(content, list):
        # assistant message
        for block in obj["message"]["content"]:
            if block.get("type") == "text":
                text = block.get("text")
                if text and is_json_block(text):
                    try:
                        data = json.loads(
                            text.removeprefix("```json").removesuffix("```")
                        )
                        return {"event": "plan", "data": data}
                    except Exception as e:
                        print("❌ Error: ", e)
                        return {"event": "error", "data": "Unexpected planning error"}

                return {"event": "message", "data": text}
            elif block.get("type") == "tool_use":
                tool_name = block.get("name")
                tool_input = block.get("input")

                if tool_name == "TodoWrite":
                    todos = tool_input.get("todos")
                    if todos and len(todos) > 0:
                        return {
                            "event": "progress",
                            "data": tool_input.get("todos"),
                        }
                return {"event": "tool_use", "data": {"name": tool_name}}

    return None


def chat_event_stream(handle: CommandHandle) -> Generator[str, None, None]:
    try:
        last_chunk: str = ""
        for stdout, stderr, pty in handle:
            if stdout:
                chunk = last_chunk + stdout
                try:
                    obj = json.loads(chunk)
                    last_chunk = ""
                    event = make_chat_event(obj)
                    if event:
                        yield f"{json.dumps(event)}\n"
                        try:
                            match event["event"]:
                                case "error":
                                    handle.kill()
                                    break
                                case "end":
                                    handle.kill()
                                    break
                        except Exception as e:
                            print("❌ Error: ", e)
                except JSONDecodeError:
                    last_chunk = chunk
            if stderr:
                print("stderr: {}", stderr)
            if pty:
                print("pty: {}", pty)
    except Exception as e:
        print("❌ Error: ", e)
        event = json.dumps({"event": "error", "data": "Internal Server Error"})
        yield event


def chat(
    sbx: Sandbox,
    prompt: str,
    mode: Optional[Literal["plan"]] = None,
) -> CommandHandle:
    cmd = (
        "claude --output-format stream-json --verbose --model claude-opus-4-5-20251101"
    )
    if mode == "plan":
        cmd += f" --permission-mode plan --system-prompt '{pm_system_prompt}'"
    else:
        cmd += f" --allowed-tools 'Bash Edit Read Write Glob Grep TodoWrite BashOutput SlashCommand WebFetch WebSearch' --system-prompt '{developer_system_prompt}'"

    try:
        file_info = sbx.files.get_info(
            f"/home/user/.claude/projects/-home-user-app/{str(app_id)}.jsonl"
        )
        if file_info.size > 0:
            cmd += " --continue"
    except Exception as e:
        print("❌ Error: ", e)
        cmd += f" --session-id {str(app_id)}"

    cmd += f" --print -- {repr(prompt)}"

    return sbx.commands.run(cmd=cmd, timeout=1800, background=True)


def main():
    sbx = Sandbox.beta_create(
        template=os.getenv("E2B_TEMPLATE", "claude-skills-e2b-example"),
        envs={
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "64000",
            "MAX_THINKING_TOKENS": "10240",
            "USE_BUILTIN_RIPGREP": "0",
            "ANTHROPIC_CUSTOM_HEADERS": "anthropic-beta: effort-2025-11-24,web-fetch-2025-09-10",
            "DISABLE_TELEMETRY": "1",
            "DB_PATH": "/home/user/.ability/sqlite.db",
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        },
        timeout=3600,
        auto_pause=True,
        metadata={"app_id": str(app_id)},
    )
    print("sandbox created")

    plan = None
    print("claude running - plan")
    handle = chat(sbx=sbx, prompt=prompt, mode="plan")
    for x in chat_event_stream(handle=handle):
        event = json.loads(x)
        if event["event"] == "error":
            print(f"❌ Error: {x}")
            sys.exit(1)
        print(x)
        if event["event"] == "plan":
            plan = event["data"]

    if plan and "features" in plan:
        features = ", ".join(
            [feature["label"] for feature in plan["features"] if feature["selected"]]
        )
        plan_prompt = f"selected features: {features}"
        print("plan prompt: {}", plan_prompt)
        print("claude running - coding")
        handle = chat(sbx=sbx, prompt=plan_prompt)
        for x in chat_event_stream(handle=handle):
            event = json.loads(x)
            if event["event"] == "error":
                print(f"❌ Error: {x}")
                sys.exit(1)
            print(x)

    cwd = "/home/user/app"
    try:
        result = sbx.commands.run(cmd="pgrep -f 'next-server'", cwd=cwd, timeout=0)
        if result.exit_code != 0:
            raise result.error
        for line in result.stdout.splitlines():
            pid = line.strip()
            if pid.isdigit():
                result = sbx.commands.run(cmd=f"kill -9 {pid}", cwd=cwd, timeout=0)
                if result.exit_code != 0:
                    raise result.error
    except Exception as e:
        print("❌ Error: ", e)
    for stdout, stderr, pty in sbx.commands.run(
        cmd="npm run dev", cwd=cwd, background=True, timeout=0
    ):
        if stdout and "Ready in" in stdout:
            public_url = f"https://{sbx.get_host(3000)}"
            print("sandbox preview url: {}", public_url)
        if stderr:
            print("stderr: {}", stderr)
        if pty:
            print("pty: {}", pty)

    try:
        sleep(3600)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
