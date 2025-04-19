#!/bin/bash
# filepath: c:\Code Repository\Media_management\install_service.sh

# Media Management Application Service Installer
# This script installs the Media Management application as a systemd service on Ubuntu

set -e  # Exit on error

# Configuration variables - modify these as needed
APP_NAME="media_management"
APP_USER="mediauser"
APP_GROUP="mediauser"
INSTALL_DIR="/opt/media_management"
VENV_DIR="/opt/media_management/venv"
SERVICE_NAME="media_management"
APP_PORT=5000
LOG_DIR="/var/log/media_management"
CONFIG_DIR="/etc/media_management"
REPOSITORY="https://github.com/zy538324/Media_management.git"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if script is run as root
if [ "$EUID" -ne 0 ]
  then echo -e "${RED}Please run as root or with sudo${NC}"
  exit 1
fi

echo -e "${GREEN}Beginning Media Management Application installation...${NC}"

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv sqlite3 git curl

# Create application user
echo -e "${YELLOW}Creating application user...${NC}"
if ! id -u $APP_USER >/dev/null 2>&1; then
    useradd -m -s /bin/bash $APP_USER
    echo "User $APP_USER created"
else
    echo "User $APP_USER already exists"
fi

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p $INSTALL_DIR $LOG_DIR $CONFIG_DIR
chown -R $APP_USER:$APP_GROUP $INSTALL_DIR $LOG_DIR $CONFIG_DIR

# Download application from GitHub
echo -e "${YELLOW}Downloading application from GitHub repository...${NC}"
if [ -d "$INSTALL_DIR/.git" ]; then
    # Repository already exists, update it
    cd $INSTALL_DIR
    sudo -u $APP_USER git pull origin main || sudo -u $APP_USER git pull origin master
else
    # Fresh clone of the repository
    rm -rf $INSTALL_DIR/*
    sudo -u $APP_USER git clone $REPOSITORY $INSTALL_DIR
fi

# Check if download was successful
if [ ! -d "$INSTALL_DIR/app" ]; then
    echo -e "${RED}Failed to download or repository structure not as expected.${NC}"
    echo -e "${YELLOW}Attempting direct download via archive...${NC}"
    
    # Backup plan: try downloading the ZIP archive
    TMP_DIR=$(mktemp -d)
    curl -L -o $TMP_DIR/media_management.zip https://github.com/zy538324/Media_management/archive/refs/heads/main.zip || \
    curl -L -o $TMP_DIR/media_management.zip https://github.com/zy538324/Media_management/archive/refs/heads/master.zip
    
    # Extract the ZIP file
    unzip -q $TMP_DIR/media_management.zip -d $TMP_DIR
    # Find the directory name (might be Media_management-main or Media_management-master)
    EXTRACTED_DIR=$(find $TMP_DIR -maxdepth 1 -type d -name "Media_management*" | head -n 1)
    
    if [ -n "$EXTRACTED_DIR" ]; then
        cp -r $EXTRACTED_DIR/* $INSTALL_DIR/
        chown -R $APP_USER:$APP_GROUP $INSTALL_DIR
    else
        echo -e "${RED}Failed to download repository. Please check the repository URL and try again.${NC}"
        exit 1
    fi
    
    # Clean up temp directory
    rm -rf $TMP_DIR
fi

# Set up Python virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
sudo -u $APP_USER python3 -m venv $VENV_DIR
sudo -u $APP_USER $VENV_DIR/bin/pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    sudo -u $APP_USER $VENV_DIR/bin/pip install -r $INSTALL_DIR/requirements.txt
else
    # Create a basic requirements file if it doesn't exist
    echo -e "${YELLOW}Creating basic requirements.txt file...${NC}"
    cat > $INSTALL_DIR/requirements.txt << EOF
flask>=2.0.0
flask-sqlalchemy>=2.5.0
flask-login>=0.5.0
werkzeug>=2.0.0
pyyaml>=6.0
requests>=2.25.0
gunicorn>=20.1.0
EOF
    sudo -u $APP_USER $VENV_DIR/bin/pip install -r $INSTALL_DIR/requirements.txt
fi

# Copy configuration file
if [ -f "$INSTALL_DIR/config.yaml" ]; then
    echo -e "${YELLOW}Copying configuration file...${NC}"
    cp $INSTALL_DIR/config.yaml $CONFIG_DIR/config.yaml
    chown $APP_USER:$APP_GROUP $CONFIG_DIR/config.yaml
    chmod 600 $CONFIG_DIR/config.yaml  # Restrict permissions for security
    
    # Create a symlink to the config in the app directory
    ln -sf $CONFIG_DIR/config.yaml $INSTALL_DIR/config.yaml
else
    echo -e "${RED}Configuration file not found. Creating a sample config...${NC}"
    cat > $CONFIG_DIR/config.yaml << EOF
Database:
  path: media_management.db
  track_modifications: false
Jackett:
  api_key: j5bmf5mf3m83yx12tx3wbxk9jarux2wd
  categories:
    Movies: '2000'
    Music: '3000'
    TV: '5000'
  server_url: http://10.252.0.15:9117/
Jellyfin:
  api_key: d60eb1a6c2594fa7a47924c1b37cf81c
  server_url: http://10.252.0.155:8096
Secret_key: ZV}1Ux/!LfbACbIR@0:F
Spotify:
  client_id: b3fb8ab712a9449e94e70c77d5ba5426
  client_secret: f6e5c9c048c6453482d3cef2fd74b7ae
TMDb:
  api_key: 84147d5f9aa77e54c45cd5b6ceabd0fc
qBittorrent:
  host: http://10.252.0.15:8080
  password: =hX-z`PB_'4BiY'R+E~\
  username: admin
EOF
    chown $APP_USER:$APP_GROUP $CONFIG_DIR/config.yaml
    chmod 600 $CONFIG_DIR/config.yaml
    ln -sf $CONFIG_DIR/config.yaml $INSTALL_DIR/config.yaml
    echo -e "${YELLOW}Generated sample config file at $CONFIG_DIR/config.yaml${NC}"
    echo -e "${YELLOW}Please update it with your actual API keys and service URLs${NC}"
fi

# Initialize the SQLite database
echo -e "${YELLOW}Initializing database...${NC}"
if [ -f "$INSTALL_DIR/init_db.py" ]; then
    cd $INSTALL_DIR
    sudo -u $APP_USER $VENV_DIR/bin/python init_db.py
else
    echo -e "${RED}Database initialization script not found. Creating a basic one...${NC}"
    
    # Create a basic database initialization script
    cat > $INSTALL_DIR/init_db.py << EOF
import sqlite3
import os
from config import Config

def init_db():
    """Initialize the SQLite database with schema"""
    config = Config()
    db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Connect to SQLite database (will create if not exists)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create basic tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        profile_text TEXT,
        profile_picture TEXT,
        role TEXT DEFAULT 'User',
        status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        last_activity TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

if __name__ == "__main__":
    init_db()
EOF
    
    chown $APP_USER:$APP_GROUP $INSTALL_DIR/init_db.py
    cd $INSTALL_DIR
    sudo -u $APP_USER $VENV_DIR/bin/python init_db.py
fi

# Create a WSGI entry point if it doesn't exist
if [ ! -f "$INSTALL_DIR/wsgi.py" ]; then
    echo -e "${YELLOW}Creating WSGI entry point...${NC}"
    cat > $INSTALL_DIR/wsgi.py << EOF
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=$APP_PORT)
EOF

    chown $APP_USER:$APP_GROUP $INSTALL_DIR/wsgi.py
fi

# Create systemd service file
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Media Management Application
After=network.target

[Service]
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${VENV_DIR}/bin"
ExecStart=${VENV_DIR}/bin/gunicorn --workers 3 --bind 0.0.0.0:${APP_PORT} wsgi:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

# Create a log rotation configuration
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
        systemctl reload ${SERVICE_NAME}.service
    endscript
}
EOF

# Enable and start the service
echo -e "${YELLOW}Enabling and starting the service...${NC}"
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl start ${SERVICE_NAME}.service

# Open firewall port if UFW is enabled
if command -v ufw > /dev/null; then
    echo -e "${YELLOW}Configuring firewall...${NC}"
    ufw allow ${APP_PORT}/tcp
    echo "Allowed port ${APP_PORT} through the firewall"
fi

# Create a convenient management script
echo -e "${YELLOW}Creating management script...${NC}"
cat > /usr/local/bin/media_management << EOF
#!/bin/bash
case "\$1" in
    start)
        systemctl start ${SERVICE_NAME}
        ;;
    stop)
        systemctl stop ${SERVICE_NAME}
        ;;
    restart)
        systemctl restart ${SERVICE_NAME}
        ;;
    status)
        systemctl status ${SERVICE_NAME}
        ;;
    logs)
        journalctl -u ${SERVICE_NAME} -f
        ;;
    update)
        cd ${INSTALL_DIR}
        sudo -u ${APP_USER} git pull
        sudo -u ${APP_USER} ${VENV_DIR}/bin/pip install -r requirements.txt
        systemctl restart ${SERVICE_NAME}
        echo "Updated and restarted ${SERVICE_NAME}"
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart|status|logs|update}"
        exit 1
esac
exit 0
EOF
chmod +x /usr/local/bin/media_management

# Display status information
echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}Service status:${NC}"
systemctl status ${SERVICE_NAME}.service --no-pager

echo -e "${GREEN}You can access your application at: http://$(hostname -I | cut -d' ' -f1):${APP_PORT}${NC}"
echo -e "${YELLOW}To manage the service:${NC}"
echo -e "  ${GREEN}media_management start${NC} - Start the service"
echo -e "  ${GREEN}media_management stop${NC} - Stop the service"
echo -e "  ${GREEN}media_management restart${NC} - Restart the service"
echo -e "  ${GREEN}media_management status${NC} - Check service status"
echo -e "  ${GREEN}media_management logs${NC} - View live logs"
echo -e "  ${GREEN}media_management update${NC} - Update from GitHub and restart"

echo -e "\n${GREEN}Done! Installation completed successfully.${NC}"
