---
paths:
  - "**/*.kt"
  - "**/*.kts"
  - "**/build.gradle.kts"
---
# Kotlin Hooks

> This file extends `.agents/hooks.json` with Kotlin-specific content.

## PostToolUse Hooks

Configure in `.agents/hooks.json`:

- **ktfmt/ktlint**: Auto-format `.kt` and `.kts` files after edit
- **detekt**: Run static analysis after editing Kotlin files
- **./gradlew build**: Verify compilation after changes
