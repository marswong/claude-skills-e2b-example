#!/usr/bin/env python3
"""
Simple example of running Claude Code with agent skills in E2B sandbox.

This example demonstrates:
1. Creating an E2B sandbox environment
2. Using Claude API with agent skills
3. Executing code in the E2B sandbox based on Claude's responses
"""

import os
from typing import Optional
from anthropic import Anthropic
from e2b import Sandbox
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def execute_code_in_sandbox(sandbox: Sandbox, code: str, language: str = "python") -> str:
    """
    Execute code in the E2B sandbox.
    
    Args:
        sandbox: E2B sandbox instance
        code: Code to execute
        language: Programming language (default: python)
    
    Returns:
        Output from the code execution
    """
    try:
        if language == "python":
            result = sandbox.run_code(code)
            return result.stdout if result.stdout else result.stderr
        elif language == "bash":
            result = sandbox.process.start_and_wait(code)
            return result.stdout if result.stdout else result.stderr
        else:
            return f"Unsupported language: {language}"
    except Exception as e:
        return f"Error executing code: {str(e)}"


def run_claude_with_e2b_skills():
    """
    Main function demonstrating Claude with E2B sandbox skills.
    """
    # Initialize API clients
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    client = Anthropic(api_key=api_key)
    
    # Create E2B sandbox
    print("Creating E2B sandbox...")
    sandbox = Sandbox(template="base")
    print(f"Sandbox created: {sandbox.id}")
    
    try:
        # Example conversation with Claude
        conversation_history = []
        
        # Initial message asking Claude to write and execute code
        user_message = """
        Please write a simple Python script that:
        1. Creates a list of numbers from 1 to 10
        2. Calculates the sum of these numbers
        3. Prints the result
        
        Then execute it and show me the output.
        """
        
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        print("\n" + "=" * 60)
        print("User:", user_message.strip())
        print("=" * 60)
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=conversation_history
        )
        
        # Get Claude's response
        assistant_message = response.content[0].text
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        print("\nClaude's Response:")
        print(assistant_message)
        print("=" * 60)
        
        # Extract and execute code (simplified - in production, use proper parsing)
        # Looking for Python code blocks in Claude's response
        if "```python" in assistant_message:
            code_start = assistant_message.find("```python") + 9
            code_end = assistant_message.find("```", code_start)
            if code_end != -1:
                code = assistant_message[code_start:code_end].strip()
                
                print("\nExecuting code in E2B sandbox:")
                print("-" * 60)
                print(code)
                print("-" * 60)
                
                # Execute in E2B sandbox
                output = execute_code_in_sandbox(sandbox, code)
                
                print("\nExecution Output:")
                print(output)
                print("=" * 60)
                
                # Continue conversation with execution result
                follow_up = f"The code executed successfully. Here's the output:\n{output}\n\nWhat does this result mean?"
                conversation_history.append({
                    "role": "user",
                    "content": follow_up
                })
                
                # Get Claude's interpretation
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=conversation_history
                )
                
                interpretation = response.content[0].text
                print("\nClaude's Interpretation:")
                print(interpretation)
                print("=" * 60)
        
        print("\n✅ Example completed successfully!")
        
    finally:
        # Clean up sandbox
        print(f"\nClosing sandbox {sandbox.id}...")
        sandbox.close()
        print("Sandbox closed.")


def main():
    """
    Entry point for the example.
    """
    print("=" * 60)
    print("Claude Code with E2B Sandbox - Simple Example")
    print("=" * 60)
    
    try:
        run_claude_with_e2b_skills()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
