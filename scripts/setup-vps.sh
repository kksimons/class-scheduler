#!/bin/bash

# VPS Setup Script for Class Scheduler Deployment
# Run this script on your GCP VPS (35.197.99.197) to prepare for deployment

set -e

echo "Setting up VPS for Class Scheduler deployment..."

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Git
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    sudo apt install -y git
fi

# Create deployment directory
sudo mkdir -p /opt/class-scheduler
sudo chown $USER:$USER /opt/class-scheduler

# Clone the repository (if not already cloned)
if [ ! -d "/opt/class-scheduler/.git" ]; then
    echo "Cloning repository..."
    git clone https://github.com/kksimons/class-scheduler.git /opt/class-scheduler
else
    echo "Repository already exists, pulling latest changes..."
    cd /opt/class-scheduler
    git pull origin main || git pull origin master
fi

# Set up log rotation for nginx logs
sudo tee /etc/logrotate.d/class-scheduler-nginx > /dev/null <<EOF
/opt/class-scheduler/logs/nginx/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose -f /opt/class-scheduler/docker-compose.yml exec nginx nginx -s reload
    endscript
}
EOF

# Create systemd service for auto-start
sudo tee /etc/systemd/system/class-scheduler.service > /dev/null <<EOF
[Unit]
Description=Class Scheduler Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/class-scheduler
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable class-scheduler.service

# Set up basic firewall with ufw
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

echo "VPS setup complete!"
echo ""
echo "Next steps:"
echo "1. Add your SSH public key to ~/.ssh/authorized_keys"
echo "2. Configure GitHub secrets with:"
echo "   - VPS_HOST: 35.197.99.197"
echo "   - VPS_USERNAME: $USER"
echo "   - VPS_SSH_KEY: (your private SSH key)"
echo "   - DOCKER_USERNAME: (your Docker Hub username)"
echo "   - DOCKER_PASSWORD: (your Docker Hub password/token)"
echo "3. Run the GCP firewall setup script"
echo "4. Test deployment by pushing to your repository"