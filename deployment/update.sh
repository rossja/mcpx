#!/bin/bash
#
# MCPX Update Script
#
# This script updates an existing MCPX installation.
# Run this script directly on your server to pull the latest changes.
#
# Usage:
#   sudo ./deployment/update.sh
#
# This script will:
#   - Pull latest code from git (or copy from temp clone)
#   - Update Python dependencies
#   - Update nginx configuration
#   - Update systemd service
#   - Restart the service
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

# Check if deployment exists
if [ ! -d "$DEPLOY_DIR" ]; then
    echo -e "${RED}Error: Deployment directory not found at $DEPLOY_DIR${NC}"
    echo -e "${RED}Please run install.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    MCPX Update Script                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"

# Determine update source
UPDATE_FROM_GIT=false
if [ -d "$DEPLOY_DIR/.git" ]; then
    UPDATE_FROM_GIT=true
    echo -e "${BLUE}Detected git repository in deployment directory${NC}\n"
elif [ "$(realpath "$REPO_ROOT")" = "$(realpath "$DEPLOY_DIR")" ]; then
    echo -e "${YELLOW}Running from deployment directory - cannot self-update${NC}"
    echo -e "${YELLOW}Please run from a fresh git clone in /tmp${NC}\n"
    exit 1
fi

# Step 1: Update code
echo -e "${BLUE}[1/6] Updating code...${NC}"
if [ "$UPDATE_FROM_GIT" = true ]; then
    cd "$DEPLOY_DIR"
    sudo -u "$DEPLOY_USER" git pull
    echo -e "${GREEN}✓ Code updated from git${NC}"
else
    # Copy from repo root (e.g., /tmp/mcpx)
    if [ ! -f "$REPO_ROOT/pyproject.toml" ]; then
        echo -e "${RED}Error: Not running from a valid git clone${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Copying files from $REPO_ROOT${NC}"
    cp "$REPO_ROOT/pyproject.toml" "$DEPLOY_DIR/"
    
    if [ -f "$REPO_ROOT/uv.lock" ]; then
        cp "$REPO_ROOT/uv.lock" "$DEPLOY_DIR/"
    fi
    
    # Update mcp_server code
    rsync -av --delete "$REPO_ROOT/mcp_server/" "$DEPLOY_DIR/mcp_server/"
    
    # Update deployment scripts
    rsync -av "$REPO_ROOT/deployment/" "$DEPLOY_DIR/deployment/"
    
    # Update static files
    if [ -d "$REPO_ROOT/web/mcpx.lol" ]; then
        rsync -av --delete "$REPO_ROOT/web/mcpx.lol/" "$DEPLOY_DIR/public/"
    fi
    
    # Update docs (optional)
    [ -f "$REPO_ROOT/README.md" ] && cp "$REPO_ROOT/README.md" "$DEPLOY_DIR/"
    [ -f "$REPO_ROOT/LICENSE" ] && cp "$REPO_ROOT/LICENSE" "$DEPLOY_DIR/"
    
    echo -e "${GREEN}✓ Code updated from local clone${NC}"
fi
echo

# Step 2: Update dependencies
echo -e "${BLUE}[2/6] Updating Python dependencies...${NC}"
cd "$DEPLOY_DIR"

# Create cache directory for uv if it doesn't exist
mkdir -p "$DEPLOY_DIR/data/.uv-cache"
chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR/data/.uv-cache"

# Run uv sync to update dependencies
sudo -u "$DEPLOY_USER" env UV_CACHE_DIR="$DEPLOY_DIR/data/.uv-cache" /usr/bin/uv sync
echo -e "${GREEN}✓ Dependencies updated${NC}\n"

# Step 3: Skip nginx configuration (managed separately)
echo -e "${BLUE}[3/6] Nginx configuration...${NC}"
echo -e "${YELLOW}⚠️  Skipping nginx config update (managed separately)${NC}"
echo -e "${YELLOW}   Updated config available at: $DEPLOY_DIR/deployment/mcpx.lol.nginx.conf${NC}"
echo -e "${YELLOW}   To update manually: sudo cp $DEPLOY_DIR/deployment/mcpx.lol.nginx.conf /etc/nginx/sites-available/mcpx.lol${NC}"
echo

# Step 4: Skip systemd service (managed separately)
echo -e "${BLUE}[4/6] Systemd service...${NC}"
echo -e "${YELLOW}⚠️  Skipping systemd service update (managed separately)${NC}"
echo -e "${YELLOW}   Updated service file available at: $DEPLOY_DIR/deployment/mcpx.service${NC}"
echo -e "${YELLOW}   To update manually: sudo cp $DEPLOY_DIR/deployment/mcpx.service /etc/systemd/system/mcpx.service && sudo systemctl daemon-reload${NC}"
echo

# Step 5: Set permissions
echo -e "${BLUE}[5/6] Fixing permissions...${NC}"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
chmod -R 755 "$DEPLOY_DIR"
chmod 755 "$DEPLOY_DIR/data"
if [ -f "$DEPLOY_DIR/.env" ]; then
    chmod 600 "$DEPLOY_DIR/.env"
fi
echo -e "${GREEN}✓ Permissions fixed${NC}\n"

# Step 6: Restart service
echo -e "${BLUE}[6/6] Restarting MCPX service...${NC}"
systemctl restart mcpx.service

# Wait a moment for service to start
sleep 2

if systemctl is-active --quiet mcpx.service; then
    echo -e "${GREEN}✓ Service restarted successfully${NC}\n"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo -e "${YELLOW}Check logs with: journalctl -u mcpx.service -n 50${NC}\n"
fi

# Display completion message
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    Update Complete! 🎉                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Post-Update Information${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}\n"

echo -e "${BLUE}Service Status:${NC}"
echo -e "   ${GREEN}systemctl status mcpx.service${NC}\n"

echo -e "${BLUE}View Logs:${NC}"
echo -e "   ${GREEN}journalctl -u mcpx.service -f${NC}\n"

echo -e "${BLUE}Test the Service:${NC}"
echo -e "   ${GREEN}curl https://$DOMAIN/mcpx/oauth/authorize${NC}\n"

if [ "$UPDATE_FROM_GIT" = false ]; then
    echo -e "${YELLOW}Note: You can delete the temporary clone directory now${NC}"
    echo -e "   ${GREEN}rm -rf $REPO_ROOT${NC}\n"
fi

echo -e "${GREEN}Update completed successfully!${NC}\n"

