#!/bin/bash
#
# MCPX Local Installation Script
#
# This script installs MCPX on the local server.
# Run this script directly on your server after cloning the repo.
#
# Usage:
#   sudo ./deployment/install.sh
#
# This script will:
#   - Install system dependencies (Python, nginx, certbot, uv)
#   - Create deployment directory structure
#   - Copy files to /data/web/mcpx.lol
#   - Install and configure nginx
#   - Setup systemd service
#   - Create .env file from template
#   - Optionally obtain SSL certificate
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    MCPX Local Installation             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"

# Step 1: Install system dependencies
echo -e "${BLUE}[1/10] Installing system dependencies...${NC}"
apt-get update -qq

# Try to install Python 3.12, fall back to 3.11 or 3.10 if not available
PYTHON_VERSION=""
if apt-cache show python3.12 &>/dev/null; then
    apt-get install -y -qq python3.12 python3.12-venv
    PYTHON_VERSION="python3.12"
elif apt-cache show python3.11 &>/dev/null; then
    apt-get install -y -qq python3.11 python3.11-venv
    PYTHON_VERSION="python3.11"
else
    # Fall back to default python3
    apt-get install -y -qq python3 python3-venv
    PYTHON_VERSION="python3"
fi

# Install other dependencies
apt-get install -y -qq python3-pip curl nginx certbot python3-certbot-nginx

# Check Python version
PYTHON_VER=$($PYTHON_VERSION --version | cut -d' ' -f2)
echo -e "${GREEN}✓ System dependencies installed (Python $PYTHON_VER)${NC}\n"

# Step 2: Install uv if not present
echo -e "${BLUE}[2/10] Installing uv package manager...${NC}"
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="/root/.cargo/bin:$PATH"
fi
# Make uv available system-wide
if [ ! -f /usr/local/bin/uv ]; then
    ln -sf /root/.cargo/bin/uv /usr/local/bin/uv
fi
echo -e "${GREEN}✓ uv installed${NC}\n"

# Step 3: Create deployment directory structure
echo -e "${BLUE}[3/10] Creating deployment directory...${NC}"
mkdir -p "$DEPLOY_DIR"/{public,data,logs}
echo -e "${GREEN}✓ Directory structure created${NC}\n"

# Step 4: Copy static website files
echo -e "${BLUE}[4/10] Copying static website...${NC}"
cp -r "$REPO_ROOT/web/mcpx.lol"/* "$DEPLOY_DIR/public/"
echo -e "${GREEN}✓ Static files copied${NC}\n"

# Step 5: Copy MCP server code
echo -e "${BLUE}[5/10] Copying MCP server code...${NC}"
# Copy all necessary files
cp "$REPO_ROOT/pyproject.toml" "$DEPLOY_DIR/"
cp "$REPO_ROOT/uv.lock" "$DEPLOY_DIR/"
cp -r "$REPO_ROOT/mcp_server" "$DEPLOY_DIR/"
cp -r "$REPO_ROOT/deployment" "$DEPLOY_DIR/"

# Copy README and LICENSE for reference
cp "$REPO_ROOT/README.md" "$DEPLOY_DIR/"
cp "$REPO_ROOT/LICENSE" "$DEPLOY_DIR/"
echo -e "${GREEN}✓ Server code copied${NC}\n"

# Step 6: Set permissions
echo -e "${BLUE}[6/10] Setting permissions...${NC}"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
chmod -R 755 "$DEPLOY_DIR"
chmod 755 "$DEPLOY_DIR/data"  # Allow write for database
echo -e "${GREEN}✓ Permissions set${NC}\n"

# Step 7: Install Python dependencies
echo -e "${BLUE}[7/10] Installing Python dependencies...${NC}"
cd "$DEPLOY_DIR"
sudo -u "$DEPLOY_USER" /usr/local/bin/uv sync
echo -e "${GREEN}✓ Python dependencies installed${NC}\n"

# Step 8: Setup environment file
echo -e "${BLUE}[8/10] Setting up environment configuration...${NC}"
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    cp "$DEPLOY_DIR/deployment/production.env.example" "$DEPLOY_DIR/.env"
    chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR/.env"
    chmod 600 "$DEPLOY_DIR/.env"
    echo -e "${YELLOW}⚠️  Created new .env file at: $DEPLOY_DIR/.env${NC}"
    echo -e "${YELLOW}⚠️  YOU MUST EDIT THIS FILE before starting the service!${NC}"
else
    echo -e "${GREEN}✓ Using existing .env file${NC}"
fi
echo -e "${GREEN}✓ Environment configured${NC}\n"

# Step 9: Install nginx configuration
echo -e "${BLUE}[9/10] Configuring nginx...${NC}"

# Check if SSL certificate exists
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo -e "${GREEN}✓ SSL certificate already exists${NC}"
    # Install nginx config with SSL
    cp "$DEPLOY_DIR/deployment/mcpx.lol.nginx.conf" /etc/nginx/sites-available/mcpx.lol
    SSL_CONFIGURED=1
else
    echo -e "${YELLOW}⚠️  No SSL certificate found${NC}"
    # Create temporary HTTP-only nginx config
    cat > /etc/nginx/sites-available/mcpx.lol << 'NGINXCONF'
server {
    listen 80;
    server_name mcpx.lol www.mcpx.lol;

    root /data/web/mcpx.lol/public;
    index index.html;

    # Static site
    location / {
        try_files $uri $uri/ =404;
    }

    # MCP server proxy
    location /mcpx/ {
        proxy_pass http://127.0.0.1:1337/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Streaming support
        proxy_buffering off;
        proxy_cache off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINXCONF
    SSL_CONFIGURED=0
fi

ln -sf /etc/nginx/sites-available/mcpx.lol /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
echo -e "${GREEN}✓ nginx configured${NC}\n"

# Step 10: Install systemd service
echo -e "${BLUE}[10/10] Setting up systemd service...${NC}"
cp "$DEPLOY_DIR/deployment/mcpx.service" /etc/systemd/system/mcpx.service
systemctl daemon-reload
systemctl enable mcpx.service
echo -e "${GREEN}✓ systemd service configured${NC}\n"

# Display completion message
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    Installation Complete! 🎉           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  IMPORTANT: Next Steps (Required!)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}\n"

echo -e "${BLUE}Step 1: Edit the .env file with your API keys${NC}"
echo -e "   sudo nano $DEPLOY_DIR/.env\n"
echo -e "   Required changes:"
echo -e "   - JWT_SECRET_KEY: Generate with:"
echo -e "     ${GREEN}python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"${NC}"
echo -e "   - OPENAI_API_KEY: Your OpenAI API key"
echo -e "   - WEATHER_API_KEY: Your weather API key (optional)\n"

if [ $SSL_CONFIGURED -eq 0 ]; then
    echo -e "${BLUE}Step 2: Obtain SSL certificate (if using a domain)${NC}"
    echo -e "   ${GREEN}sudo certbot --nginx -d $DOMAIN${NC}"
    echo -e "   ${YELLOW}Note: Make sure your domain DNS is pointing to this server first!${NC}\n"
    NEXT_STEP=3
else
    NEXT_STEP=2
fi

echo -e "${BLUE}Step $NEXT_STEP: Start the MCPX service${NC}"
echo -e "   ${GREEN}sudo systemctl start mcpx.service${NC}\n"

NEXT_STEP=$((NEXT_STEP + 1))
echo -e "${BLUE}Step $NEXT_STEP: Check that everything is working${NC}"
echo -e "   ${GREEN}sudo systemctl status mcpx.service${NC}"
echo -e "   ${GREEN}curl http://localhost:1337/health${NC}\n"

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Useful Commands${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}\n"

echo -e "View service logs:"
echo -e "   ${GREEN}sudo journalctl -u mcpx.service -f${NC}\n"

echo -e "Restart service (after editing .env):"
echo -e "   ${GREEN}sudo systemctl restart mcpx.service${NC}\n"

echo -e "Test the deployment:"
if [ $SSL_CONFIGURED -eq 1 ]; then
    echo -e "   ${GREEN}curl https://$DOMAIN${NC}"
    echo -e "   ${GREEN}curl https://$DOMAIN/mcpx/health${NC}\n"
else
    echo -e "   ${GREEN}curl http://$DOMAIN${NC}"
    echo -e "   ${GREEN}curl http://$DOMAIN/mcpx/health${NC}\n"
fi

echo -e "${GREEN}Installation directory: $DEPLOY_DIR${NC}\n"

