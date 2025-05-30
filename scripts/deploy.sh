#!/bin/bash

# Auto-deployment script for ProjectIM
# This script is triggered by GitHub Actions on push to main/master

set -e  # Exit on error

echo "Starting deployment of ProjectIM..."

# Configuration
DEPLOY_DIR="/opt/projectim"
SERVICE_NAME="projectim"
BACKUP_DIR="/opt/projectim-backups"

# Create backup of current deployment
if [ -d "$DEPLOY_DIR" ]; then
    echo "Creating backup of current deployment..."
    mkdir -p "$BACKUP_DIR"
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
    cp -r "$DEPLOY_DIR" "$BACKUP_DIR/$BACKUP_NAME"
    echo "Backup created: $BACKUP_DIR/$BACKUP_NAME"
fi

# Create deployment directory if it doesn't exist
mkdir -p "$DEPLOY_DIR"

# Copy project files
echo "Copying project files..."
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='imenv' ./ "$DEPLOY_DIR/"

# Install/update dependencies
echo "Installing dependencies..."
cd "$DEPLOY_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file if it exists in deployment location
if [ -f "/opt/projectim-config/.env" ]; then
    cp "/opt/projectim-config/.env" "$DEPLOY_DIR/.env"
fi

# Create systemd service if it doesn't exist
if [ ! -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    echo "Creating systemd service..."
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOL
[Unit]
Description=ProjectIM - Claude Self-Improvement System
After=network.target

[Service]
Type=simple
User=projectim
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin"
ExecStart=$DEPLOY_DIR/venv/bin/python $DEPLOY_DIR/claude_cli.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL
fi

# Reload systemd and restart service
echo "Restarting service..."
systemctl daemon-reload
systemctl restart $SERVICE_NAME
systemctl enable $SERVICE_NAME

# Check service status
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "Deployment successful! Service is running."
else
    echo "Warning: Service is not running. Check logs with: journalctl -u $SERVICE_NAME"
fi

# Clean up old backups (keep last 5)
echo "Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t | tail -n +6 | xargs -r rm -rf

echo "Deployment complete!"