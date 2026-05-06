---
name: cost-monitor
version: 1.0.0
description: Monitor MiniMax API usage, track session token counts, generate daily/weekly cost reports, and alert on budget thresholds for Hermes.
emoji: 💰
tags:
  - cost
  - monitoring
  - minimax
  - tokens
  - budget
  - api-usage
  - reports
---

# Hermes Cost Monitor — MiniMax API Usage Tracking

Track MiniMax API usage, session token counts, and generate cost reports for Hermes.

## The Problem

Running Hermes with MiniMax API key-based pricing can be opaque:
- How many sessions are you running per day?
- What is the average context size per request?
- How many TTS calls are you making?
- When will you hit your budget limit?

## What This Skill Does

When triggered (via cron or manually), the skill:
1. Reads Hermes session logs and usage data
2. Calculates per-session and total token counts
3. Tracks TTS usage separately
4. Compares against configured budget thresholds
5. Sends alerts if limits are approaching
6. Generates daily/weekly cost reports

## Usage

Ask Hermes (or any agent with this skill):

```
"Give me a cost report for MiniMax API usage"
"How many sessions did I run today?"
"Am I going to hit my budget this week?"
"Show me TTS usage stats"
```

### Automated Daily Report (Cron)

```json5
{
  "name": "Daily Cost Report",
  "schedule": { "kind": "cron", "expr": "0 20 * * *", "tz": "Europe/Berlin" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run a MiniMax cost report. Check session logs and usage data. Report: total sessions, avg context size, TTS calls, total tokens, estimated cost. Send summary to user."
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce" }
}
```

### Weekly Summary (Cron)

```json5
{
  "name": "Weekly Cost Summary",
  "schedule": { "kind": "cron", "expr": "0 9 * * 1", "tz": "Europe/Berlin" },
  "payload": {
    "kind": "agentTurn",
    "message": "Generate weekly cost summary for MiniMax API. Include: 7-day trend, daily averages, projected monthly cost, budget status."
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce" }
}
```

## Cost Report Format

When generating a report, use this structure:

```markdown
## 💰 Hermes Cost Report — [Date]

### Session Overview
| Metric | Value |
|--------|-------|
| Sessions Today | 12 |
| Avg Context Size | 4.2K tokens |
| Total API Calls | 48 |
| TTS Calls | 23 |

### Token Usage Breakdown
| Type | Count | Est. Cost |
|------|-------|-----------|
| Text API (input) | 125K | — |
| Text API (output) | 89K | — |
| TTS (chars) | 12.5K | — |
| **Total** | 226K | Unknown* |

### Budget Status
- **Daily Budget:** $5.00 (warn at 80% = $4.00)
- **Current Spend:** ~$2.50 (50%)
- **Weekly Budget:** $30.00 (warn at 70% = $21.00)
- **Current Week:** ~$15.00 (50%)

### Trends
- Sessions: ↑ 12% from yesterday
- Avg context size: ↓ 5% from last week
- TTS usage: ↑ 8% from yesterday

### Recommendations
1. Consider reducing session context window for routine tasks
2. TTS usage is elevated — check if all calls are necessary
3. Enable context pruning for idle sessions
```

*Note: MiniMax M2.7 Plus has no public pricing. Cost estimation is based on API key billing.

## Metrics Tracked

### Session Metrics
- Sessions per day/week/month
- Average context size (tokens per session)
- Session duration
- Requests per session

### API Usage
- Total API calls (text completion)
- Input/output token ratios
- TTS character count
- TTS vs text API cost ratio

### Cost Indicators
- Estimated cost per session
- Daily/weekly cost projections
- Budget utilization percentage

## Alert Thresholds

Configure in your monitoring settings:

```markdown
## Budget Alerts
- Daily budget: $5.00 (warn at 80% = $4.00)
- Weekly budget: $30.00 (warn at 70% = $21.00)
- Monthly budget: $100.00 (warn at 75% = $75.00)
- TTS daily max: 50,000 chars (warn at 80%)
```

## Integration with DevOps Agent

If you have a DevOps/monitoring agent, add to its configuration:

```markdown
## Cost Monitoring
- Run daily cost report at 20:00
- Alert if daily spend exceeds $4.00
- Weekly summary every Monday 09:00
- Track trends: is usage going up or down?
```

## Python Scripts

Located in `~/.hermes/scripts/cost_monitor/`:

- `tracker.py` — Tracks and stores usage metrics
- `reporter.py` — Generates daily/weekly reports
- `alerts.py` — Checks thresholds and sends alerts
- `config.py` — Configuration management

### Direct Usage

```bash
# Get current usage stats
python3 ~/.hermes/scripts/cost_monitor/tracker.py

# Generate daily report
python3 ~/.hermes/scripts/cost_monitor/reporter.py --period daily

# Generate weekly report
python3 ~/.hermes/scripts/cost_monitor/reporter.py --period weekly

# Check alerts
python3 ~/.hermes/scripts/cost_monitor/alerts.py

# Update configuration
python3 ~/.hermes/scripts/cost_monitor/config.py --set daily_budget=5.00
```

## FAQ

**Q: How accurate are cost estimates?**
A: MiniMax M2.7 Plus has no public pricing. Estimates are based on observed API key billing patterns and should be treated as indicators, not exact figures.

**Q: What data sources are used?**
A: The tracker reads Hermes session logs (`~/.hermes/sessions/`) and any available usage telemetry.

**Q: How do I set up alerts?**
A: Configure thresholds in `~/.hermes/scripts/cost_monitor/config.json`. Alerts are checked on each tracker run.

**Q: Can I track historical data?**
A: Yes, the tracker maintains a SQLite database at `~/.hermes/cost_data.db` with historical usage.

## Changelog

### v1.0.0
- Initial release for Hermes/MiniMax
- Session and token tracking
- Daily/weekly report generation
- Budget alert thresholds
