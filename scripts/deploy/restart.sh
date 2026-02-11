#!/usr/bin/env bash
# Restart Helionyx service for specified environment
# Usage: restart.sh <env>
# Environments: dev, staging, live

set -euo pipefail

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

info "Restarting Helionyx service: $SERVICE_NAME (env: $ENV)"

# Check if systemd service exists
if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    error "Service $SERVICE_NAME is not installed"
    echo "To install, see: deployment/systemd/README.md"
    exit 1
fi

# Restart the service
if ! sudo systemctl restart "$SERVICE_NAME"; then
    error "Failed to restart service"
    exit 1
fi

success "Service restart initiated"

# Wait for service to stabilize
info "Waiting for service to start..."
sleep 2

# Check if service is running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    success "Service is running"
    echo ""
    info "Recent logs:"
    sudo journalctl -u "$SERVICE_NAME" -n 10 --no-pager
else
    error "Service failed to start"
    echo ""
    info "Service status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager || true
    exit 1
fi
