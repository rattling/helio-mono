# Helionyx Systemd Service Configuration

This directory contains systemd service unit files for running Helionyx as a system service on node1.

## Available Services

Three service configurations are provided for multi-environment deployment:

- **`helionyx-dev.service`** - Development environment (port 8000)
- **`helionyx-staging.service`** - Staging environment (port 8001)
- **`helionyx.service`** - Production/live environment (port 8002)

Each service:
- Runs under the `john` user
- Uses environment-specific configuration file (`.env.dev`, `.env.staging`, `.env.live`)
- Automatically restarts on failure
- Logs to systemd journal
- Can be enabled for auto-start on boot

## Prerequisites

Before installing a service:

1. **Environment configuration file must exist**:
   ```bash
   # Create from example
   cp .env.dev.example .env.dev
   # Edit and fill in credentials
   nano .env.dev
   ```

2. **Virtual environment must be set up**:
   ```bash
   make install
   ```

3. **Service must run successfully manually**:
   ```bash
   ENV=dev make run
   # Test, then stop with Ctrl+C
   ```

## Installation

To install a service (e.g., dev environment):

```bash
# 1. Copy service file to systemd
sudo cp deployment/systemd/helionyx-dev.service /etc/systemd/system/

# 2. Reload systemd to recognize new service
sudo systemctl daemon-reload

# 3. Enable service to start on boot (optional)
sudo systemctl enable helionyx-dev

# 4. Start the service
sudo systemctl start helionyx-dev

# 5. Check status
sudo systemctl status helionyx-dev
```

## Service Management

### Check Status

```bash
# Development
sudo systemctl status helionyx-dev

# Staging
sudo systemctl status helionyx-staging

# Live
sudo systemctl status helionyx
```

Or use the helper script:
```bash
make status ENV=dev
```

### Start/Stop/Restart

```bash
# Start
sudo systemctl start helionyx-dev

# Stop
sudo systemctl stop helionyx-dev

# Restart
sudo systemctl restart helionyx-dev
```

Or use helper scripts:
```bash
make restart ENV=dev
make stop ENV=dev
```

### View Logs

```bash
# View recent logs
sudo journalctl -u helionyx-dev -n 50

# Follow logs (live tail)
sudo journalctl -u helionyx-dev -f

# View logs since boot
sudo journalctl -u helionyx-dev -b
```

Or use the helper script:
```bash
make logs ENV=dev          # Last 50 lines
scripts/deploy/logs.sh dev -f  # Follow live
```

### Enable/Disable Auto-start

```bash
# Enable (start on boot)
sudo systemctl enable helionyx-dev

# Disable (don't start on boot)
sudo systemctl disable helionyx-dev

# Check if enabled
systemctl is-enabled helionyx-dev
```

## Running Multiple Environments

All three services can run simultaneously on the same host:

```bash
# Install all three services
sudo cp deployment/systemd/helionyx-dev.service /etc/systemd/system/
sudo cp deployment/systemd/helionyx-staging.service /etc/systemd/system/
sudo cp deployment/systemd/helionyx.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start all environments
sudo systemctl start helionyx-dev
sudo systemctl start helionyx-staging
sudo systemctl start helionyx

# Check all are running
systemctl list-units 'helionyx*' --all
```

Each environment is fully isolated:
- Different ports (8000, 8001, 8002)
- Separate data directories
- Separate Telegram bots
- Independent configuration

## Troubleshooting

### Service fails to start

1. Check service status for error details:
   ```bash
   sudo systemctl status helionyx-dev
   ```

2. Check logs for detailed error messages:
   ```bash
   sudo journalctl -u helionyx-dev -n 100
   ```

3. Verify configuration file exists and is valid:
   ```bash
   ls -la .env.dev
   .venv/bin/python -c "from shared.common.config import Config; Config.from_env('dev')"
   ```

4. Test running manually:
   ```bash
   ENV=dev .venv/bin/python services/api/runner.py
   ```

### Port already in use

If you see "Address already in use" errors:

1. Check what's using the port:
   ```bash
   sudo lsof -i :8000
   ```

2. Make sure no duplicate service is running:
   ```bash
   systemctl list-units 'helionyx*' --all
   ```

3. Verify each environment uses a unique port in its `.env.{env}` file:
   ```bash
   grep API_PORT .env.dev .env.staging .env.live
   ```

### Permission issues

If you see permission errors:

1. Verify user/group in service file matches actual user:
   ```bash
   whoami  # Should match User= in service file
   ```

2. Ensure user has access to project directory:
   ```bash
   ls -la /home/john/repos/helio-mono
   ```

3. Check data directory permissions:
   ```bash
   ls -la data/
   ```

## Customization

To customize a service (e.g., change user, paths):

1. Edit the service file in this directory
2. Re-copy to `/etc/systemd/system/`
3. Reload systemd: `sudo systemctl daemon-reload`
4. Restart service: `sudo systemctl restart <service-name>`

**Important paths to update**:
- `User=` and `Group=` - System user to run as
- `WorkingDirectory=` - Project root directory
- `EnvironmentFile=` - Path to .env file
- `ExecStart=` - Full path to Python interpreter and runner script

## Security Notes

The service files include basic security hardening:
- `NoNewPrivileges=true` - Prevents privilege escalation
- `PrivateTmp=true` - Uses private /tmp directory

For production (live environment), consider additional hardening:
- Restrict filesystem access with `ProtectHome=`, `ReadOnlyPaths=`
- Limit resources with `MemoryMax=`, `CPUQuota=`
- Use dedicated service account instead of personal user

See `man systemd.exec` for full list of security options.

## Related Documentation

- **Deployment Guide**: [`docs/DEPLOYMENT.md`](../../docs/DEPLOYMENT.md)
- **Architecture**: [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- **Configuration**: [`.env.template`](../../.env.template)
