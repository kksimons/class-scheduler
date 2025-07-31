#!/bin/bash

# Add swap space to VPS for memory-intensive operations
# Run this script if you need to add swap space manually

set -e

SWAP_SIZE=${1:-4G}  # Default to 4GB, can be overridden with argument

echo "Adding ${SWAP_SIZE} swap space..."

# Check if swap file already exists
if [ -f /swapfile ]; then
    echo "Swap file already exists. Current swap status:"
    sudo swapon --show
    free -h
    exit 0
fi

# Create swap file
echo "Creating ${SWAP_SIZE} swap file..."
sudo fallocate -l ${SWAP_SIZE} /swapfile

# Set correct permissions
sudo chmod 600 /swapfile

# Set up swap space
sudo mkswap /swapfile

# Enable swap
sudo swapon /swapfile

# Make swap permanent
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Optimize swap settings
if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
fi

if ! grep -q 'vm.vfs_cache_pressure' /etc/sysctl.conf; then
    echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
fi

# Apply settings
sudo sysctl -p

echo "Swap space added successfully!"
echo ""
echo "Current memory status:"
free -h
echo ""
echo "Swap devices:"
sudo swapon --show
echo ""
echo "Swap settings:"
echo "- swappiness=10 (low tendency to swap, prefer RAM)"
echo "- vfs_cache_pressure=50 (balanced cache pressure)"