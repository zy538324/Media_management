#!/bin/bash
# Media Management Application Service Installer for Linux
# This script installs the application as a systemd service on Ubuntu/Debian-based systems

set -e  # Exit on error

# Configuration variables
APP_NAME="media_management"
APP_USER="mediauser"
APP_GROUP="mediauser"
INSTALL_DIR="/var/www/media_manager"
VENV_DIR="/var/www/media_manager/venv"
SERVICE_NAME="media-management"
APP_PORT=5000
LOG_DIR="/var/www/media_manager/logs"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root or with sudo"
    exit 1
fi

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Media Management Application - Service Installer${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

# Install system dependencies
print_info "Installing system dependencies..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv libpq-dev build-essential curl > /dev/null 2>&1
print_success "System dependencies installed"

# Create application user
print_info "Creating application user..."
if ! id -u $APP_USER >/dev/null 2>&1; then
    useradd -m -s /bin/bash $APP_USER
    print_success "User $APP_USER created"
else
    print_warning "User $APP_USER already exists"
fi

# Create required directories
print_info "Creating application directories..."
mkdir -p $INSTALL_DIR $LOG_DIR
print_success "Directories created"

# Copy application files from current directory
print_info "Copying application files from $SCRIPT_DIR..."
if [ ! -d "$SCRIPT_DIR/app" ]; then
    print_error "Application directory structure not found in $SCRIPT_DIR"
    print_error "Please run this script from the Media Management project directory"
    exit 1
fi

# Copy files excluding unnecessary ones
rsync -av --exclude='venv' \
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.git' \
          --exclude='logs/*' \
          --exclude='instance/*' \
          --exclude='*.log' \
          --exclude='docs' \
          --exclude='windows_setup.ps1' \
          --exclude='service_wrapper.py' \
          --exclude='setup.py' \
          --exclude='user.py' \
          --exclude='schema.sql' \
          --exclude='sql.sql' \
          --exclude='*.tar.gz' \
          "$SCRIPT_DIR/" "$INSTALL_DIR/"

# Ensure logs directory exists
mkdir -p $INSTALL_DIR/logs

# Set proper ownership
chown -R $APP_USER:$APP_GROUP $INSTALL_DIR
print_success "Application files copied"

# Set up Python virtual environment
print_info "Setting up Python virtual environment..."
sudo -u $APP_USER python3 -m venv $VENV_DIR
sudo -u $APP_USER $VENV_DIR/bin/pip install --upgrade pip -q
print_success "Virtual environment created"

# Install Python dependencies
print_info "Installing Python dependencies..."
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    sudo -u $APP_USER $VENV_DIR/bin/pip install -r $INSTALL_DIR/requirements.txt -q
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Verify config.yaml exists
if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
    print_error "config.yaml not found in $INSTALL_DIR"
    print_error "Please ensure config.yaml exists before running this script"
    exit 1
fi
print_success "Configuration file verified"

# Create systemd service file
print_info "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Media Management Web Application
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

# Use Gunicorn for production
ExecStart=${VENV_DIR}/bin/gunicorn \
    --workers 2 \
    --threads 4 \
    --bind 0.0.0.0:${APP_PORT} \
    --timeout 300 \
    --access-logfile ${LOG_DIR}/access.log \
    --error-logfile ${LOG_DIR}/error.log \
    --log-level info \
    --capture-output \
    "app:create_app()"

# Restart policy
Restart=always
RestartSec=10
StartLimitBurst=5
StartLimitInterval=60

# Logging
StandardOutput=append:${LOG_DIR}/service.log
StandardError=append:${LOG_DIR}/service_error.log

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${INSTALL_DIR}/logs ${INSTALL_DIR}/instance
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Resource limits
LimitNOFILE=65535
LimitNPROC=512

[Install]
WantedBy=multi-user.target
EOF
print_success "Systemd service file created"

# Create log rotation configuration
print_info "Configuring log rotation..."
cat > /etc/logrotate.d/${SERVICE_NAME} << EOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ${APP_USER} ${APP_GROUP}
    sharedscripts
    postrotate
        systemctl reload ${SERVICE_NAME}.service > /dev/null 2>&1 || true
    endscript
}
EOF
print_success "Log rotation configured"

# Create management script
print_info "Creating management script..."
cat > /usr/local/bin/media-mgmt << 'MGMT_SCRIPT'
#!/bin/bash

SERVICE_NAME="media-management"
INSTALL_DIR="/opt/media_management"
LOG_DIR="/opt/media_management/logs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

case "$1" in
    start)
        echo -e "${BLUE}Starting ${SERVICE_NAME}...${NC}"
        systemctl start ${SERVICE_NAME}
        echo -e "${GREEN}✓ Service started${NC}"
        ;;
    stop)
        echo -e "${YELLOW}Stopping ${SERVICE_NAME}...${NC}"
        systemctl stop ${SERVICE_NAME}
        echo -e "${GREEN}✓ Service stopped${NC}"
        ;;
    restart)
        echo -e "${YELLOW}Restarting ${SERVICE_NAME}...${NC}"
        systemctl restart ${SERVICE_NAME}
        echo -e "${GREEN}✓ Service restarted${NC}"
        ;;
    reload)
        echo -e "${BLUE}Reloading ${SERVICE_NAME} configuration...${NC}"
        systemctl reload ${SERVICE_NAME}
        echo -e "${GREEN}✓ Configuration reloaded${NC}"
        ;;
    status)
        systemctl status ${SERVICE_NAME} --no-pager
        ;;
    logs)
        if [ -n "$2" ]; then
            journalctl -u ${SERVICE_NAME} -n "$2" --no-pager
        else
            journalctl -u ${SERVICE_NAME} -f
        fi
        ;;
    app-logs)
        tail -f ${LOG_DIR}/service.log
        ;;
    error-logs)
        tail -f ${LOG_DIR}/service_error.log
        ;;
    access-logs)
        tail -f ${LOG_DIR}/access.log
        ;;
    enable)
        echo -e "${BLUE}Enabling ${SERVICE_NAME} to start on boot...${NC}"
        systemctl enable ${SERVICE_NAME}
        echo -e "${GREEN}✓ Service enabled${NC}"
        ;;
    disable)
        echo -e "${YELLOW}Disabling ${SERVICE_NAME} from starting on boot...${NC}"
        systemctl disable ${SERVICE_NAME}
        echo -e "${GREEN}✓ Service disabled${NC}"
        ;;
    test)
        echo -e "${BLUE}Testing configuration...${NC}"
        cd ${INSTALL_DIR}
        sudo -u mediauser ${INSTALL_DIR}/venv/bin/python -c "from app import create_app; app = create_app(); print('✓ Configuration OK')"
        ;;
    daemon-reload)
        echo -e "${BLUE}Reloading systemd daemon...${NC}"
        systemctl daemon-reload
        echo -e "${GREEN}✓ Daemon reloaded${NC}"
        ;;
    *)
        echo -e "${BLUE}Media Management Service Manager${NC}"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Service Control:"
        echo "  start          - Start the service"
        echo "  stop           - Stop the service"
        echo "  restart        - Restart the service"
        echo "  reload         - Reload configuration without stopping"
        echo "  status         - Show service status"
        echo "  enable         - Enable service on boot"
        echo "  disable        - Disable service on boot"
        echo ""
        echo "Logging:"
        echo "  logs [n]       - Show system logs (optionally last n lines)"
        echo "  app-logs       - Show application logs"
        echo "  error-logs     - Show error logs"
        echo "  access-logs    - Show access logs"
        echo ""
        echo "System:"
        echo "  test           - Test configuration"
        echo "  daemon-reload  - Reload systemd daemon"
        exit 1
        ;;
esac
exit 0
MGMT_SCRIPT

chmod +x /usr/local/bin/media-mgmt
print_success "Management script created at /usr/local/bin/media-mgmt"

# Configure firewall if UFW is active
if command -v ufw > /dev/null && ufw status | grep -q "Status: active"; then
    print_info "Configuring firewall..."
    ufw allow ${APP_PORT}/tcp > /dev/null 2>&1
    print_success "Firewall configured (port ${APP_PORT} allowed)"
else
    print_warning "UFW not active, skipping firewall configuration"
fi

# Enable and start the service
print_info "Enabling and starting service..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service > /dev/null 2>&1
systemctl start ${SERVICE_NAME}.service

# Wait a moment for service to start
sleep 3

# Check if service started successfully
if systemctl is-active --quiet ${SERVICE_NAME}.service; then
    print_success "Service started successfully!"
else
    print_error "Service failed to start. Check logs with: media-mgmt logs"
    exit 1
fi

# Display completion message
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Installation Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}Service Information:${NC}"
echo -e "  Name:          ${SERVICE_NAME}"
echo -e "  Status:        $(systemctl is-active ${SERVICE_NAME})"
echo -e "  Install Dir:   ${INSTALL_DIR}"
echo -e "  Log Dir:       ${LOG_DIR}"
echo -e "  Port:          ${APP_PORT}"
echo -e ""
echo -e "${GREEN}Access your application at:${NC}"
echo -e "  ${BLUE}http://${IP_ADDR}:${APP_PORT}${NC}"
echo -e "  ${BLUE}http://localhost:${APP_PORT}${NC}"
echo -e ""
echo -e "${YELLOW}Management Commands:${NC}"
echo -e "  ${GREEN}media-mgmt start${NC}          - Start the service"
echo -e "  ${GREEN}media-mgmt stop${NC}           - Stop the service"
echo -e "  ${GREEN}media-mgmt restart${NC}        - Restart the service"
echo -e "  ${GREEN}media-mgmt reload${NC}         - Reload without stopping"
echo -e "  ${GREEN}media-mgmt status${NC}         - Check service status"
echo -e "  ${GREEN}media-mgmt logs${NC}           - View live system logs"
echo -e "  ${GREEN}media-mgmt app-logs${NC}       - View application logs"
echo -e "  ${GREEN}media-mgmt test${NC}           - Test configuration"
echo -e "  ${GREEN}media-mgmt daemon-reload${NC}  - Reload systemd daemon"
echo -e ""
echo -e "${BLUE}Current Status:${NC}"
systemctl status ${SERVICE_NAME}.service --no-pager -l
echo -e "\n${GREEN}Installation completed successfully!${NC}\n"
