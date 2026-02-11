#!/usr/bin/env bash
# Tail Helionyx service logs for specified environment
# Usage: logs.sh <env> [lines]
# Environments: dev, staging, live
# Lines: number of lines to show (default: 50)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
ENV="${1:-}"
LINES="${2:-50}"

usage() {
    echo "Usage: $0 <env> [lines]"
    echo "  env: dev, staging, or live"
    echo "  lines: number of recent lines to show (default: 50)"
    echo ""
    echo "Examples:"
    echo "  $0 dev          # Show last 50 lines for dev"
    echo "  $0 live 100     # Show last 100 lines for live"
    echo "  $0 staging -f   # Follow staging logs (live tail)"
    exit 1
}

error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

info() {
    echo -e "${BLUE}$1${NC}"
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

# Check if systemd service exists
if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    error "Service $SERVICE_NAME is not installed"
    exit 1
fi

# Check if user wants to follow logs
if [[ "$LINES" == "-f" || "$LINES" == "--follow" ]]; then
    info "Following logs for $SERVICE_NAME (Ctrl+C to stop)..."
    sudo journalctl -u "$SERVICE_NAME" -f
else
    info "Showing last $LINES lines for $SERVICE_NAME..."
    sudo journalctl -u "$SERVICE_NAME" -n "$LINES" --no-pager
fi
