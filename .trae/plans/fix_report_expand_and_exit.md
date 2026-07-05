# Plan: 修复报告默认折叠 & 程序退出卡住问题

## 需求

1. Coder Agent 报告和 Reviewer Agent 报告默认展开显示（不折叠）
2. 工作流完成后程序自动退出，不卡在交互式回顾模式

## 变更点

### FR1: 报告默认展开

- **`src/ui/collapsible.py`** `add_agent_report()`: `collapsed=True` → `collapsed=False`
- **`src/ui/console.py`** `agent_report()`: `collapsed=True` → `collapsed=False`

### FR2: 程序自动退出

- **`main.py`**: 移除 `console.enter_interactive_mode()` 调用，替换为 `console.print("[dim]工作流已完成，程序退出。[/]")` 提示后自然退出

## 影响范围

- 无外部依赖变更
- 交互式回顾模式的方法 `enter_interactive_mode()` 仍保留在 `console.py` 中供将来使用
- 工具结果（`add_tool_result`）仍保持折叠，不影响
