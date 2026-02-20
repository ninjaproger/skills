# Gemini CLI Reference

## Core Usage

```bash
gemini "prompt"              # one-shot, non-interactive
echo "text" | gemini         # stdin as prompt
cat file | gemini "context"  # combine stdin + positional prompt
gemini -i "prompt"           # run prompt then enter REPL
```

> The `--prompt` flag is deprecated — use positional arguments instead.

## Key Flags

| Flag | Values | Purpose |
|------|--------|---------|
| `--approval-mode` | `default` \| `auto_edit` \| `yolo` | Tool execution approval |
| `--model, -m` | string | Override model (default: `auto`) |
| `--output-format, -o` | `text` \| `json` \| `stream-json` | Output format |
| `--sandbox, -s` | boolean | Run in sandboxed environment |
| `--debug, -d` | boolean | Enable verbose logging |
| `--extensions` | ext1,ext2 | Load extensions |
| `--allowed-mcp-server-names` | server1,server2 | Allow specific MCP servers |

## Approval Modes

| Mode | Behavior |
|------|----------|
| `default` | Pauses for approval before tool calls |
| `auto_edit` | Auto-approves file edits, pauses for shell commands |
| `yolo` | No approval prompts — fully autonomous |

## Session Management

```bash
gemini -r "latest"           # resume most recent session
gemini -r "latest" "prompt"  # resume + new prompt
gemini -r "<session-id>"     # resume specific session
gemini --list-sessions       # list all sessions
gemini --delete-session <n>  # delete session by index
```

## Output Formats

- `text` (default) — human-readable plain text
- `json` — structured JSON response
- `stream-json` — newline-delimited JSON events (for streaming)

Use `--output-format json` in CI/automation for machine-readable results.

## Piping Context (Recommended Pattern)

Since Gemini reads stdin, pipe files directly to embed context without directory flags:

```bash
(cat skill.md reference.md; echo "---"; echo "Task: ...") | gemini --approval-mode yolo
```

Run from the project root (`cd [PROJECT_ROOT]`) so Gemini's file tool operations resolve correctly.
