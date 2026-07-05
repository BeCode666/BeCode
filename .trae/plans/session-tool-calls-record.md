# Plan: 在 Session JSON 中记录工具调用（不含响应）

## 需求

每轮对话保存的 session JSON 中，需要新增记录：
- 调用了哪些工具（tool name）
- 传递的参数（args）
- **不需要**记录工具的响应

## 改动清单

### 1. `src/ui/callbacks.py` — ToolCallCapture

- 增加 `_tool_calls: list[dict]` 累加器
- `on_tool_start` 中记录 `{"tool": name, "args": dict}`（不含响应）
- 新增 `get_tool_calls()` / `clear_tool_calls()` 公开方法

### 2. `src/core/orchestrator.py` — Orchestrator.run()

- Coder 运行结束后：`coder_callback.get_tool_calls()` → 写入 `session.add_entry(..., metadata={"tool_calls": ...})`
- Reviewer 运行结束后：同理

### 3. `src/core/session_store.py` — 注释更新

- 补充 docstring 说明 metadata.tool_calls 字段

## 数据格式示例

```json
{
  "history": [{
    "turn": 1,
    "role": "coder",
    "content": "...",
    "metadata": {
      "tool_calls": [
        {"tool": "read_file", "args": {"path": "x.py"}},
        {"tool": "bash_exec", "args": {"command": "python test.py"}}
      ]
    }
  }]
}
```