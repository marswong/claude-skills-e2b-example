# Claude Skills E2B Example

A simple example of running Claude Code with agent skills in E2B sandbox.

## Overview

This example demonstrates how to:
- Create an E2B sandbox environment
- Use Claude API to generate code
- Execute the generated code in the E2B sandbox
- Continue the conversation with execution results

## Prerequisites

- Python 3.8 or higher
- Anthropic API key
- E2B API key (optional, E2B can work without explicit key for basic usage)

## Setup

1. Clone this repository:
```bash
git clone https://github.com/marswong/claude-skills-e2b-example.git
cd claude-skills-e2b-example
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up environment variables:
Create a `.env` file in the project root:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
E2B_API_KEY=your_e2b_api_key_here  # Optional
```

## Usage

Run the example:
```bash
python main.py
```

The example will:
1. Create an E2B sandbox
2. Ask Claude to write a simple Python script
3. Execute the script in the E2B sandbox
4. Show the execution results
5. Ask Claude to interpret the results

## Project Structure

- `main.py` - Main example demonstrating Claude with E2B sandbox
- `pyproject.toml` - Project dependencies and configuration
- `.env` - Environment variables (not committed to git)

## How It Works

1. **Sandbox Creation**: Creates an isolated E2B sandbox environment
2. **Claude Interaction**: Sends a prompt to Claude asking for code
3. **Code Extraction**: Extracts Python code from Claude's response
4. **Code Execution**: Runs the code in the E2B sandbox
5. **Result Processing**: Sends execution results back to Claude for interpretation

## License

MIT