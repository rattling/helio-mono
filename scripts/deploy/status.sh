#!/usr/bin/env bash
# Check Helionyx service status for specified environment
# Usage: status.sh [env]
# Environments: dev, staging, live (default: dev)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
ENV="${1:-dev}"

error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

info() {
    echo -e "${BLUE}$1${NC}"
}

# Validate environment
if [[ ! "$ENV" =~ ^(dev|staging|live)$ ]]; then
    error "Invalid environment: $ENV"
    echo "Usage: $0 [env]"
    echo "  env: dev (default), staging, or live"
    exit 1
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

echo ""
info "========================================"
info "Helionyx Status - Environment: $ENV"
info "Service: $SERVICE_NAME"
info "========================================"
echo ""

# Check if systemd service exists
if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    error "Service $SERVICE_NAME is not installed"
    echo ""
    echo "To install systemd service:"
    echo "  sudo cp deployment/systemd/${SERVICE_NAME}.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable ${SERVICE_NAME}"
    echo "  sudo systemctl start ${SERVICE_NAME}"
    echo ""
    exit 1
fi

# Show service status
info "Service Status:"
echo ""
sudo systemctl status "$SERVICE_NAME" --no-pager || true
echo ""

# Show whether service is enabled
if systemctl is-enabled --quiet "$SERVICE_NAME"; then
    success "Service is enabled (will start on boot)"
else
    echo -e "${YELLOW}⚠ Service is not enabled (will not start on boot)${NC}"
    echo "  To enable: sudo systemctl enable $SERVICE_NAME"
fi

# Check if service is active
if systemctl is-active --quiet "$SERVICE_NAME"; then
    success "Service is active and running"
else
    error "Service is not running"
    info "To start: sudo systemctl start $SERVICE_NAME"
fi

# Show recent logs
echo ""
info "Recent Logs (last 20 lines):"
echo ""
sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager

echo ""
info "========================================"
info "To view live logs: sudo journalctl -u $SERVICE_NAME -f"
info "========================================"
echo ""
