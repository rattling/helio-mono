# Helionyx Deployment Guide

**Target Platform**: node1 (Linux with systemd)  
**Deployment Model**: Same-host multi-environment  
**Audience**: Operators with SSH access to node1

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [First-Time Setup](#first-time-setup)
4. [Telegram Bot Setup](#telegram-bot-setup)
5. [Standard Deployment](#standard-deployment)
6. [Operations](#operations)
7. [Troubleshooting](#troubleshooting)
8. [Rollback](#rollback)

---

## Overview

This guide covers deploying and operating Helionyx on **node1** with support for multiple isolated environments (dev, staging, live) running simultaneously on the same host.

**Key Concepts:**
- Each environment has its own port, data directory, systemd service, and Telegram bot
- Deployments are idempotent and preserve event log data
- All operations are make-based for consistency
- systemd manages service lifecycle and logging

**Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md#deployment-architecture-m3) for detailed deployment architecture.

---

## Prerequisites

Before deploying Helionyx, ensure you have:

### System Requirements
- **SSH access** to node1 with appropriate permissions
- **Linux OS** with systemd (Ubuntu 20.04+ or equivalent)
- **Python 3.11+** installed
- **sudo access** for systemd service installation
- **Git** installed

### Network Requirements
- **Outbound HTTPS** for OpenAI API access
- **Outbound HTTPS** for Telegram API access
- **Ports available**: 8000 (dev), 8001 (staging), 8002 (live)

### Credentials
- **OpenAI API key** (for LLM extraction)
- **Telegram bot tokens** (one per environment - see [Telegram Bot Setup](#telegram-bot-setup))
- **Telegram chat ID** (your personal chat ID)

### Knowledge
- Basic Linux command line
- Basic systemd service management
- Basic Git operations

---

## First-Time Setup

Follow these steps for initial deployment on node1.

### 1. Clone Repository

```bash
ssh user@node1
cd ~/repos
git clone git@github.com:rattling/helio-mono.git
cd helio-mono
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
make install
# Or manually:
.venv/bin/pip install -e ".[dev,extraction,telegram]"
```

### 4. Configure Environments

Create environment-specific configuration files:

```bash
# Copy example files (if they exist) or create from template
cp .env.dev.example .env.dev
cp .env.staging.example .env.staging
cp .env.live.example .env.live

# Or create from template
cp .env.template .env.dev
cp .env.template .env.staging
cp .env.template .env.live
```

Edit each file with environment-specific settings:

**`.env.dev`** (development):
```bash
LOG_LEVEL=DEBUG
API_HOST=0.0.0.0
API_PORT=8000
EVENT_STORE_PATH=/var/lib/helionyx/dev/events
PROJECTIONS_DB_PATH=/var/lib/helionyx/dev/projections/helionyx.db

# Optional (used by backup/restore scripts)
BACKUP_ROOT=/var/lib/helionyx/backups

# OpenAI (can use mock for dev)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini

# Telegram (dev bot)
TELEGRAM_BOT_TOKEN=your_dev_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Cost controls
LLM_DAILY_COST_LIMIT_USD=5.0
```

**`.env.staging`** (staging):
```bash
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8001
EVENT_STORE_PATH=/var/lib/helionyx/staging/events
PROJECTIONS_DB_PATH=/var/lib/helionyx/staging/projections/helionyx.db

# Optional (used by backup/restore scripts)
BACKUP_ROOT=/var/lib/helionyx/backups

# OpenAI (real API)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini

# Telegram (staging bot)
TELEGRAM_BOT_TOKEN=your_staging_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Cost controls
LLM_DAILY_COST_LIMIT_USD=10.0
```

**`.env.live`** (production):
```bash
LOG_LEVEL=WARNING
API_HOST=0.0.0.0
API_PORT=8002
EVENT_STORE_PATH=/var/lib/helionyx/live/events
PROJECTIONS_DB_PATH=/var/lib/helionyx/live/projections/helionyx.db

# Optional (used by backup/restore scripts)
BACKUP_ROOT=/var/lib/helionyx/backups

# OpenAI (real API)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini

# Telegram (live bot)
TELEGRAM_BOT_TOKEN=your_live_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Cost controls
LLM_DAILY_COST_LIMIT_USD=50.0
```

**Security Note:** Never commit `.env.*` files with real credentials to git. They are gitignored.

### 5. Create Data Directories

```bash
# Dev environment (requires sudo)
sudo mkdir -p /var/lib/helionyx/dev/events
sudo mkdir -p /var/lib/helionyx/dev/projections

# Staging environment (requires sudo)
sudo mkdir -p /var/lib/helionyx/staging/events
sudo mkdir -p /var/lib/helionyx/staging/projections

# Live environment (requires sudo)
sudo mkdir -p /var/lib/helionyx/live/events
sudo mkdir -p /var/lib/helionyx/live/projections
sudo chown -R $USER:$USER /var/lib/helionyx

# Optional: backups root (if using BACKUP_ROOT)
sudo mkdir -p /var/lib/helionyx/backups
sudo chown -R $USER:$USER /var/lib/helionyx/backups
```

### 6. Install systemd Services

```bash
# Install service files
sudo cp deployment/systemd/helionyx-dev.service /etc/systemd/system/
sudo cp deployment/systemd/helionyx-staging.service /etc/systemd/system/
sudo cp deployment/systemd/helionyx.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services (auto-start on boot - optional)
sudo systemctl enable helionyx-dev
sudo systemctl enable helionyx-staging
sudo systemctl enable helionyx  # live

# Start services
sudo systemctl start helionyx-dev
sudo systemctl start helionyx-staging
sudo systemctl start helionyx
```

### 7. Verify Installation

```bash
# Check service status
make status ENV=dev
make status ENV=staging
make status ENV=live

# Check logs
make logs ENV=dev

# Test API endpoints
curl http://localhost:8000/health  # dev
curl http://localhost:8001/health  # staging
curl http://localhost:8002/health  # live
```

**Expected Response:**
```json
{"status": "healthy", "environment": "dev"}
```

---

## Telegram Bot Setup

Each environment requires its own Telegram bot. This is a **one-time manual setup** performed by the human operator.

### Create Bots via @BotFather

1. Open Telegram and search for **@BotFather**
2. Start a chat and use `/newbot` command
3. Create three bots:
   - **helionyx_dev_bot** (or your preferred name)
   - **helionyx_staging_bot**
   - **helionyx_bot** (production)
4. BotFather will provide a **bot token** for each - save these securely

### Get Your Chat ID

1. Start a chat with each bot (send `/start` message)
2. Run the bot temporarily to capture your chat ID:
   ```bash
   ENV=dev make run
   # Send a message to your dev bot
   # Check logs for: "Received message from chat_id: 123456789"
   ```
3. Note your chat ID (same for all bots)

### Update Configuration

Add bot tokens and chat ID to your `.env.{env}` files:

```bash
# In .env.dev
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz12345678
TELEGRAM_CHAT_ID=123456789

# In .env.staging
TELEGRAM_BOT_TOKEN=9876543210:XYZabcDEFghiJKLmnoPQRstuvWXYZ98765432
TELEGRAM_CHAT_ID=123456789

# In .env.live
TELEGRAM_BOT_TOKEN=1357924680:QWErtyUIOPasdfGHJKLzxcVBNM13579246
TELEGRAM_CHAT_ID=123456789
```

### Verify Telegram Integration

```bash
# Start service (if not already running)
sudo systemctl restart helionyx-dev

# Check logs for successful bot startup
make logs ENV=dev

# Send /start to your dev bot in Telegram
# Bot should respond with welcome message
```

**Benefits of Separate Bots:**
- Development testing doesn't spam production bot
- Bot username clearly indicates environment (@helionyx_dev_bot)
- Safe testing of notification changes
- True environment isolation

---

## Standard Deployment

Use these commands to deploy updates to running environments.

### Deploy to Environment

```bash
# Deploy to dev
make deploy ENV=dev

# Deploy to staging
make deploy ENV=staging

# Deploy to live
make deploy ENV=live
```

**What `make deploy` does:**
1. Validates environment and prerequisites
2. Creates backup point (git commit ref)
3. Pulls latest code from appropriate milestone branch
4. Updates dependencies if needed
5. Restarts systemd service
6. Verifies service health
7. Reports success or initiates rollback on failure

**Deployment is idempotent** - safe to run multiple times.

### Deployment Workflow

Typical deployment sequence:

```bash
# 1. Develop and test locally
ENV=dev make run

# 2. Commit and push changes
git add .
git commit -m "feat: add new feature"
git push origin milestone-3

# 3. Deploy to dev on node1
ssh user@node1
cd ~/repos/helio-mono
make deploy ENV=dev

# 4. Test in dev environment
make status ENV=dev
make logs ENV=dev
curl http://localhost:8000/health

# 5. If successful, deploy to staging
make deploy ENV=staging

# 6. Run staging validation
make status ENV=staging
# Test with staging bot

# 7. If validated, deploy to live
make deploy ENV=live

# 8. Monitor live environment
make logs ENV=live
make status ENV=live
```

---

## Operations

Common operational tasks.

### Check Service Status

```bash
# Via make (recommended)
make status ENV=dev
make status ENV=staging
make status ENV=live

# Via systemctl directly
sudo systemctl status helionyx-dev
sudo systemctl status helionyx-staging
sudo systemctl status helionyx
```

**Healthy Output:**
```
● helionyx-dev.service - Helionyx Development Environment
     Loaded: loaded
     Active: active (running) since...
```

### View Logs

```bash
# Via make (recommended)
make logs ENV=dev

# Via journalctl directly
sudo journalctl -u helionyx-dev -f -n 100

# View specific time range
sudo journalctl -u helionyx-dev --since "1 hour ago"

# View log files
tail -f /var/log/helionyx-dev.log
```

### Restart Service

```bash
# Via make (recommended)
make restart ENV=dev

# Via systemctl directly
sudo systemctl restart helionyx-dev
```

**When to restart:**
- After configuration changes
- After manual code updates
- Service appears unresponsive
- Memory/resource issues

### Stop Service

```bash
# Via make (recommended)
make stop ENV=dev

# Via systemctl directly
sudo systemctl stop helionyx-dev
```

**When to stop:**
- Maintenance window
- Debugging issues
- Manual data operations
- Decommissioning environment

### Start Service

```bash
# Via systemctl
sudo systemctl start helionyx-dev

# Or use restart if already stopped
make restart ENV=dev
```

### Check Event Log

```bash
# View recent events
.venv/bin/python scripts/view_events.py

# Count events
wc -l data/dev/events/*.jsonl

# Search for specific event type
grep '"event_type":"MessageIngestedEvent"' data/dev/events/*.jsonl | wc -l
```

### Rebuild Projections

```bash
# If projections get out of sync
ENV=dev .venv/bin/python scripts/rebuild_projections.py

# Check result
ENV=dev .venv/bin/python scripts/query_live.py
```

---

## Troubleshooting

### Service Won't Start

**Symptoms:** `systemctl status` shows `failed` or `inactive (dead)`

**Check:**
```bash
# View error logs
sudo journalctl -u helionyx-dev -n 50 --no-pager

# Check configuration
ENV=dev .venv/bin/python -c "from shared.common.config import Config; c=Config.from_env(); print(f'Port: {c.API_PORT}')"

# Check port availability
sudo lsof -i :8000
```

**Common Causes:**
- Port already in use by another process
- Missing or invalid `.env.dev` file
- Missing Telegram bot token
- Missing data directories
- Python virtual environment issues

**Solutions:**
```bash
# Kill process using port
sudo kill $(sudo lsof -t -i:8000)

# Verify .env file exists and is readable
ls -la .env.dev
cat .env.dev | grep TELEGRAM_BOT_TOKEN

# Create missing directories
mkdir -p ./data/dev/events ./data/dev/projections

# Reinstall dependencies
.venv/bin/pip install -e ".[dev,extraction,telegram]"
```

### Service Crashes Repeatedly

**Symptoms:** Service starts but crashes within seconds

**Check:**
```bash
# Full logs
sudo journalctl -u helionyx-dev -n 200 --no-pager

# Check for Python errors
make logs ENV=dev | grep -i error
make logs ENV=dev | grep -i traceback
```

**Common Causes:**
- Invalid OpenAI API key
- Invalid Telegram credentials
- Database corruption
- Code errors

**Solutions:**
```bash
# Validate OpenAI key
ENV=dev .venv/bin/python -c "from services.extraction.openai_client import OpenAILLMService; import os; os.environ['ENV']='dev'; from shared.common.config import Config; c=Config.from_env(); s=OpenAILLMService(c); print('OK')"

# Rebuild projections
ENV=dev .venv/bin/python scripts/rebuild_projections.py

# Check for code errors
.venv/bin/pytest tests/ -v
```

### Wrong Environment Running

**Symptoms:** Service responds but uses wrong configuration

**Check:**
```bash
# Verify service file
cat /etc/systemd/system/helionyx-dev.service | grep EnvironmentFile

# Check which config is loaded
sudo journalctl -u helionyx-dev -n 20 | grep ENV
```

**Solution:**
```bash
# Ensure correct .env file in service definition
sudo systemctl edit --full helionyx-dev
# Verify: EnvironmentFile=/path/to/.env.dev

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart helionyx-dev
```

### Telegram Bot Not Responding

**Symptoms:** Bot doesn't reply to messages

**Check:**
```bash
# Check bot is running
make status ENV=dev

# Check logs for Telegram errors
make logs ENV=dev | grep -i telegram

# Verify bot token
echo $TELEGRAM_BOT_TOKEN
```

**Common Causes:**
- Invalid bot token
- Bot not started in code
- Network connectivity issues
- Chat ID mismatch

**Solutions:**
```bash
# Test bot token manually
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe

# Verify chat ID
# Send message to bot, check logs for actual chat ID

# Restart service
make restart ENV=dev
```

### High Cost / LLM Rate Limits

**Symptoms:** Logs show rate limit errors or cost warnings

**Check:**
```bash
# Check LLM usage events
grep '"event_type":"ObjectExtractedEvent"' data/dev/events/*.jsonl | wc -l

# View cost warnings in logs
make logs ENV=dev | grep -i "cost\|limit"
```

**Solutions:**
```bash
# Reduce cost limits in .env.dev
# LLM_DAILY_COST_LIMIT_USD=1.0

# Use mock LLM for dev
# (Code supports this but requires implementation)

# Monitor usage
make logs ENV=dev | grep "LLM request"
```

### Data Loss / Event Log Issues

**Symptoms:** Events missing or queries return no results

**Check:**
```bash
# Verify event files exist
ls -lh data/dev/events/

# Count events
cat data/dev/events/*.jsonl | wc -l

# Check projections DB
sqlite3 data/dev/projections/helionyx.db "SELECT COUNT(*) FROM todos;"
```

**Solutions:**
```bash
# Event log is append-only and should never be lost
# If events exist, rebuild projections
ENV=dev .venv/bin/python scripts/rebuild_projections.py

# If events are truly missing, check backups (M4)
# Events should never be deleted by deployment
```

---

## Rollback

If a deployment fails or introduces issues, rollback to the previous version.

### Automatic Rollback

The deployment script attempts automatic rollback if:
- Service fails to start after update
- Health check fails after deployment
- Critical error detected during deploy

### Manual Rollback

```bash
# 1. Note current commit
git rev-parse HEAD

# 2. Find previous working commit
git log --oneline -n 10

# 3. Checkout previous commit
git checkout <previous-commit-hash>

# 4. Reinstall dependencies (if changed)
.venv/bin/pip install -e ".[dev,extraction,telegram]"

# 5. Restart service
make restart ENV=dev

# 6. Verify health
make status ENV=dev
curl http://localhost:8000/health

# 7. If successful, update remote (optional)
git push origin HEAD:milestone-3 --force
```

### Rollback Checklist

- [ ] Note current commit for potential re-forward
- [ ] Checkout known-good commit
- [ ] Reinstall dependencies if required
- [ ] Restart service
- [ ] Verify health and functionality
- [ ] Check event log is intact
- [ ] Test critical user flows
- [ ] Update team/documentation if needed

### Rollback Limitations

**What rollback preserves:**
- Event log (never touched by deployment)
- Projection data (can be rebuilt)
- Configuration files

**What rollback does NOT preserve:**
- In-flight requests during restart
- Temporary state (by design)
- Scheduled tasks not yet executed

**Data Safety:** Event log is append-only and never mutated by deployment or rollback. All other state can be reconstructed.

---

## Best Practices

### Deployment Discipline
- Always deploy to dev first
- Validate in staging before live
- Use `make deploy` (not manual steps)
- Monitor logs after deployment
- Keep deployment atomic (all environments on same commit)

### Configuration Management
- Never commit `.env.*` files with secrets
- Use `.env.template` as reference
- Document environment-specific values
- Rotate credentials periodically

### Monitoring
- Check `make status` regularly
- Review logs for errors/warnings
- Monitor LLM cost via logs
- Verify Telegram bot responsiveness

### Data Management
- Event log is source of truth
- Projections are derived and rebuildable
- Backup `.env` files separately (M4)
- Never manually edit event log files

---

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture including deployment model
- [PROJECT_CHARTER.md](PROJECT_CHARTER.md) - Project vision and principles
- [MILESTONE3_CHARTER.md](MILESTONE3_CHARTER.md) - Milestone 3 goals and scope
- `.env.template` - Configuration reference
- `deployment/systemd/README.md` - systemd service details

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review logs: `make logs ENV=<env>`
3. Check GitHub issues: https://github.com/rattling/helio-mono/issues
4. Consult related documentation

**Remember:** The event log is immutable and durable. If something breaks, projections can be rebuilt, and services can be restarted. The system is designed for operational resilience.
