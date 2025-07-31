# Deployment Guide

This guide covers deploying the Class Scheduler FastAPI application to a GCP VPS with automated GitHub Actions deployment.

## Architecture

- **FastAPI Application**: Runs in Docker container on port 5000
- **Nginx Reverse Proxy**: Handles requests, rate limiting, and security headers
- **GitHub Actions**: Automated deployment pipeline
- **GCP VPS**: Target deployment server (35.197.99.197)

## Security Features

### Nginx Security Configuration
- Rate limiting: 10 requests/minute for API endpoints, 30 requests/minute for general endpoints
- Security headers (X-Frame-Options, CSP, etc.)
- Connection limits (10 connections per IP)
- Request size limits (1MB max)
- Hidden nginx version
- Blocked common attack patterns

### Network Security
- GCP firewall rules restricting access to GitHub Actions IP ranges
- UFW firewall on VPS
- Docker network isolation

## Setup Instructions

### 1. VPS Setup

SSH into your GCP VPS (35.197.99.197) and run:

```bash
# Download and run the VPS setup script
curl -fsSL https://raw.githubusercontent.com/kksimons/class-scheduler/main/scripts/setup-vps.sh | bash

# Or clone the repo and run locally
git clone https://github.com/kksimons/class-scheduler.git
cd class-scheduler
./scripts/setup-vps.sh
```

### 2. GCP Firewall Configuration

Configure firewall rules to allow GitHub Actions access:

```bash
# Run the firewall setup script
./scripts/setup-gcp-firewall.sh

# Tag your VM instance
gcloud compute instances add-tags YOUR_INSTANCE_NAME \
  --tags=github-actions-deployment,http-server,https-server \
  --zone=YOUR_ZONE
```

### 3. GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `VPS_HOST` | VPS IP address | `35.197.99.197` |
| `VPS_USERNAME` | SSH username | `your-username` |
| `VPS_SSH_KEY` | Private SSH key | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `DOCKER_USERNAME` | Docker Hub username | `your-dockerhub-username` |
| `DOCKER_PASSWORD` | Docker Hub password/token | `your-token` |

### 4. SSH Key Setup

Generate SSH keys for deployment:

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/github_actions.pub user@35.197.99.197

# Add private key to GitHub secrets as VPS_SSH_KEY
cat ~/.ssh/github_actions
```

## Deployment Process

The deployment is triggered automatically on:
- Push to `main` or `master` branch
- Pull requests to `main` or `master` branch

### Deployment Steps:
1. **Build**: Docker image is built and pushed to Docker Hub
2. **Deploy**: SSH into VPS and update the running containers
3. **Health Check**: Verify the application is running correctly

## API Endpoints

- `GET /` - Health check endpoint
- `POST /api/v1/class-scheduler` - Generate schedule (basic algorithm)
- `POST /api/v1/class-scheduler-optimal` - Generate schedule (optimal algorithm)

## Rate Limiting

- **API endpoints** (`/api/*`): 10 requests/minute per IP, burst of 5
- **General endpoints**: 30 requests/minute per IP, burst of 10
- **Connection limit**: 10 concurrent connections per IP

## Monitoring

### Logs
- Nginx logs: Available in Docker volume `nginx-logs`
- Application logs: `docker-compose logs app`
- System logs: `journalctl -u class-scheduler.service`

### Health Checks
- Application health: `curl http://35.197.99.197/health`
- Docker health checks run every 30 seconds

## Troubleshooting

### Common Issues

1. **Deployment fails with SSH connection error**
   - Verify SSH key is correctly added to GitHub secrets
   - Check VPS firewall allows GitHub Actions IP ranges

2. **Rate limiting too aggressive**
   - Adjust rate limits in `nginx.conf`
   - Redeploy with updated configuration

3. **Application not responding**
   - Check container status: `docker-compose ps`
   - View logs: `docker-compose logs`
   - Restart services: `sudo systemctl restart class-scheduler`

### Manual Deployment

If automated deployment fails, you can deploy manually:

```bash
# SSH into VPS
ssh user@35.197.99.197

# Navigate to deployment directory
cd /opt/class-scheduler

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose pull
docker-compose up -d
```

## Security Considerations

- Keep GitHub Actions IP ranges updated
- Regularly update Docker images and system packages
- Monitor logs for suspicious activity
- Consider adding SSL/TLS certificate for HTTPS
- Implement application-level authentication if needed

## Performance Tuning

- Adjust nginx worker processes based on CPU cores
- Tune rate limiting based on expected traffic
- Consider adding Redis for session storage if scaling
- Monitor resource usage and adjust container limits