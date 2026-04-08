#!/usr/bin/env python3
"""
Agent that calls an LLM to answer questions.
Supports both simple Q&A (Task 1) and tool-augmented wiki navigation (Task 2).
Usage: uv run agent.py "your question here"
"""

import os
import sys
import json
import dotenv
from openai import OpenAI
import argparse
from pathlib import Path
from typing import Any, Optional

# Load environment variables
dotenv.load_dotenv(".env.agent.secret")

# Constants
MAX_TOOL_CALLS = 10
PROJECT_ROOT = Path(__file__).parent


def validate_path(path: str) -> bool:
    """Ensure path doesn't contain directory traversal."""
    if ".." in path:
        return False
    return True


def read_file(path: str) -> str:
    """Read the contents of a file."""
    if not validate_path(path):
        return "Error: Directory traversal not allowed"
    
    file_path = PROJECT_ROOT / path
    if not file_path.exists():
        return f"Error: File not found: {path}"
    if not file_path.is_file():
        return f"Error: Not a file: {path}"
    
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {str(e)}"


def list_files(path: str) -> str:
    """List files in a directory."""
    if not validate_path(path):
        return "Error: Directory traversal not allowed"
    
    dir_path = PROJECT_ROOT / path
    if not dir_path.exists():
        return f"Error: Directory not found: {path}"
    if not dir_path.is_dir():
        return f"Error: Not a directory: {path}"
    
    try:
        entries = list(dir_path.iterdir())
        # Return relative paths
        relative_paths = [entry.relative_to(PROJECT_ROOT) for entry in entries]
        return "\n".join(str(p) for p in relative_paths)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


# Tool schemas for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file given a relative path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file (e.g., 'wiki/git-workflow.md')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the contents of a directory given a relative path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the directory (e.g., 'wiki')"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a documentation assistant that helps users find information in the project wiki. You have access to two tools:

1. `list_files(path)`: Lists files and directories at the given path
2. `read_file(path)`: Reads the contents of a file at the given path

Use these tools to navigate the wiki and find answers to user questions. Always:
- Start by using `list_files` to discover the wiki structure
- Use `read_file` to examine relevant files
- Provide your answer with a source reference in the format: `wiki/filename.md#section-anchor`
- If you can't find a specific section, use just the file path as the source

Be concise and accurate. Always cite your sources."""


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool and return the result."""
    if tool_name == "read_file":
        return read_file(arguments.get("path", ""))
    elif tool_name == "list_files":
        return list_files(arguments.get("path", ""))
    else:
        return f"Error: Unknown tool: {tool_name}"


def main():
    # Parse command line argument
    parser = argparse.ArgumentParser(description="LLM Agent")
    parser.add_argument("question", help="Question to ask the LLM")
    args = parser.parse_args()

    # Get API configuration from environment
    api_key = os.getenv("LLM_API_KEY")
    api_base = os.getenv("LLM_API_BASE")
    model = os.getenv("LLM_MODEL", "qwen3-coder-plus")

    if not api_key or not api_base:
        print("Error: LLM_API_KEY and LLM_API_BASE must be set in .env.agent.secret",
              file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize OpenAI-compatible client
        client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )

        # Print debug info to stderr
        print(f"Using model: {model}", file=sys.stderr)
        print(f"Question: {args.question}", file=sys.stderr)

        # Initialize conversation
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": args.question}
        ]

        # Agentic loop
        tool_calls_log = []
        tool_call_count = 0
        answer: Optional[str] = None

        while tool_call_count < MAX_TOOL_CALLS:
            # Make API call with tools
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            choice = response.choices[0]
            message = choice.message

            # Check if LLM wants to call tools
            if message.tool_calls:
                # Process tool calls
                messages.append(message)  # Add assistant's message with tool calls

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    # Parse arguments
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    print(f"Tool call: {tool_name}({tool_args})", file=sys.stderr)

                    # Execute tool
                    result = execute_tool(tool_name, tool_args)
                    print(f"Tool result length: {len(result)} chars", file=sys.stderr)

                    # Log tool call
                    tool_calls_log.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result
                    })

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": result
                    })

                    tool_call_count += 1
                    if tool_call_count >= MAX_TOOL_CALLS:
                        print(f"Max tool calls ({MAX_TOOL_CALLS}) reached", file=sys.stderr)
                        break

                if tool_call_count >= MAX_TOOL_CALLS:
                    # Max calls reached without final answer
                    answer = answer or "I was unable to find a complete answer within the allowed number of tool calls."
                    break
            else:
                # No tool calls, this is the final answer
                answer = message.content
                break

        # Safety fallback if answer is still None
        if answer is None:
            answer = "No answer was provided by the LLM."

        # Try to extract source from answer (if LLM provided one)
        # For Task 1 compatibility, if no tool calls were made, use simpler output
        if len(tool_calls_log) == 0:
            # Task 1 mode - no tools used
            result = {
                "answer": answer,
                "tool_calls": []
            }
        else:
            # Task 2 mode - tools used
            # Try to find source in answer or use last accessed file
            source = ""
            for log in reversed(tool_calls_log):
                if log["tool"] == "read_file":
                    source = log["args"].get("path", "")
                    break

            result = {
                "answer": answer,
                "source": source,
                "tool_calls": tool_calls_log
            }

        # Output JSON to stdout
        print(json.dumps(result))

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()