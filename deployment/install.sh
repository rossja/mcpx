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
# apt-get update -qq # TODO: make apt update optional

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
fi

# Find where uv was installed and make it available system-wide
UV_LOCATION=""
if [ -f /root/.local/bin/uv ]; then
    UV_LOCATION="/root/.local/bin/uv"
elif [ -f /root/.cargo/bin/uv ]; then
    UV_LOCATION="/root/.cargo/bin/uv"
elif command -v uv &> /dev/null; then
    UV_LOCATION=$(which uv)
fi

if [ -n "$UV_LOCATION" ]; then
    # Copy (not symlink) to /usr/bin so it's always in PATH for all users
    # This is needed because www-data can't access /root/.local/bin
    # and /usr/bin is guaranteed to be in PATH even with restricted sudo
    if [ ! -f /usr/bin/uv ] || [ "$UV_LOCATION" -nt /usr/bin/uv ]; then
        cp "$UV_LOCATION" /usr/bin/uv
        chmod 755 /usr/bin/uv
    fi
fi
echo -e "${GREEN}✓ uv installed${NC}\n"

# Step 3: Create deployment directory structure
echo -e "${BLUE}[3/10] Creating deployment directory...${NC}"
mkdir -p "$DEPLOY_DIR"/{public,data,logs}
echo -e "${GREEN}✓ Directory structure created${NC}\n"

# Step 4: Copy static website files
echo -e "${BLUE}[4/10] Copying static website...${NC}"
# Check if we're already in the deployment directory
if [ "$(realpath "$REPO_ROOT")" = "$(realpath "$DEPLOY_DIR")" ]; then
    echo -e "${YELLOW}⚠️  Already running from deployment directory - skipping file copy${NC}"
else
    cp -r "$REPO_ROOT/web/mcpx.lol"/* "$DEPLOY_DIR/public/"
    echo -e "${GREEN}✓ Static files copied${NC}"
fi
echo

# Step 5: Copy MCP server code
echo -e "${BLUE}[5/10] Copying MCP server code...${NC}"
# Check if we're already in the deployment directory
if [ "$(realpath "$REPO_ROOT")" = "$(realpath "$DEPLOY_DIR")" ]; then
    echo -e "${YELLOW}⚠️  Already running from deployment directory - skipping code copy${NC}"
else
    # Copy all necessary files
    cp "$REPO_ROOT/pyproject.toml" "$DEPLOY_DIR/"
    cp "$REPO_ROOT/uv.lock" "$DEPLOY_DIR/"
    cp -r "$REPO_ROOT/mcp_server" "$DEPLOY_DIR/"
    cp -r "$REPO_ROOT/deployment" "$DEPLOY_DIR/"

    # Copy README and LICENSE for reference
    cp "$REPO_ROOT/README.md" "$DEPLOY_DIR/"
    cp "$REPO_ROOT/LICENSE" "$DEPLOY_DIR/"
    echo -e "${GREEN}✓ Server code copied${NC}"
fi
echo

# Step 6: Set permissions
echo -e "${BLUE}[6/10] Setting permissions...${NC}"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
chmod -R 755 "$DEPLOY_DIR"
chmod 755 "$DEPLOY_DIR/data"  # Allow write for database
echo -e "${GREEN}✓ Permissions set${NC}\n"

# Step 7: Install Python dependencies
echo -e "${BLUE}[7/10] Installing Python dependencies...${NC}"
cd "$DEPLOY_DIR"

# Create cache directory for uv in our deployment directory
mkdir -p "$DEPLOY_DIR/data/.uv-cache"
chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR/data/.uv-cache"

# Run uv sync as the deploy user
# Set UV_CACHE_DIR to use our deployment directory instead of /var/www/.cache
# We use /usr/bin/uv which was copied there in step 2 (guaranteed to be in PATH)
sudo -u "$DEPLOY_USER" env UV_CACHE_DIR="$DEPLOY_DIR/data/.uv-cache" /usr/bin/uv sync
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

# Disable any duplicate or old nginx configs by renaming them
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f /etc/nginx/sites-enabled/mcpx.lol.conf ]; then
    mv /etc/nginx/sites-enabled/mcpx.lol.conf "/etc/nginx/sites-enabled/mcpx.lol.conf.disabled_${TIMESTAMP}"
    echo -e "${YELLOW}⚠️  Disabled duplicate config: mcpx.lol.conf -> mcpx.lol.conf.disabled_${TIMESTAMP}${NC}"
fi
if [ -f /etc/nginx/sites-available/mcpx.lol.conf ]; then
    mv /etc/nginx/sites-available/mcpx.lol.conf "/etc/nginx/sites-available/mcpx.lol.conf.disabled_${TIMESTAMP}"
    echo -e "${YELLOW}⚠️  Backed up duplicate config: sites-available/mcpx.lol.conf${NC}"
fi

# Check if config already exists and is working
CONFIG_EXISTS=false
if [ -f /etc/nginx/sites-available/mcpx.lol ]; then
    # Check if the config has the required upstream and location blocks
    if grep -q "upstream mcpx" /etc/nginx/sites-available/mcpx.lol && \
       grep -q "location /mcpx" /etc/nginx/sites-available/mcpx.lol; then
        CONFIG_EXISTS=true
        echo -e "${GREEN}✓ nginx configuration already exists${NC}"
    fi
fi

# Check if SSL certificate exists
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    SSL_CONFIGURED=1
    if [ "$CONFIG_EXISTS" = false ]; then
        echo -e "${YELLOW}⚠️  Installing nginx config with SSL support${NC}"
        # Install nginx config with SSL
        cp "$DEPLOY_DIR/deployment/mcpx.lol.nginx.conf" /etc/nginx/sites-available/mcpx.lol
    else
        echo -e "${GREEN}✓ SSL certificate already exists${NC}"
    fi
else
    SSL_CONFIGURED=0
    if [ "$CONFIG_EXISTS" = false ]; then
        echo -e "${YELLOW}⚠️  No SSL certificate found - installing HTTP-only config${NC}"
        # Create temporary HTTP-only nginx config
        cat > /etc/nginx/sites-available/mcpx.lol << 'NGINXCONF'
# Upstream for MCP server
upstream mcpx {
  server localhost:1337;
}

server {
    listen 80;
    listen [::]:80;
    server_name mcpx.lol www.mcpx.lol;

    root /data/web/mcpx.lol/public;
    index index.html;

    # Allow Let's Encrypt validation
    location /.well-known {
        allow all;
    }

    # Static site
    location / {
        try_files $uri $uri/ =404;
    }

    # MCP server proxy
    location /mcpx {
        proxy_pass http://mcpx/$is_args$args;
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
    else
        echo -e "${YELLOW}⚠️  No SSL certificate found${NC}"
    fi
fi

# Enable the site
ln -sf /etc/nginx/sites-available/mcpx.lol /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
if nginx -t 2>/dev/null; then
    systemctl reload nginx
    echo -e "${GREEN}✓ nginx configured and reloaded${NC}"
else
    echo -e "${YELLOW}⚠️  nginx configuration test failed - please check manually${NC}"
    echo -e "${YELLOW}   Run: nginx -t${NC}"
fi
echo

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


