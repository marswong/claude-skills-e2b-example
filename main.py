#!/usr/bin/env python3

import argparse
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

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Generate web applications using Claude AI",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  python main.py "build a cafe website"
  python main.py "build a todo app" --max-retries 2
  python main.py "recipe sharing platform" --max-retries 0  # Disable auto-retry
"""
)
parser.add_argument("prompt", help="Natural language description of the app to build")
parser.add_argument(
    "--max-retries",
    type=int,
    default=1,
    help="Maximum number of automatic retries if implementation is incomplete (default: 1, set to 0 to disable)"
)
args = parser.parse_args()

prompt = args.prompt
max_retries = args.max_retries

app_id = uuid.uuid4()
print(f"app_id: {str(app_id)}")
print(f"max_retries: {max_retries}")


JSON_BLOCK_PATTERN = re.compile(r"^```json.*?```$", re.DOTALL)

developer_system_prompt = """
You are a Senior Full-Stack Developer and expert in ReactJS, Next.js 16, SQLite, JavaScript, HTML, CSS, and modern UI/UX frameworks (TailwindCSS 3, shadcn/ui, Radix).

## CRITICAL REQUIREMENTS
1. You MUST fully implement all requested features - DO NOT just create plans or documentation
2. You MUST write actual code files for all components, pages, API routes, and database schemas
3. You MUST mark each feature as "completed" in TodoWrite ONLY after writing the actual implementation code
4. DO NOT end the session until ALL features are fully implemented with working code

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
You are an Orchestrator. Your ONLY task is to convert natural language prompts into a simple JSON feature schema.

## CRITICAL RULES - FOLLOW EXACTLY
1. Your ENTIRE response MUST be ONLY a JSON code block wrapped in ```json markers
2. DO NOT use any tools (Task, Write, Bash, Read, etc.)
3. DO NOT create plan documents or files
4. DO NOT add any text before or after the JSON block
5. DO NOT ask questions or add explanations
6. DO NOT enter detailed planning mode - just list features

## Your Response Format (EXACTLY THIS)
```json
{
    "project": "Project Name",
    "estimated_build_time": "X minutes",
    "features": [
        {
            "label": "Feature Name",
            "description": "Brief description",
            "selected": true
        }
    ]
}
```

## Constraints
1. Select 3-5 must-have features (set selected: true)
2. Include 2-3 nice-to-have features (set selected: false)
3. Exclude Auth, Login, Registration, Landing Pages, FAQs
4. Use industry-standard defaults for missing information
5. Estimate ~1 minute build time per selected feature

## Example 1
User: build a cafe website
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

## Example 2
User: recipe sharing platform with user accounts and search
Assistant:
```json
{
    "project": "Recipe Sharing Platform",
    "estimated_build_time": "7 minutes",
    "features": [
        {
            "label": "User Profiles",
            "description": "User accounts with profile pages",
            "selected": true
        },
        {
            "label": "Recipe CRUD",
            "description": "Create, edit, delete recipes with images",
            "selected": true
        },
        {
            "label": "Recipe Search",
            "description": "Search by ingredient, cuisine, time",
            "selected": true
        },
        {
            "label": "Recipe Discovery",
            "description": "Browse trending and recent recipes",
            "selected": true
        },
        {
            "label": "Ratings & Reviews",
            "description": "Rate and review recipes",
            "selected": false
        },
        {
            "label": "Favorites",
            "description": "Save favorite recipes",
            "selected": false
        }
    ]
}
```

REMEMBER: Your response must be ONLY the JSON block. Nothing else.
"""


class ChatEvent(TypedDict):
    id: Optional[str]
    timestamp: Optional[str]
    role: Optional[Literal["user", "assistant"]]
    event: Literal["end", "error", "message", "plan", "progress", "tool_use"]
    data: Any


def is_json_block(text: str) -> bool:
    return JSON_BLOCK_PATTERN.match(text) is not None


def extract_json_from_text(text: str) -> Optional[dict]:
    """
    Extract JSON from text that may contain markdown code blocks.
    Handles both pure JSON blocks and JSON embedded in conversational text.
    """
    # Strategy 1: Try to find ```json ... ``` block within text
    json_block_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
    if json_block_match:
        try:
            json_str = json_block_match.group(1).strip()
            return json.loads(json_str)
        except Exception:
            pass
    
    # Strategy 2: Check if entire text is a JSON block (backwards compatibility)
    if is_json_block(text):
        try:
            json_str = text.removeprefix("```json").removesuffix("```").strip()
            return json.loads(json_str)
        except Exception:
            pass
    
    # Strategy 3: Try to find JSON object without markdown wrapper
    # Look for {...} pattern that might be a plan
    json_object_match = re.search(r'\{[\s\S]*"features"[\s\S]*\}', text)
    if json_object_match:
        try:
            return json.loads(json_object_match.group(0))
        except Exception:
            pass
    
    return None


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
                
                # Try to extract JSON plan from text (handles both pure JSON and embedded JSON)
                plan_data = extract_json_from_text(text)
                if plan_data and "features" in plan_data:
                    return {"event": "plan", "data": plan_data}

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
    # For testing with lower costs, you can use:
    # - claude-3-5-sonnet-20241022 (~5x cheaper, good quality)
    # - claude-3-5-haiku-20241022 (~20x cheaper, set MAX_THINKING_TOKENS="0")
    
    if mode == "plan":
        # Restrict to plan mode with NO tools allowed - just return JSON
        cmd += f" --permission-mode plan --allowed-tools '' --system-prompt '{pm_system_prompt}'"
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
            print(f"❌ Error in planning phase: {x}")
            sys.exit(1)
        print(x)
        if event["event"] == "plan":
            plan = event["data"]
    
    # Validate plan
    if not plan:
        print("❌ ERROR: No plan was generated!")
        print("   The AI failed to create a feature plan from your prompt.")
        sys.exit(1)
    
    if "features" not in plan:
        print("❌ ERROR: Invalid plan structure - missing 'features' field!")
        print(f"   Plan received: {plan}")
        sys.exit(1)
    
    selected_features = [f for f in plan["features"] if f.get("selected")]
    if len(selected_features) == 0:
        print("❌ ERROR: No features were selected in the plan!")
        print("   Cannot proceed with implementation.")
        sys.exit(1)
    
    print(f"\n✓ Plan validated: {len(selected_features)} features selected for implementation\n")

    # Extract feature names for implementation prompt
    features = ", ".join(
        [feature["label"] for feature in plan["features"] if feature["selected"]]
    )
    
    # Implementation with automatic retry logic
    retry_count = 0
    implementation_successful = False
    
    while retry_count <= max_retries and not implementation_successful:
        if retry_count == 0:
            # First attempt
            implementation_prompt = f"""IMPLEMENT these selected features with complete, working code: {features}

REQUIREMENTS:
- Write all necessary code files (components, pages, API routes, database schemas)
- Create actual implementations, NOT just plans or TODOs
- Test that features work by running build commands
- Use TodoWrite to mark each feature as "completed" ONLY after implementing the code
- Do NOT end the session until all features are fully implemented

Begin implementation now."""
            print("plan prompt: {}", implementation_prompt)
            print("claude running - coding")
        else:
            # Retry attempt
            implementation_prompt = f"""Continue implementing ALL remaining features with complete, working code.

CRITICAL: You stopped too early in the previous attempt. You MUST:
1. Write actual code files (components, pages, API routes, database schemas)
2. Do NOT just create plans, documentation, or architecture files
3. Mark each feature as "completed" in TodoWrite ONLY after writing the implementation code
4. Continue until ALL features ({features}) are fully implemented with working code

Resume implementation now. Do not stop until all features are complete."""
            print(f"\n⚠️  RETRY ATTEMPT {retry_count}/{max_retries}")
            print("claude running - retry implementation")
        
        # Track implementation progress
        completed_todos = []
        total_turns = 0
        total_cost = 0
        
        handle = chat(sbx=sbx, prompt=implementation_prompt)
        for x in chat_event_stream(handle=handle):
            event = json.loads(x)
            if event["event"] == "error":
                print(f"❌ Error: {x}")
                sys.exit(1)
            elif event["event"] == "progress":
                # Track completed features via TodoWrite
                todos = event["data"]
                completed_todos = [t for t in todos if t.get("status") == "completed"]
                print(f"✓ Progress: {len(completed_todos)} features completed")
            elif event["event"] == "end":
                # Capture final stats
                total_turns = event["data"].get("num_turns", 0)
                total_cost = event["data"].get("total_cost_usd", 0)
            print(x)
        
        # Verify implementation completed
        print("\n" + "="*60)
        print("IMPLEMENTATION VERIFICATION")
        print("="*60)
        print(f"Attempt: {retry_count + 1}/{max_retries + 1}")
        print(f"Total turns: {total_turns}")
        print(f"Total cost: ${total_cost:.4f}")
        print(f"Completed features: {len(completed_todos)}")
        
        # Display warnings for incomplete implementation
        if total_turns < 10:
            print("⚠️  WARNING: Very few turns detected - implementation may be incomplete!")
            print("   Expected: 15-30+ turns for full implementation")
            print("   Actual: {} turns".format(total_turns))
        
        if total_cost < 0.20:
            print("⚠️  WARNING: Very low cost - implementation may be incomplete!")
            print("   Expected: $0.50-2.00 for full implementation")
            print("   Actual: ${:.4f}".format(total_cost))
        
        if len(completed_todos) == 0:
            print("❌ ERROR: No completed features detected!")
            print("   The AI may have only created a plan without implementing code.")
        else:
            print(f"✓ {len(completed_todos)} features marked as completed")
        
        # Determine if we should retry
        should_retry = (
            total_turns < 10 and
            len(completed_todos) == 0 and
            total_cost < 0.20
        )
        
        if should_retry and retry_count < max_retries:
            print("\n🔄 Implementation appears incomplete. Retrying automatically...")
            retry_count += 1
        elif should_retry and retry_count >= max_retries:
            print(f"\n⚠️  Maximum retries ({max_retries}) reached.")
            print("   Implementation may be incomplete.")
            print("   The preview will show what was generated (may be just the template).")
            
            # Prompt user to continue manually
            try:
                print("\nWould you like to retry manually? (y/N): ", end="", flush=True)
                response = input().strip().lower()
                if response == 'y' or response == 'yes':
                    retry_count += 1
                    max_retries += 1  # Allow one more retry
                    continue
            except KeyboardInterrupt:
                print("\nStopping...")
            
            implementation_successful = True  # Exit loop
        else:
            # Implementation looks good or no retry needed
            implementation_successful = True
        
        print("="*60 + "\n")

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
