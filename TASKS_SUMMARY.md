# Lab 6 Tasks Summary

## ✅ Task 1: Call an LLM from Code - COMPLETED

### Deliverables
- ✅ **Plan**: `plans/task-1.md` - Documents LLM provider (Qwen Code API), model (qwen3-coder-plus), and agent structure
- ✅ **Agent**: `agent.py` - Simple CLI that queries LLM and returns JSON with `answer` and `tool_calls` fields
- ✅ **Documentation**: `AGENT.md` - Complete architecture and setup documentation
- ✅ **Test**: `tests/test_agent_task1.py` - Regression test validating JSON output structure

### Branch
- **Branch**: `task-1-llm-agent`
- **Status**: Pushed to origin

### Manual Steps Needed
1. Create GitHub Issue: `[Task] Call an LLM from Code`
2. Create PR from `task-1-llm-agent` branch with "Closes #<issue-number>"
3. Get partner approval
4. Merge PR

---

## ✅ Task 2: The Documentation Agent - COMPLETED

### Deliverables
- ✅ **Plan**: `plans/task-2.md` - Documents tool schema design, agentic loop, and path security
- ✅ **Agent**: `agent.py` - Full implementation with:
  - `read_file` tool - reads files with path traversal protection
  - `list_files` tool - lists directories with path traversal protection
  - Agentic loop with max 10 tool calls limit
  - OpenAI function calling integration
  - JSON output with `answer`, `source`, and `tool_calls` fields
- ✅ **Documentation**: `AGENT.md` - Updated with tools, agentic loop, and system prompt strategy
- ✅ **Tests**: `tests/test_agent_task2.py` - 2 regression tests:
  - Test `read_file` tool execution and source formatting
  - Test `list_files` tool execution
  - Bonus: Test max tool calls limit

### Branch
- **Branch**: `task-2-documentation-agent`
- **Status**: Pushed to origin

### Manual Steps Needed
1. Create GitHub Issue: `[Task] The Documentation Agent`
2. Create PR from `task-2-documentation-agent` branch with "Closes #<issue-number>"
3. Get partner approval
4. Merge PR

---

## Configuration

### `.env.agent.secret` (Already configured)
```
LLM_API_KEY=sk-087c7084d4dd4bbcbba202c33a76d631
LLM_API_BASE=http://10.93.26.61:42005/v1
LLM_MODEL=qwen3-coder-plus
```

---

## Testing

### Task 1 Test
```bash
pytest tests/test_agent_task1.py -v
```

### Task 2 Tests
```bash
pytest tests/test_agent_task2.py -v
```

### Manual Testing
```bash
# Task 1: Simple question
uv run agent.py "What is 2+2?"

# Task 2: Wiki question (uses tools)
uv run agent.py "How do I resolve merge conflicts?"
```

---

## Security Features
- ✅ Directory traversal prevention (`../` blocked)
- ✅ Path validation in both tools
- ✅ Max tool calls limit (10)
- ✅ API keys stored in `.env.agent.secret` (not hardcoded)

---

## Next Steps
Since GitHub CLI (`gh`) is not installed on your system, you'll need to manually:

1. Go to: https://github.com/Locks4/se-toolkit-lab-6
2. Create Issue for Task 1
3. Create PR from `task-1-llm-agent` → `main`
4. Get partner approval
5. Merge PR
6. Repeat for Task 2 with `task-2-documentation-agent` branch

All code is complete and ready for review!
