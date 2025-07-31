#!/bin/bash

# Simple VPS Setup Script for Class Scheduler (No Docker)
# Run this script on your GCP VPS to prepare for lightweight deployment

set -e

echo "Setting up VPS for lightweight Class Scheduler deployment..."

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip git

# Install required Python packages globally (for systemd service)
sudo python3 -m pip install fastapi uvicorn pydantic

# Create app directory
mkdir -p /home/kksimons/class-scheduler

# Create systemd service file
sudo tee /etc/systemd/system/class-scheduler.service > /dev/null <<EOF
[Unit]
Description=Class Scheduler FastAPI Application
After=network.target

[Service]
Type=simple
User=kksimons
WorkingDirectory=/home/kksimons/class-scheduler/app
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 80
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable class-scheduler.service

# Set up basic firewall with ufw
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp

echo "Simple VPS setup complete!"
echo ""
echo "The FastAPI app will run directly on port 80 without Docker."
echo "Service will auto-start on boot and restart if it crashes."
echo ""
echo "Commands to manage the service:"
echo "  sudo systemctl start class-scheduler    # Start the service"
echo "  sudo systemctl stop class-scheduler     # Stop the service"
echo "  sudo systemctl status class-scheduler   # Check status"
echo "  sudo journalctl -u class-scheduler -f   # View logs"