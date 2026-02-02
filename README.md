# E2B Sandbox Example

A simple example of running code in E2B sandbox.

## Overview

This example demonstrates how to:
- Create an E2B sandbox environment
- Execute Python code in the E2B sandbox
- Handle execution results

## Prerequisites

- Python 3.10 or higher
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
E2B_API_KEY=your_e2b_api_key_here  # Optional
```

## Usage

Run the example:
```bash
python main.py
```

The example will:
1. Create an E2B sandbox
2. Execute a simple Python script in the sandbox
3. Show the execution results

## Project Structure

- `main.py` - Main example demonstrating E2B sandbox
- `pyproject.toml` - Project dependencies and configuration
- `.env` - Environment variables (not committed to git)

## How It Works

1. **Sandbox Creation**: Creates an isolated E2B sandbox environment
2. **Code Execution**: Runs Python code in the E2B sandbox
3. **Result Processing**: Displays execution results

## License

MIT