#!/usr/bin/env python3

from datetime import datetime, timezone
from dotenv import load_dotenv
from e2b import Template, default_build_logger

load_dotenv()

template = (
    Template()
    .from_node_image("20")
    .apt_install(["curl", "git", "ripgrep", "python3-pip"])
    .make_dir("/home/user/.ability")
    .make_dir("/home/user/.claude")
    .copy("skills", "/home/user/.claude/skills", force_upload=True)
    .copy("plugins", "/home/user/.claude/plugins", force_upload=True)
    .run_cmd("pip install --break-system-packages openai")
    .npm_install("@anthropic-ai/claude-code degit", g=True)
    .set_workdir("/home/user/app")
    .run_cmd("degit marswong/claude-code-web-template")
    .run_cmd("npm i")
    .run_cmd("npm run build")
)


Template.build(
    template,
    alias="claude-skills-e2b-example",
    cpu_count=1,
    memory_mb=2048,
    on_build_logs=default_build_logger(),
    skip_cache=True,
)
