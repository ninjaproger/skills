# Codex CLI Reference

## Primary Commands

### `codex exec` (alias: `codex e`)
Non-interactive background execution. The workhorse for automation.

```bash
codex exec [FLAGS] "PROMPT"
codex exec [FLAGS] -          # read prompt from stdin
```

**Key flags:**

| Flag | Values | Purpose |
|------|--------|---------|
| `--full-auto` | boolean | Shortcut: workspace-write + never approve. Use for autonomous runs. |
| `--output-last-message, -o` | path | Write final assistant message to file |
| `--json` | boolean | Emit newline-delimited JSON events |
| `--ephemeral` | boolean | Don't persist session files |
| `--cd, -C` | path | Set working directory before execution |
| `--image, -i` | path[,…] | Attach image files to prompt |
| `--skip-git-repo-check` | boolean | Allow runs outside Git repos |
| `--color` | always\|never\|auto | ANSI output control |

### `codex exec resume [SESSION_ID]`
Continue a prior session.

```bash
codex exec resume --last           # most recent session
codex exec resume --all            # search across directories
codex exec resume <SESSION_ID>
```

### `codex` (interactive)
Launch the TUI with an optional initial prompt.

```bash
codex "Start implementing X"
codex resume --last
codex fork --last                  # branch into a new thread
```

## Global Flags (all commands)

| Flag | Values | Purpose |
|------|--------|---------|
| `--model, -m` | string | Override model |
| `--sandbox, -s` | read-only \| workspace-write \| danger-full-access | Execution restrictions |
| `--ask-for-approval, -a` | untrusted \| on-request \| never | When to pause for approval |
| `--profile, -p` | string | Load config profile from config.toml |
| `--config, -c` | key=value | Override config value |
| `--add-dir` | path | Grant additional directory write access |
| `--enable` / `--disable` | feature | Force feature flags |

## Sandbox Modes

| Mode | File writes | Shell commands |
|------|-------------|----------------|
| `read-only` | No | No |
| `workspace-write` | Working dir only | Restricted |
| `danger-full-access` | Anywhere | Unrestricted |

`--full-auto` = `--sandbox workspace-write --ask-for-approval never`

## Other Commands

```bash
codex login                        # authenticate (ChatGPT OAuth)
codex login --with-api-key         # authenticate via API key from stdin
codex login status                 # check credentials
codex logout                       # remove credentials
codex cloud list --env <ENV_ID>    # list cloud tasks
codex apply <TASK_ID>              # apply cloud task diff locally
codex mcp list                     # list MCP servers
codex features list                # list feature flags
```

## Configuration

Config file: `~/.codex/config.toml`

Precedence: CLI `-c key=value` > profile > base config

## Safety

- Prefer `--add-dir` over `danger-full-access` for targeted access
- Never combine `--full-auto` with `--dangerously-bypass-approvals-and-sandbox` outside VMs
- Use `--json` + `--output-last-message` for CI/automation
