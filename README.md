# claude-skills-e2b-example

A simple example of running code in E2B sandbox.

## Prerequisites

- Python 3.10 or higher
- Anthropic API key
- E2B API key
- OpenAI API key (optional for chatgpt skill)

## Setup

1. Clone this repository:
```bash
git clone https://github.com/marswong/claude-skills-e2b-example.git
cd claude-skills-e2b-example
```

2. Install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

3. Set up environment variables:
Create a `.env` file in the project root:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
E2B_API_KEY=your_e2b_api_key_here
```

## Usage

Build the E2B template first:
```bash
python build_template.py
```

Run the example:
```bash
python main.py "your prompt"
```
