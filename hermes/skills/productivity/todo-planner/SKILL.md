---
version: "2.0.0"
name: todo-planner
description: "Organize todos with priorities, deadlines, and weekly views. Use when adding tasks, planning agendas, tracking progress, reviewing overdue items."
author: Adapted for Hermes from BytesAgain/todo-planner
category: productivity
tags:
  - todo
  - task-management
  - planning
  - productivity
  - tracking
tools:
  - python3
  - file_read
  - file_write
---

# Todo Planner

Todo Planner v2.0.0 — a productivity toolkit for managing tasks, plans, and reviews from the command line. All data is stored locally in flat log files with timestamps, making it easy to review history, export records, and search across entries.

## Commands

Run `python3 ~/.hermes/scripts/todo_planner/script.py <command> [args]` to use.

### Core Operations

| Command | Description |
|---------|-------------|
| `add <input>` | Log an add entry (e.g. add a new task, note, or action item) |
| `plan <input>` | Log a plan entry (e.g. create a daily/weekly plan, set goals) |
| `track <input>` | Log a track entry (e.g. track progress on a task or project) |
| `review <input>` | Log a review entry (e.g. review completed tasks, reflect on progress) |
| `streak <input>` | Log a streak entry (e.g. record daily streaks, habit tracking) |
| `remind <input>` | Log a remind entry (e.g. set reminders, note follow-ups) |
| `prioritize <input>` | Log a prioritize entry (e.g. rank tasks, flag urgent items) |
| `archive <input>` | Log an archive entry (e.g. archive completed tasks, move to done) |
| `tag <input>` | Log a tag entry (e.g. tag tasks with categories or labels) |
| `timeline <input>` | Log a timeline entry (e.g. plot tasks on a timeline, milestones) |
| `report <input>` | Log a report entry (e.g. daily/weekly task summaries) |
| `weekly-review <input>` | Log a weekly-review entry (e.g. end-of-week retrospectives) |

Each command without arguments shows the 20 most recent entries for that category.

### Utility Commands

| Command | Description |
|---------|-------------|
| `stats` | Summary statistics across all log categories with entry counts and disk usage |
| `export <fmt>` | Export all data in `json`, `csv`, or `txt` format |
| `search <term>` | Search across all log files for a keyword (case-insensitive) |
| `recent` | Show the 20 most recent entries from the global activity history |
| `status` | Health check — version, data directory, total entries, disk usage, last activity |
| `help` | Show full usage information |
| `version` | Show version string (`todo-planner v2.0.0`) |

## Data Storage

All data is persisted locally under `~/.hermes/todo-planner/`:

- **`<command>.log`** — One log file per command (e.g. `add.log`, `plan.log`, `track.log`)
- **`history.log`** — Global activity log with timestamps for every operation
- **`export.<fmt>`** — Generated export files (json/csv/txt)

Each entry is stored as `YYYY-MM-DD HH:MM|<input>` (pipe-delimited). No external services, no API keys, no network calls — everything stays on your machine.

## Hermes-Native Integrations

### Using with Hermes Todo Tool

Hermes provides a built-in todo tool for quick task management:

```
todo add "Write documentation for API endpoints"
todo list
todo complete "Write documentation for API endpoints"
```

### Knowledge Base Integration

Store important plans and decisions in `~/KnowledgeBase/` for semantic retrieval:

```bash
# Query the Knowledge Base for related tasks
python3 ~/KnowledgeBase/query.py --semantic "API documentation tasks"
```

### Session Context

Access recent session context from `~/.hermes/hermes_sessions.db` to understand what tasks were discussed:

```python
import sqlite3
conn = sqlite3.connect('~/.hermes/hermes_sessions.db')
cursor = conn.cursor()
cursor.execute("SELECT content FROM sessions WHERE timestamp > datetime('now', '-1 day')")
```

## Requirements

- **Python 3** 3.8+ with `set -euo pipefail`
- Standard Unix utilities: `date`, `wc`, `du`, `grep`, `tail`, `cat`, `sed`, `basename`
- No external dependencies or packages required
- No API keys or accounts needed

## When to Use

1. **Capturing tasks quickly** — Use `add` to log new tasks as they come to mind, building a searchable backlog you can organize later with `prioritize` and `tag`
2. **Planning your day or week** — Use `plan` to create structured daily agendas, then `track` progress throughout the day as you complete items
3. **Maintaining streaks and habits** — Use `streak` to record daily consistency, then `search` to review your habit patterns over time
4. **Running weekly retrospectives** — Use `weekly-review` to log end-of-week reflections, then `report` to generate summaries of what was accomplished
5. **Archiving and organizing** — Use `archive` to move completed work out of active view, `tag` to categorize tasks, and `timeline` to visualize milestones

## Examples

```bash
# Add a new task
python3 ~/.hermes/scripts/todo_planner/script.py add "Write blog post about productivity systems — due Friday"

# Plan your day
python3 ~/.hermes/scripts/todo_planner/script.py plan "Morning: code review, API docs. Afternoon: deploy staging, team sync"

# Track progress on a task
python3 ~/.hermes/scripts/todo_planner/script.py track "Blog post: draft complete, needs editing pass"

# Prioritize urgent items
python3 ~/.hermes/scripts/todo_planner/script.py prioritize "P1: Deploy hotfix. P2: Update docs. P3: Refactor tests"

# Tag a task with a category
python3 ~/.hermes/scripts/todo_planner/script.py tag "blog-post: writing, content, marketing"

# Run a weekly review
python3 ~/.hermes/scripts/todo_planner/script.py weekly-review "Completed 12/15 tasks. Carried over: API docs, test refactor, deploy script"

# Search for all entries mentioning 'deploy'
python3 ~/.hermes/scripts/todo_planner/script.py search deploy

# Export everything to CSV
python3 ~/.hermes/scripts/todo_planner/script.py export csv

# View summary statistics
python3 ~/.hermes/scripts/todo_planner/script.py stats
```

## File Structure

```
~/.hermes/todo-planner/
  add.log           # Task additions
  plan.log          # Plans
  track.log         # Progress tracking
  review.log        # Reviews
  streak.log        # Habit streaks
  remind.log        # Reminders
  prioritize.log    # Priority items
  archive.log       # Archived items
  tag.log           # Tags/labels
  timeline.log      # Timeline entries
  report.log        # Reports
  weekly-review.log # Weekly retrospectives
  history.log       # Global activity log

~/.hermes/scripts/todo_planner/
  script.py         # Main CLI script
```

## Privacy & Security

1. **All data stays local** — Never transmit todo contents to external services
2. **No network calls** — Everything works offline
3. **User owns their data** — Export or purge at any time

---

Adapted for Hermes from BytesAgain/todo-planner v2.0.0
