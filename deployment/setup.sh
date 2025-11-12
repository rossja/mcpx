#!/bin/bash
#
# MCPX Server Deployment Script
#
# This script automates the deployment of the MCPX HTTP MCP Server
# on a Linux server with nginx and Let's Encrypt SSL.
#
# Prerequisites:
# - Ubuntu/Debian-based system
# - Root or sudo access
# - Domain name (mcpx.lol) pointing to server IP
#
# Usage:
#   sudo ./setup.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="mcpx.lol"
APP_DIR="/opt/mcpx"
APP_USER="www-data"
CERTBOT_EMAIL="admin@mcpx.lol"

echo -e "${GREEN}=== MCPX Server Deployment ===${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Update system packages
echo -e "${YELLOW}[1/10] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Install Python 3.12+
echo -e "${YELLOW}[2/10] Installing Python 3.12+...${NC}"
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.12 python3.12-venv python3.12-dev

# Install uv
echo -e "${YELLOW}[3/10] Installing uv package manager...${NC}"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Install nginx
echo -e "${YELLOW}[4/10] Installing nginx...${NC}"
apt-get install -y nginx

# Install certbot
echo -e "${YELLOW}[5/10] Installing certbot...${NC}"
apt-get install -y certbot python3-certbot-nginx

# Create application directory
echo -e "${YELLOW}[6/10] Setting up application directory...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or copy application code
# (Assumes code is already in $APP_DIR or will be deployed separately)
echo -e "${YELLOW}[7/10] Installing Python dependencies...${NC}"
if [ -f "pyproject.toml" ]; then
    uv sync
else
    echo -e "${RED}pyproject.toml not found. Please copy application code to $APP_DIR${NC}"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > $APP_DIR/.env << EOF
# Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_NAME=$DOMAIN

# API Keys (REPLACE THESE VALUES)
OPENAI_API_KEY=your_openai_api_key_here
WEATHER_API_KEY=your_weather_api_key_here

# SSL Configuration
CERTBOT_EMAIL=$CERTBOT_EMAIL

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
    echo -e "${RED}⚠️  Please edit $APP_DIR/.env and add your API keys!${NC}"
fi

# Set permissions
chown -R $APP_USER:$APP_USER $APP_DIR
chmod 600 $APP_DIR/.env

# Obtain SSL certificate
echo -e "${YELLOW}[8/10] Obtaining SSL certificate from Let's Encrypt...${NC}"
certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email $CERTBOT_EMAIL

# Configure nginx
echo -e "${YELLOW}[9/10] Configuring nginx...${NC}"
cp $APP_DIR/deployment/nginx.conf /etc/nginx/sites-available/mcpx.conf
ln -sf /etc/nginx/sites-available/mcpx.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Configure systemd service
echo -e "${YELLOW}[10/10] Setting up systemd service...${NC}"
cp $APP_DIR/deployment/systemd.service /etc/systemd/system/mcpx.service
systemctl daemon-reload
systemctl enable mcpx.service

# Start services
echo -e "${GREEN}Starting services...${NC}"
systemctl restart nginx
systemctl start mcpx.service

# Setup auto-renewal for SSL certificates
echo -e "${GREEN}Setting up SSL certificate auto-renewal...${NC}"
systemctl enable certbot.timer
systemctl start certbot.timer

# Display status
echo -e "\n${GREEN}=== Deployment Complete ===${NC}\n"
echo -e "Service status:"
systemctl status mcpx.service --no-pager
echo -e "\nnginx status:"
systemctl status nginx --no-pager

echo -e "\n${GREEN}Next steps:${NC}"
echo -e "1. Edit $APP_DIR/.env and add your API keys"
echo -e "2. Restart the service: sudo systemctl restart mcpx.service"
echo -e "3. Check logs: sudo journalctl -u mcpx.service -f"
echo -e "4. Test the server: https://$DOMAIN"
echo -e "\n${YELLOW}Remember to configure your firewall to allow ports 80 and 443!${NC}"

