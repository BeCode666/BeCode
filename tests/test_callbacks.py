"""Tests for src.ui.callbacks — ToolCallCapture callback handler."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.ui.callbacks import ToolCallCapture, _extract_tool_output


class TestExtractToolOutput:
    """Verify _extract_tool_output handles various output types."""

    def test_plain_string(self):
        assert _extract_tool_output("hello") == "hello"

    def test_none_output(self):
        assert _extract_tool_output(None) == "(无输出)"

    def test_message_like_object(self):
        """Objects with .content attribute should use that."""
        obj = MagicMock()
        obj.content = "file content"
        assert _extract_tool_output(obj) == "file content"

    def test_message_with_empty_content(self):
        obj = MagicMock()
        obj.content = ""
        assert _extract_tool_output(obj) == "(无输出)"

    def test_message_with_none_content(self):
        obj = MagicMock()
        obj.content = None
        assert _extract_tool_output(obj) == "(无输出)"


class TestToolCallCapture:
    """Verify ToolCallCapture lifecycle."""

    def setup_method(self):
        self.capture = ToolCallCapture(agent_name="coder")

    def test_initial_state(self):
        assert self.capture.agent_name == "coder"
        assert self.capture.get_tool_calls() == []

    def test_on_tool_start_records_call(self):
        serialized = {"name": "read_file"}
        self.capture.on_tool_start(
            serialized=serialized,
            input_str="",
            run_id=uuid4(),
            inputs={"path": "test.py"},
        )
        calls = self.capture.get_tool_calls()
        assert len(calls) == 1
        assert calls[0]["tool"] == "read_file"
        assert calls[0]["args"]["path"] == "test.py"

    def test_on_tool_start_without_inputs(self):
        serialized = {"name": "bash_exec"}
        self.capture.on_tool_start(
            serialized=serialized,
            input_str="echo hello",
            run_id=uuid4(),
        )
        calls = self.capture.get_tool_calls()
        assert len(calls) == 1
        assert calls[0]["tool"] == "bash_exec"

    def test_on_tool_end_clears_state(self):
        """on_tool_end should pop the active tool entry for its run_id."""
        rid = uuid4()
        self.capture._active_tools[rid] = {
            "tool": "bash_exec",
            "args": {"command": "echo hi"},
        }
        self.capture.on_tool_end(output="hi", run_id=rid)
        assert rid not in self.capture._active_tools

    def test_on_tool_error_clears_state(self):
        """on_tool_error should pop the active tool entry for its run_id."""
        rid = uuid4()
        self.capture._active_tools[rid] = {
            "tool": "bash_exec",
            "args": {"command": "echo hi"},
        }
        self.capture.on_tool_error(
            Exception("Command failed"),
            run_id=rid,
        )
        assert rid not in self.capture._active_tools

    def test_parallel_tool_calls_dont_clobber(self):
        """Two concurrent tool runs must be tracked independently by run_id.

        This is the regression test for the 'unknown_tool' bug: when the
        LLM emits multiple tool_calls in one message, LangGraph's ToolNode
        executes them concurrently and the callbacks are interleaved.
        A single _current_tool variable would let the second on_tool_start
        overwrite the first, so the first on_tool_end would see the wrong
        tool (and the second would see None → 'unknown_tool').
        """
        rid_a = uuid4()
        rid_b = uuid4()

        # Tool A starts
        self.capture.on_tool_start(
            serialized={"name": "bash_exec"},
            input_str="",
            run_id=rid_a,
            inputs={"command": "echo A"},
        )
        # Tool B starts (before A finishes) — must NOT overwrite A
        self.capture.on_tool_start(
            serialized={"name": "web_search"},
            input_str="",
            run_id=rid_b,
            inputs={"query": "hello"},
        )

        assert self.capture._active_tools[rid_a]["tool"] == "bash_exec"
        assert self.capture._active_tools[rid_b]["tool"] == "web_search"

        # Tool A ends first — must retrieve A's info, not B's
        self.capture.on_tool_end(output="A result", run_id=rid_a)
        # Tool B ends after — must still find B's info
        self.capture.on_tool_end(output="B result", run_id=rid_b)

        # Both should be popped
        assert rid_a not in self.capture._active_tools
        assert rid_b not in self.capture._active_tools

        # Both calls recorded in order
        calls = self.capture.get_tool_calls()
        assert [c["tool"] for c in calls] == ["bash_exec", "web_search"]

    def test_clear_tool_calls(self):
        serialized = {"name": "read_file"}
        self.capture.on_tool_start(
            serialized=serialized,
            input_str="",
            run_id=uuid4(),
            inputs={"path": "x.py"},
        )
        assert len(self.capture.get_tool_calls()) == 1
        self.capture.clear_tool_calls()
        assert self.capture.get_tool_calls() == []
