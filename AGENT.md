# LLM Agent Documentation

## Overview
This agent (`agent.py`) is a CLI tool that sends questions to an LLM and returns structured JSON responses. It supports both simple question-answering (Task 1) and tool-augmented interactions with a project wiki (Task 2).

## Architecture

### Task 1: Simple LLM Call
- **Input**: Question as command-line argument
- **Processing**: Sends question to LLM API with system prompt
- **Output**: JSON with `answer` and `tool_calls` fields (empty array)

### Task 2: Documentation Agent with Tools
- **Input**: Question as command-line argument
- **Processing**: Agentic loop with tool calling
  1. LLM receives question + tool schemas
  2. If LLM returns tool calls → execute tools, append results, loop back
  3. If LLM returns plain text → extract answer and source, format JSON, exit
  4. Maximum 10 tool calls per question
- **Output**: JSON with `answer`, `source`, and `tool_calls` fields

#### Tools
- **`read_file`**: Reads a file given a relative `path`. Returns contents or error. Blocks directory traversal (`../`).
- **`list_files`**: Lists directory contents at a given relative `path`. Returns newline-separated entries. Blocks directory traversal (`../`).

#### Security
- Both tools validate paths to prevent directory traversal attacks
- Paths containing `../` are rejected

## LLM Provider: Qwen Code API
- **Provider**: Qwen Code (1000 free requests/day)
- **Model**: qwen3-coder-plus
- **API Compatibility**: OpenAI-compatible chat completions API
- **Authentication**: API key stored in `.env.agent.secret`

## Setup Instructions

### 1. Environment Configuration
Copy the example environment file and edit it:
```bash
cp .env.agent.example .env.agent.secret
```

Edit `.env.agent.secret`:
- `LLM_API_KEY`: Your Qwen API key
- `LLM_API_BASE`: `http://<VM_IP>:<port>/v1`
- `LLM_MODEL`: `qwen3-coder-plus`

### 2. Dependencies
Ensure dependencies are installed via `uv sync --dev`

## Usage

### Task 1: Simple Question
```bash
uv run agent.py "What is the capital of France?"
```

Output:
```json
{"answer": "The capital of France is Paris.", "tool_calls": []}
```

### Task 2: Wiki Question
```bash
uv run agent.py "How do I resolve merge conflicts?"
```

Output:
```json
{
  "answer": "To resolve merge conflicts...",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "git-workflow.md\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-workflow.md"},
      "result": "# Git Workflow\n..."
    }
  ]
}
```

## Testing

### Task 1 Regression Test
Run: `pytest tests/test_agent_task1.py -v`
- Validates JSON output structure
- Checks for required fields (`answer`, `tool_calls`)

### Task 2 Regression Tests
Run: `pytest tests/test_agent_task2.py -v`
- Test `read_file` tool execution and source formatting
- Test `list_files` tool execution

## Error Handling
- Missing API configuration → exit with error to stderr
- API timeout/error → exit with error to stderr
- Invalid input → exit with error to stderr
- Directory traversal attempts → blocked with error
- Max tool calls reached → output best answer with warning