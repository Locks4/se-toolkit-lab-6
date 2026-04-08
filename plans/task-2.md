# Task 2: The Documentation Agent - Implementation Plan

## Overview
Convert the Task 1 CLI agent into an LLM agent that uses tools to navigate the project wiki and answer questions based on documentation files.

## Tool Schema Design

### 1. read_file
- **Purpose**: Read the contents of a file
- **Parameters**: 
  - `path` (string): Relative path to the file (e.g., "wiki/git-workflow.md")
- **Returns**: File contents as string, or error message
- **Security**: Blocks directory traversal attempts (paths containing `../`)

### 2. list_files
- **Purpose**: List files in a directory
- **Parameters**:
  - `path` (string): Relative path to the directory (e.g., "wiki")
- **Returns**: Newline-separated list of files/directories
- **Security**: Blocks directory traversal attempts (paths containing `../`)

## Agentic Loop Implementation

### Loop Logic
1. Initialize conversation with user question + tool schemas in system prompt
2. Send messages to LLM
3. Check if response contains `tool_calls`:
   - **Yes**: Execute each tool, append results as `tool` role messages, loop back to step 2
   - **No**: Extract answer and source, format as JSON, exit
4. If 10 tool calls reached, stop loop and output current best answer

### Message Format
```python
messages = [
    {"role": "system", "content": system_prompt_withToolSchemas},
    {"role": "user", "content": user_question}
]

# After tool execution:
messages.append({
    "role": "tool",
    "tool_name": "read_file",
    "content": tool_result
})
```

## Path Security Measures

### Directory Traversal Prevention
- Both tools validate input paths
- Reject any path containing `../` or `..\\`
- Only allow relative paths from project root
- Resolve paths and verify they stay within allowed directories

### Implementation
```python
def validate_path(path: str) -> bool:
    """Ensure path doesn't contain directory traversal."""
    if ".." in path:
        return False
    return True
```

## System Prompt Strategy
The system prompt will:
1. Instruct the LLM to use `list_files` to discover wiki files first
2. Use `read_file` to examine relevant files
3. Always include a `source` field with the wiki file path and section anchor
4. Stop after finding the answer or reaching max tool calls (10)

## Output Format
```json
{
  "answer": "The answer text",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "git-workflow.md\\ngit.md\\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-workflow.md"},
      "result": "# Git Workflow\\n..."
    }
  ]
}
```

## Implementation Steps
1. Commit this plan before writing code ✓
2. Update `agent.py` to:
   - Define tool schemas for OpenAI function calling
   - Implement `read_file` and `list_files` functions
   - Add path validation and security checks
   - Implement agentic loop with tool execution
   - Format output with `answer`, `source`, and `tool_calls`
3. Update `AGENT.md` with tool documentation (already done)
4. Write 2 regression tests:
   - Test `read_file` tool execution and source formatting
   - Test `list_files` tool execution
5. Create GitHub issue and PR workflow

## Error Handling
- Invalid path → return error message to LLM
- File not found → return error message to LLM
- Max tool calls reached → output warning with best answer
- LLM API error → exit with error to stderr
- Invalid JSON output → exit with error to stderr
