#!/bin/bash
#
# MCPX Deployment Script
#
# This script deploys the MCPX server and brochure site to /data/web/mcpx.lol
#
# Prerequisites:
# - SSH access to the server
# - sudo privileges on the server
# - Domain (mcpx.lol) pointing to server IP
#
# Usage:
#   ./deploy.sh [user@]hostname
#
# Example:
#   ./deploy.sh root@mcpx.lol
#   ./deploy.sh user@192.168.1.100
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="mcpx.lol"
DEPLOY_DIR="/data/web/mcpx.lol"
DEPLOY_USER="www-data"
CERTBOT_EMAIL="admin@mcpx.lol"

# Check if hostname is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No hostname provided${NC}"
    echo "Usage: $0 [user@]hostname"
    echo "Example: $0 root@mcpx.lol"
    exit 1
fi

HOST="$1"

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    MCPX Deployment to $DOMAIN        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"

# Test SSH connection
echo -e "${BLUE}[1/12] Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=5 "$HOST" "echo 'SSH connection successful'" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to $HOST${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}\n"

# Create deployment directory
echo -e "${BLUE}[2/12] Creating deployment directory...${NC}"
ssh "$HOST" "sudo mkdir -p $DEPLOY_DIR/{public,data,logs} && \
            sudo chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR"
echo -e "${GREEN}✓ Directory created${NC}\n"

# Sync static website files
echo -e "${BLUE}[3/12] Deploying static website...${NC}"
rsync -avz --progress \
    --exclude 'nginx-conf' \
    ./web/mcpx.lol/ \
    "$HOST:$DEPLOY_DIR/public/"
ssh "$HOST" "sudo chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR/public"
echo -e "${GREEN}✓ Static files deployed${NC}\n"

# Sync MCP server code
echo -e "${BLUE}[4/12] Deploying MCP server code...${NC}"
rsync -avz --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache' \
    --exclude 'tests' \
    --exclude 'docs' \
    --exclude 'web' \
    --exclude '.git' \
    --exclude '.env' \
    --exclude 'data' \
    ./ \
    "$HOST:$DEPLOY_DIR/"
ssh "$HOST" "sudo chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR"
echo -e "${GREEN}✓ Server code deployed${NC}\n"

# Install system dependencies
echo -e "${BLUE}[5/12] Installing system dependencies...${NC}"
ssh "$HOST" << 'ENDSSH'
sudo apt-get update -qq
sudo apt-get install -y -qq python3.12 python3.12-venv python3-pip curl nginx certbot python3-certbot-nginx
ENDSSH
echo -e "${GREEN}✓ System dependencies installed${NC}\n"

# Install uv if not present
echo -e "${BLUE}[6/12] Installing uv package manager...${NC}"
ssh "$HOST" << 'ENDSSH'
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
ENDSSH
echo -e "${GREEN}✓ uv installed${NC}\n"

# Install Python dependencies
echo -e "${BLUE}[7/12] Installing Python dependencies...${NC}"
ssh "$HOST" << ENDSSH
cd $DEPLOY_DIR
export PATH="\$HOME/.cargo/bin:/usr/local/bin:\$PATH"
sudo -u $DEPLOY_USER uv sync
ENDSSH
echo -e "${GREEN}✓ Python dependencies installed${NC}\n"

# Setup environment file
echo -e "${BLUE}[8/12] Setting up environment configuration...${NC}"
ssh "$HOST" << ENDSSH
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    sudo cp $DEPLOY_DIR/deployment/production.env.example $DEPLOY_DIR/.env
    sudo chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_DIR/.env
    sudo chmod 600 $DEPLOY_DIR/.env
    echo -e "${YELLOW}⚠️  Created new .env file. YOU MUST EDIT IT WITH YOUR API KEYS!${NC}"
else
    echo -e "${GREEN}✓ Using existing .env file${NC}"
fi
ENDSSH
echo -e "${GREEN}✓ Environment configured${NC}\n"

# Setup SSL certificate
echo -e "${BLUE}[9/12] Setting up SSL certificate...${NC}"
ssh "$HOST" << ENDSSH
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Obtaining SSL certificate for $DOMAIN..."
    sudo certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email $CERTBOT_EMAIL --pre-hook "systemctl stop nginx" --post-hook "systemctl start nginx" || true
else
    echo -e "${GREEN}✓ SSL certificate already exists${NC}"
fi
ENDSSH
echo -e "${GREEN}✓ SSL configured${NC}\n"

# Install nginx configuration
echo -e "${BLUE}[10/12] Configuring nginx...${NC}"
ssh "$HOST" << ENDSSH
sudo cp $DEPLOY_DIR/deployment/mcpx.lol.nginx.conf /etc/nginx/sites-available/mcpx.lol
sudo ln -sf /etc/nginx/sites-available/mcpx.lol /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
ENDSSH
echo -e "${GREEN}✓ nginx configured${NC}\n"

# Install systemd service
echo -e "${BLUE}[11/12] Setting up systemd service...${NC}"
ssh "$HOST" << ENDSSH
sudo cp $DEPLOY_DIR/deployment/mcpx.service /etc/systemd/system/mcpx.service
sudo systemctl daemon-reload
sudo systemctl enable mcpx.service
ENDSSH
echo -e "${GREEN}✓ systemd service configured${NC}\n"

# Start/restart services
echo -e "${BLUE}[12/12] Starting services...${NC}"
ssh "$HOST" << ENDSSH
sudo systemctl restart mcpx.service
sudo systemctl reload nginx

# Wait a moment for services to start
sleep 2

# Check service status
echo -e "\n${BLUE}Service Status:${NC}"
sudo systemctl status mcpx.service --no-pager --lines=5 || true
ENDSSH
echo -e "${GREEN}✓ Services started${NC}\n"

# Display completion message
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       Deployment Complete! 🎉         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}Important Next Steps:${NC}"
echo -e "1. Edit the .env file with your API keys:"
echo -e "   ${BLUE}ssh $HOST 'sudo nano $DEPLOY_DIR/.env'${NC}"
echo -e ""
echo -e "2. Generate a secure JWT secret:"
echo -e "   ${BLUE}python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"${NC}"
echo -e ""
echo -e "3. Restart the service after editing .env:"
echo -e "   ${BLUE}ssh $HOST 'sudo systemctl restart mcpx.service'${NC}"
echo -e ""
echo -e "4. Check logs if needed:"
echo -e "   ${BLUE}ssh $HOST 'sudo journalctl -u mcpx.service -f'${NC}"
echo -e ""
echo -e "5. Test the deployment:"
echo -e "   ${BLUE}curl https://$DOMAIN${NC}"
echo -e "   ${BLUE}curl https://$DOMAIN/mcpx/health${NC}"
echo -e ""
echo -e "${GREEN}Your site should now be live at: https://$DOMAIN${NC}\n"

