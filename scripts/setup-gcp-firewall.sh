#!/bin/bash

# Script to configure GCP firewall rules for GitHub Actions deployment
# Run this script on your GCP VPS or from gcloud CLI

echo "Setting up GCP firewall rules for GitHub Actions..."

# GitHub Actions IP ranges (these change periodically, so check GitHub's meta API)
# You can get current ranges from: https://api.github.com/meta

# Create firewall rule for GitHub Actions runners
gcloud compute firewall-rules create allow-github-actions \
    --description="Allow GitHub Actions runners to access deployment endpoints" \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:22,tcp:80,tcp:443 \
    --source-ranges=\
4.175.114.64/26,\
20.87.225.212/30,\
20.119.28.4/30,\
20.200.245.240/29,\
20.201.28.144/28,\
20.205.243.160/28,\
20.207.73.82/30,\
20.233.54.53/32,\
20.233.83.145/32,\
20.248.137.48/28,\
20.29.134.17/32,\
20.87.245.0/26,\
4.208.26.196/30,\
4.231.180.112/28 \
    --target-tags=github-actions-deployment

echo "Firewall rule created. Make sure your VM instance has the 'github-actions-deployment' tag."
echo ""
echo "To add the tag to your VM instance, run:"
echo "gcloud compute instances add-tags YOUR_INSTANCE_NAME --tags=github-actions-deployment --zone=YOUR_ZONE"
echo ""
echo "Also create a rule for HTTP/HTTPS traffic:"

# Allow HTTP and HTTPS traffic
gcloud compute firewall-rules create allow-http-https \
    --description="Allow HTTP and HTTPS traffic" \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:80,tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=http-server,https-server

echo "HTTP/HTTPS firewall rule created."
echo ""
echo "Make sure to also tag your instance with 'http-server' and 'https-server' tags:"
echo "gcloud compute instances add-tags YOUR_INSTANCE_NAME --tags=http-server,https-server --zone=YOUR_ZONE"