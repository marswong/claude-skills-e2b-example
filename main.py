#!/usr/bin/env python3
"""
Simple example of running code in E2B sandbox.

This example demonstrates:
1. Creating an E2B sandbox environment
2. Executing code in the E2B sandbox
3. Handling execution results
"""

import os
from e2b import Sandbox
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def execute_code_in_sandbox(sandbox: Sandbox, code: str) -> str:
    """
    Execute Python code in the E2B sandbox.
    
    Args:
        sandbox: E2B sandbox instance
        code: Python code to execute
    
    Returns:
        Output from the code execution
    """
    try:
        # Write code to a temporary file to avoid shell escaping issues
        temp_file = "/tmp/code_to_execute.py"
        sandbox.files.write(temp_file, code)
        
        # Execute the Python file
        result = sandbox.commands.run(f"python3 {temp_file}")
        
        # Clean up the temporary file
        try:
            sandbox.files.remove(temp_file)
        except:
            pass  # Ignore cleanup errors
        
        # Return stdout output, or stderr if there's an error
        if result.exit_code != 0:
            return f"Error (exit code {result.exit_code}): {result.stderr if result.stderr else 'Command failed'}"
        
        return result.stdout if result.stdout else "(No output)"
    except Exception as e:
        return f"Error executing code: {str(e)}"


def main():
    """
    Entry point for the example.
    """
    print("=" * 60)
    print("E2B Sandbox - Simple Example")
    print("=" * 60)
    
    try:
        # Create E2B sandbox
        print("\nCreating E2B sandbox...")
        sandbox = Sandbox()
        print("Sandbox created successfully")
        
        try:
            # Example Python code to execute
            code = """numbers = list(range(1, 11))
total = sum(numbers)
print(f"Numbers: {numbers}")
print(f"Sum: {total}")
"""
            
            print("\nExecuting code in E2B sandbox:")
            print("-" * 60)
            print(code.strip())
            print("-" * 60)
            
            # Execute in E2B sandbox
            output = execute_code_in_sandbox(sandbox, code)
            
            print("\nExecution Output:")
            print(output)
            print("=" * 60)
            
            print("\n✅ Example completed successfully!")
            
        finally:
            # Clean up sandbox
            print("\nClosing sandbox...")
            sandbox.close()
            print("Sandbox closed.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
