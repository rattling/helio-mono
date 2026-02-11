#!/usr/bin/env bash
# Deploy Helionyx to node1 for specified environment
# Usage: deploy.sh <env>
# Environments: dev, staging, live

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
ENV="${1:-}"

usage() {
    echo "Usage: $0 <env>"
    echo "  env: dev, staging, or live"
    echo ""
    echo "Example:"
    echo "  $0 dev"
    exit 1
}

error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Validate environment
if [[ -z "$ENV" ]]; then
    error "Environment not specified"
    usage
fi

if [[ ! "$ENV" =~ ^(dev|staging|live)$ ]]; then
    error "Invalid environment: $ENV"
    usage
fi

# Determine service name based on environment
case "$ENV" in
    dev)
        SERVICE_NAME="helionyx-dev"
        ;;
    staging)
        SERVICE_NAME="helionyx-staging"
        ;;
    live)
        SERVICE_NAME="helionyx"
        ;;
esac

info "Deploying Helionyx to environment: $ENV"
info "Service name: $SERVICE_NAME"
info "Project root: $PROJECT_ROOT"

# Check if we're on node1 (local deployment)
if [[ ! -f "$PROJECT_ROOT/.env.$ENV" ]]; then
    error "Configuration file not found: $PROJECT_ROOT/.env.$ENV"
    error "Please create this file before deploying."
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Create backup reference point (current commit)
BACKUP_COMMIT=$(git rev-parse HEAD)
BACKUP_BRANCH=$(git branch --show-current)
info "Current commit: $BACKUP_COMMIT"
info "Current branch: $BACKUP_BRANCH"

# Pull latest changes from remote
info "Pulling latest changes from origin/$BACKUP_BRANCH..."
if ! git pull origin "$BACKUP_BRANCH"; then
    error "Failed to pull latest changes"
    exit 1
fi

NEW_COMMIT=$(git rev-parse HEAD)
if [[ "$NEW_COMMIT" != "$BACKUP_COMMIT" ]]; then
    success "Updated from $BACKUP_COMMIT to $NEW_COMMIT"
else
    success "Already up to date"
fi

# Update dependencies
info "Updating dependencies..."
if ! .venv/bin/pip install -e ".[dev,extraction,telegram]" --quiet; then
    error "Failed to update dependencies"
    info "Rolling back to $BACKUP_COMMIT..."
    git reset --hard "$BACKUP_COMMIT"
    exit 1
fi
success "Dependencies updated"

# Check if systemd service exists
if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    info "Restarting systemd service: $SERVICE_NAME"
    
    # Restart the service
    if ! sudo systemctl restart "$SERVICE_NAME"; then
        error "Failed to restart service"
        info "Rolling back to $BACKUP_COMMIT..."
        git reset --hard "$BACKUP_COMMIT"
        .venv/bin/pip install -e ".[dev,extraction,telegram]" --quiet
        exit 1
    fi
    
    # Wait a moment for service to start
    sleep 2
    
    # Verify service is running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        success "Service $SERVICE_NAME is running"
    else
        error "Service failed to start"
        info "Checking service status:"
        sudo systemctl status "$SERVICE_NAME" --no-pager || true
        info "Rolling back to $BACKUP_COMMIT..."
        git reset --hard "$BACKUP_COMMIT"
        .venv/bin/pip install -e ".[dev,extraction,telegram]" --quiet
        sudo systemctl restart "$SERVICE_NAME"
        exit 1
    fi
    
    # Show logs
    info "Service logs (last 10 lines):"
    sudo journalctl -u "$SERVICE_NAME" -n 10 --no-pager
    
    success "Deployment complete!"
else
    success "Code and dependencies updated"
    info "Note: Systemd service $SERVICE_NAME not installed"
    info "To install, see: deployment/systemd/README.md"
    info "You can run manually with: ENV=$ENV make run"
fi
