# MCPX Server Deployment Guide

This guide walks you through deploying the MCPX HTTP MCP Server to a production Linux server.

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- Root or sudo access
- Domain name pointing to your server's IP address
- Ports 80 and 443 open in firewall

## Quick Deployment (Automated)

For a fully automated deployment, use the provided setup script:

```bash
# 1. Copy project files to server
scp -r . user@your-server:/tmp/mcpx

# 2. SSH into server
ssh user@your-server

# 3. Move to /opt and run setup
sudo mv /tmp/mcpx /opt/mcpx
cd /opt/mcpx/deployment
sudo ./setup.sh
```

The script will:
- ✅ Install all system dependencies (Python 3.12+, nginx, certbot)
- ✅ Install uv package manager
- ✅ Set up Python virtual environment
- ✅ Obtain SSL certificate from Let's Encrypt
- ✅ Configure nginx as reverse proxy
- ✅ Create and start systemd service
- ✅ Set up automatic SSL renewal

## Manual Deployment

### Step 1: System Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.12+
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev

# Install nginx
sudo apt-get install -y nginx

# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx
```

### Step 2: Install uv Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### Step 3: Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/mcpx
sudo chown $USER:$USER /opt/mcpx

# Copy application files
cp -r . /opt/mcpx/
cd /opt/mcpx

# Install Python dependencies
uv sync

# Create environment file
cp env.example .env
```

### Step 4: Configure Environment Variables

Edit `/opt/mcpx/.env`:

```bash
sudo nano /opt/mcpx/.env
```

Required configuration:

```bash
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_NAME=your-domain.com

# REQUIRED: Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-key-here

# OPTIONAL: Get from https://openweathermap.org/api
WEATHER_API_KEY=your-weather-key-here

CERTBOT_EMAIL=admin@your-domain.com
LOG_LEVEL=INFO
```

Secure the environment file:

```bash
sudo chown root:root /opt/mcpx/.env
sudo chmod 600 /opt/mcpx/.env
```

### Step 5: SSL Certificate

```bash
# Obtain certificate (replace your-domain.com)
sudo certbot certonly --nginx \
  -d your-domain.com \
  --non-interactive \
  --agree-tos \
  --email admin@your-domain.com
```

### Step 6: Configure nginx

```bash
# Update domain in nginx config
sudo sed -i 's/mcpx.lol/your-domain.com/g' /opt/mcpx/deployment/nginx.conf

# Copy nginx configuration
sudo cp /opt/mcpx/deployment/nginx.conf /etc/nginx/sites-available/mcpx.conf
sudo ln -s /etc/nginx/sites-available/mcpx.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### Step 7: Configure systemd Service

```bash
# Copy service file
sudo cp /opt/mcpx/deployment/systemd.service /etc/systemd/system/mcpx.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable mcpx.service

# Start the service
sudo systemctl start mcpx.service

# Check status
sudo systemctl status mcpx.service
```

### Step 8: Enable SSL Auto-Renewal

```bash
# Enable certbot timer
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal
sudo certbot renew --dry-run
```

## Verification

### Check Service Status

```bash
# Service status
sudo systemctl status mcpx.service

# View logs
sudo journalctl -u mcpx.service -f

# Check nginx logs
sudo tail -f /var/log/nginx/mcpx.access.log
sudo tail -f /var/log/nginx/mcpx.error.log
```

### Test the Server

```bash
# Test HTTPS connection
curl https://your-domain.com

# Test echo tool (requires MCP client or appropriate request format)
# The MCP server expects MCP protocol requests
```

### Health Check

```bash
# If you've configured a health endpoint
curl https://your-domain.com/health
```

## Firewall Configuration

### Using UFW (Ubuntu Firewall)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
sudo ufw status
```

### Using firewalld (CentOS/RHEL)

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u mcpx.service -n 50 --no-pager

# Check if port is in use
sudo lsof -i :8000

# Verify environment file
sudo cat /opt/mcpx/.env

# Test Python application manually
cd /opt/mcpx
uv run python -m src.main
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Manually renew
sudo certbot renew --force-renewal

# Check nginx SSL config
sudo nginx -t
```

### nginx Issues

```bash
# Check nginx status
sudo systemctl status nginx

# Check nginx error log
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/mcpx

# Fix environment file permissions
sudo chown root:root /opt/mcpx/.env
sudo chmod 600 /opt/mcpx/.env
```

## Maintenance

### Update Application

```bash
# Stop service
sudo systemctl stop mcpx.service

# Update code
cd /opt/mcpx
git pull  # or copy new files

# Update dependencies
uv sync

# Restart service
sudo systemctl start mcpx.service
```

### Update Python Dependencies

```bash
cd /opt/mcpx
uv sync --upgrade
sudo systemctl restart mcpx.service
```

### View Logs

```bash
# Application logs
sudo journalctl -u mcpx.service -f

# nginx access logs
sudo tail -f /var/log/nginx/mcpx.access.log

# nginx error logs
sudo tail -f /var/log/nginx/mcpx.error.log

# All logs from today
sudo journalctl -u mcpx.service --since today
```

### Rotate Logs

Logs are automatically rotated by systemd and nginx logrotate configuration. To manually configure:

```bash
# nginx logrotate (usually already configured)
sudo cat /etc/logrotate.d/nginx
```

### Backup Configuration

```bash
# Backup environment file
sudo cp /opt/mcpx/.env /opt/mcpx/.env.backup

# Backup nginx config
sudo cp /etc/nginx/sites-available/mcpx.conf /opt/mcpx/deployment/nginx.conf.backup

# Backup SSL certificates (optional, Let's Encrypt can regenerate)
sudo tar -czf ~/letsencrypt-backup.tar.gz /etc/letsencrypt/
```

## Monitoring

### Basic Monitoring with systemd

```bash
# Service status
sudo systemctl status mcpx.service

# Failed services
sudo systemctl --failed

# Resource usage
sudo systemctl status mcpx.service | grep -i memory
```

### Advanced Monitoring (Optional)

Consider setting up:
- **Prometheus** + **Grafana** for metrics
- **Loki** for log aggregation
- **Uptime Kuma** for uptime monitoring
- **Netdata** for real-time system monitoring

## Security Hardening

### Recommendations

1. **Keep system updated:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **Enable automatic security updates:**
   ```bash
   sudo apt-get install unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

3. **Use fail2ban to prevent brute force:**
   ```bash
   sudo apt-get install fail2ban
   sudo systemctl enable fail2ban
   ```

4. **Regular security audits:**
   ```bash
   # Check for security updates
   sudo apt-get upgrade -s | grep -i security
   ```

5. **Monitor logs for suspicious activity**

6. **Rotate API keys periodically**

7. **Use strong firewall rules**

## Performance Tuning

### nginx Tuning

Edit `/etc/nginx/nginx.conf`:

```nginx
worker_processes auto;
worker_connections 1024;

# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json;
```

### Python/uvicorn Tuning

For higher load, consider:
- Running multiple instances behind a load balancer
- Increasing worker processes
- Tuning timeouts and connection limits

### System Tuning

```bash
# Increase file descriptor limit
sudo nano /etc/security/limits.conf
# Add: * soft nofile 65536
# Add: * hard nofile 65536
```

## Scaling Considerations

For production at scale:

1. **Load Balancer:** Use nginx/HAProxy to distribute traffic across multiple instances
2. **Containerization:** Use Docker for easier deployment and scaling
3. **Orchestration:** Consider Kubernetes for automated scaling
4. **CDN:** Use Cloudflare or similar for DDoS protection
5. **Database:** If adding stateful features, use managed database services
6. **Monitoring:** Implement comprehensive monitoring and alerting
7. **Backup:** Regular automated backups of configuration and data

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review logs: `sudo journalctl -u mcpx.service -n 100`
- Open an issue on GitHub

---

Last updated: 2025-11-12

