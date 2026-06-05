#!/bin/bash
# InternMailer Service Installation Script
# Supports both Linux (systemd) and macOS (launchd)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo -e "${BLUE}Detected: Linux${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo -e "${BLUE}Detected: macOS${NC}"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

# Functions
install_systemd() {
    echo -e "${YELLOW}Installing systemd service...${NC}"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Please run with sudo for systemd installation${NC}"
        exit 1
    fi
    
    USER=${SUDO_USER:-$USER}
    SERVICE_NAME="internmailer@${USER}.service"
    SERVICE_FILE="/etc/systemd/system/internmailer@.service"
    
    # Copy service file
    cp "$SCRIPT_DIR/internmailer.service" "$SERVICE_FILE"
    
    # Update paths in service file
    sed -i "s|/home/%I|/home/$USER|g" "$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    echo -e "${GREEN}Systemd service installed successfully!${NC}"
    echo ""
    echo "Commands:"
    echo "  Start:   sudo systemctl start $SERVICE_NAME"
    echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
    echo "  Status:  sudo systemctl status $SERVICE_NAME"
    echo "  Enable:  sudo systemctl enable $SERVICE_NAME"
    echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
}

install_launchd() {
    echo -e "${YELLOW}Installing launchd service...${NC}"
    
    PLIST_NAME="com.internmailer.daemon.plist"
    PLIST_SOURCE="$SCRIPT_DIR/$PLIST_NAME"
    PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"
    
    # Create LaunchAgents directory if needed
    mkdir -p "$HOME/Library/LaunchAgents"
    
    # Copy and update plist file
    cp "$PLIST_SOURCE" "$PLIST_DEST"
    
    # Replace paths
    sed -i '' "s|REPLACE_WITH_PATH|$PROJECT_DIR|g" "$PLIST_DEST"
    
    echo -e "${GREEN}Launchd service installed successfully!${NC}"
    echo ""
    echo "Commands:"
    echo "  Start:   launchctl load $PLIST_DEST"
    echo "  Stop:    launchctl unload $PLIST_DEST"
    echo "  Status:  launchctl list | grep internmailer"
    echo "  Logs:    tail -f $PROJECT_DIR/logs/daemon.stdout.log"
}

uninstall_systemd() {
    echo -e "${YELLOW}Uninstalling systemd service...${NC}"
    
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Please run with sudo${NC}"
        exit 1
    fi
    
    USER=${SUDO_USER:-$USER}
    SERVICE_NAME="internmailer@${USER}.service"
    SERVICE_FILE="/etc/systemd/system/internmailer@.service"
    
    # Stop if running
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    
    # Remove service file
    rm -f "$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    echo -e "${GREEN}Systemd service uninstalled!${NC}"
}

uninstall_launchd() {
    echo -e "${YELLOW}Uninstalling launchd service...${NC}"
    
    PLIST_NAME="com.internmailer.daemon.plist"
    PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"
    
    # Unload if loaded
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    
    # Remove plist file
    rm -f "$PLIST_DEST"
    
    echo -e "${GREEN}Launchd service uninstalled!${NC}"
}

show_status() {
    echo -e "${BLUE}Checking service status...${NC}"
    
    if [ "$OS" == "linux" ]; then
        USER=${SUDO_USER:-$USER}
        SERVICE_NAME="internmailer@${USER}.service"
        systemctl status "$SERVICE_NAME" --no-pager || true
    else
        launchctl list | grep internmailer || echo "Service not loaded"
        
        # Check log files
        echo ""
        echo "Recent log entries:"
        if [ -f "$PROJECT_DIR/logs/daemon.stdout.log" ]; then
            tail -20 "$PROJECT_DIR/logs/daemon.stdout.log"
        else
            echo "No log file found"
        fi
    fi
}

show_help() {
    echo "InternMailer Service Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  install     Install the service (requires sudo on Linux)"
    echo "  uninstall   Remove the service (requires sudo on Linux)"
    echo "  status      Check service status"
    echo "  start       Start the service"
    echo "  stop        Stop the service"
    echo "  restart     Restart the service"
    echo "  logs        Show service logs"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 install"
    echo "  $0 start"
    echo "  $0 logs"
}

# Main logic
COMMAND=${1:-help}

case "$COMMAND" in
    install)
        if [ "$OS" == "linux" ]; then
            install_systemd
        else
            install_launchd
        fi
        ;;
    
    uninstall)
        if [ "$OS" == "linux" ]; then
            uninstall_systemd
        else
            uninstall_launchd
        fi
        ;;
    
    status)
        show_status
        ;;
    
    start)
        if [ "$OS" == "linux" ]; then
            USER=${SUDO_USER:-$USER}
            sudo systemctl start "internmailer@${USER}.service"
        else
            launchctl load "$HOME/Library/LaunchAgents/com.internmailer.daemon.plist"
        fi
        echo -e "${GREEN}Service started${NC}"
        ;;
    
    stop)
        if [ "$OS" == "linux" ]; then
            USER=${SUDO_USER:-$USER}
            sudo systemctl stop "internmailer@${USER}.service"
        else
            launchctl unload "$HOME/Library/LaunchAgents/com.internmailer.daemon.plist" 2>/dev/null || true
        fi
        echo -e "${YELLOW}Service stopped${NC}"
        ;;
    
    restart)
        if [ "$OS" == "linux" ]; then
            USER=${SUDO_USER:-$USER}
            sudo systemctl restart "internmailer@${USER}.service"
        else
            launchctl unload "$HOME/Library/LaunchAgents/com.internmailer.daemon.plist" 2>/dev/null || true
            sleep 1
            launchctl load "$HOME/Library/LaunchAgents/com.internmailer.daemon.plist"
        fi
        echo -e "${GREEN}Service restarted${NC}"
        ;;
    
    logs)
        if [ "$OS" == "linux" ]; then
            USER=${SUDO_USER:-$USER}
            sudo journalctl -u "internmailer@${USER}.service" -f
        else
            tail -f "$PROJECT_DIR/logs/daemon.stdout.log" "$PROJECT_DIR/logs/daemon.stderr.log"
        fi
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac
