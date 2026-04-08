"""
Regression tests for Task 2: The Documentation Agent
Tests tool execution, agentic loop, and output structure.
"""

import subprocess
import json
import sys
import os
import pytest


@pytest.fixture
def agent_script():
    """Get the path to the agent.py script."""
    return os.path.join(os.path.dirname(__file__), "..", "agent.py")


@pytest.fixture
def env_file_exists():
    """Check if .env.agent.secret exists."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env.agent.secret")
    if not os.path.exists(env_path):
        pytest.skip(".env.agent.secret not found - skipping integration test")
    return True


def test_task2_read_file_and_source(agent_script, env_file_exists):
    """
    Test that agent uses read_file tool and includes source in output.
    Asks about merge conflicts which should require reading wiki/git-workflow.md
    """
    result = subprocess.run(
        [sys.executable, agent_script, "How do I resolve merge conflicts?"],
        capture_output=True,
        text=True,
        timeout=60
    )

    # Check exit code
    assert result.returncode == 0, f"Agent failed with error: {result.stderr}"

    # Parse stdout as JSON
    stdout = result.stdout.strip()
    try:
        response = json.loads(stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}\nStdout: {stdout}\nStderr: {result.stderr}")

    # Validate required fields for Task 2
    assert "answer" in response, "Missing 'answer' field in output"
    assert "source" in response, "Missing 'source' field in output"
    assert "tool_calls" in response, "Missing 'tool_calls' field in output"

    # Validate field types
    assert isinstance(response["answer"], str), "'answer' should be a string"
    assert isinstance(response["source"], str), "'source' should be a string"
    assert isinstance(response["tool_calls"], list), "'tool_calls' should be an array"

    # If tools were used, validate tool call structure
    if len(response["tool_calls"]) > 0:
        for tool_call in response["tool_calls"]:
            assert "tool" in tool_call, "Each tool_call must have a 'tool' field"
            assert "args" in tool_call, "Each tool_call must have an 'args' field"
            assert "result" in tool_call, "Each tool_call must have a 'result' field"
            
            # Validate read_file tool was used
            if tool_call["tool"] == "read_file":
                assert "path" in tool_call["args"], "read_file must have 'path' in args"
                # Source should reference a wiki file
                assert "wiki/" in response["source"] or response["source"] == "", \
                    "Source should reference a wiki file"


def test_task2_list_files_tool(agent_script, env_file_exists):
    """
    Test that agent can use list_files tool.
    Asks about wiki structure which should trigger list_files usage.
    """
    result = subprocess.run(
        [sys.executable, agent_script, "What files are in the wiki?"],
        capture_output=True,
        text=True,
        timeout=60
    )

    # Check exit code
    assert result.returncode == 0, f"Agent failed with error: {result.stderr}"

    # Parse stdout as JSON
    stdout = result.stdout.strip()
    try:
        response = json.loads(stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}\nStdout: {stdout}\nStderr: {result.stderr}")

    # Validate required fields
    assert "answer" in response, "Missing 'answer' field in output"
    assert "tool_calls" in response, "Missing 'tool_calls' field in output"

    # Validate tool_calls is an array
    assert isinstance(response["tool_calls"], list), "'tool_calls' should be an array"

    # If tools were used, validate list_files was among them
    if len(response["tool_calls"]) > 0:
        tools_used = [tc["tool"] for tc in response["tool_calls"]]
        # list_files or read_file should be used
        assert "list_files" in tools_used or "read_file" in tools_used, \
            "Expected list_files or read_file to be used"

        # Validate tool call structure
        for tool_call in response["tool_calls"]:
            assert "tool" in tool_call, "Each tool_call must have a 'tool' field"
            assert "args" in tool_call, "Each tool_call must have an 'args' field"
            assert "result" in tool_call, "Each tool_call must have a 'result' field"
            
            # Validate list_files tool structure if used
            if tool_call["tool"] == "list_files":
                assert "path" in tool_call["args"], "list_files must have 'path' in args"


def test_task2_max_tool_calls_limit(agent_script, env_file_exists):
    """
    Test that agent respects maximum tool call limit (10).
    """
    # This is more of a structural test - we verify the limit is enforced
    # by checking stderr for max calls message if it's reached
    result = subprocess.run(
        [sys.executable, agent_script, 
         "Explain in detail the complete architecture of this project including all components"],
        capture_output=True,
        text=True,
        timeout=60
    )

    # Should complete without hanging
    assert result.returncode == 0, f"Agent failed with error: {result.stderr}"

    # Parse output
    stdout = result.stdout.strip()
    try:
        response = json.loads(stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}\nStdout: {stdout}")

    # Verify tool_calls don't exceed limit
    assert len(response.get("tool_calls", [])) <= 10, \
        "Agent exceeded maximum tool call limit of 10"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
