#!/bin/bash

# Simple VPS Setup Script for Class Scheduler (No Docker)
# Run this script on your GCP VPS to prepare for lightweight deployment

set -e

echo "Setting up VPS for lightweight Class Scheduler deployment..."

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip git

# Create 4GB swap file for memory-intensive OR-Tools operations
echo "Creating 4GB swap file..."
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize swap settings for better performance
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# Apply sysctl settings
sudo sysctl -p

# Verify swap is active
echo "Swap status:"
sudo swapon --show
free -h

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
echo "System configuration:"
echo "- 4GB swap file created for memory-intensive operations"
echo "- Swap settings optimized (swappiness=10, cache_pressure=50)"
echo "- FastAPI app will run directly on port 80 without Docker"
echo "- Service will auto-start on boot and restart if it crashes"
echo ""
echo "Memory status:"
free -h
echo ""
echo "Commands to manage the service:"
echo "  sudo systemctl start class-scheduler    # Start the service"
echo "  sudo systemctl stop class-scheduler     # Stop the service"
echo "  sudo systemctl status class-scheduler   # Check status"
echo "  sudo journalctl -u class-scheduler -f   # View logs"
echo ""
echo "Commands to monitor memory usage:"
echo "  free -h                                 # Check memory/swap usage"
echo "  htop                                    # Interactive process monitor"
echo "  sudo swapon --show                      # Show swap devices"