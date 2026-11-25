---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Hooks

> This file extends `.agents/hooks.json` with Python specific content.

## PostToolUse Hooks

Configure in `.agents/hooks.json`:

- **black/ruff**: Auto-format `.py` files after edit
- **mypy/pyright**: Run type checking after editing `.py` files

## Warnings

- Warn about `print()` statements in edited files (use `logging` module instead)
