#!/bin/bash
#
# MCPX Configuration Verification Script
#
# This script checks that your MCPX installation is properly configured
# before you start the service.
#
# Usage:
#   sudo ./deployment/verify-config.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DEPLOY_DIR="/data/web/mcpx.lol"
ERRORS=0
WARNINGS=0

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  MCPX Configuration Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  Warning: Not running as root. Some checks may fail.${NC}\n"
fi

# Check 1: Deployment directory exists
echo -e "${BLUE}[1/10] Checking deployment directory...${NC}"
if [ -d "$DEPLOY_DIR" ]; then
    echo -e "${GREEN}✓ Deployment directory exists${NC}\n"
else
    echo -e "${RED}✗ Deployment directory not found: $DEPLOY_DIR${NC}"
    echo -e "${YELLOW}   Run: sudo ./deployment/install.sh${NC}\n"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: .env file exists
echo -e "${BLUE}[2/10] Checking .env file...${NC}"
if [ -f "$DEPLOY_DIR/.env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}\n"
else
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "${YELLOW}   Run: sudo cp $DEPLOY_DIR/deployment/production.env.example $DEPLOY_DIR/.env${NC}\n"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: JWT secret key is set
echo -e "${BLUE}[3/10] Checking JWT_SECRET_KEY...${NC}"
if [ -f "$DEPLOY_DIR/.env" ]; then
    JWT_SECRET=$(grep "^JWT_SECRET_KEY=" "$DEPLOY_DIR/.env" | cut -d'=' -f2-)
    if [ "$JWT_SECRET" = "CHANGE-ME-TO-A-SECURE-RANDOM-KEY" ] || [ "$JWT_SECRET" = "your-super-secret-jwt-key-here" ] || [ -z "$JWT_SECRET" ]; then
        echo -e "${RED}✗ JWT_SECRET_KEY not properly configured${NC}"
        echo -e "${YELLOW}   Generate one with: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"${NC}"
        echo -e "${YELLOW}   Then edit: sudo nano $DEPLOY_DIR/.env${NC}\n"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓ JWT_SECRET_KEY is configured${NC}\n"
    fi
fi

# Check 4: OpenAI API key is set
echo -e "${BLUE}[4/10] Checking OPENAI_API_KEY...${NC}"
if [ -f "$DEPLOY_DIR/.env" ]; then
    OPENAI_KEY=$(grep "^OPENAI_API_KEY=" "$DEPLOY_DIR/.env" | cut -d'=' -f2-)
    if [ "$OPENAI_KEY" = "sk-your-openai-api-key-here" ] || [ -z "$OPENAI_KEY" ]; then
        echo -e "${YELLOW}⚠️  OPENAI_API_KEY not configured${NC}"
        echo -e "${YELLOW}   Web search tool will not work${NC}"
        echo -e "${YELLOW}   Get your key at: https://platform.openai.com/api-keys${NC}\n"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓ OPENAI_API_KEY is configured${NC}\n"
    fi
fi

# Check 5: Python dependencies installed
echo -e "${BLUE}[5/10] Checking Python dependencies...${NC}"
if [ -d "$DEPLOY_DIR/.venv" ]; then
    echo -e "${GREEN}✓ Python virtual environment exists${NC}\n"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo -e "${YELLOW}   Run: cd $DEPLOY_DIR && sudo -u www-data uv sync${NC}\n"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 6: nginx configuration
echo -e "${BLUE}[6/10] Checking nginx configuration...${NC}"
if [ -f "/etc/nginx/sites-available/mcpx.lol" ]; then
    if nginx -t 2>&1 | grep -q "test is successful"; then
        echo -e "${GREEN}✓ nginx configuration is valid${NC}\n"
    else
        echo -e "${RED}✗ nginx configuration has errors${NC}"
        echo -e "${YELLOW}   Run: sudo nginx -t${NC}\n"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗ nginx configuration not found${NC}"
    echo -e "${YELLOW}   Run: sudo ./deployment/install.sh${NC}\n"
    ERRORS=$((ERRORS + 1))
fi

# Check 7: systemd service file
echo -e "${BLUE}[7/10] Checking systemd service...${NC}"
if [ -f "/etc/systemd/system/mcpx.service" ]; then
    echo -e "${GREEN}✓ systemd service file exists${NC}\n"
else
    echo -e "${RED}✗ systemd service file not found${NC}"
    echo -e "${YELLOW}   Run: sudo ./deployment/install.sh${NC}\n"
    ERRORS=$((ERRORS + 1))
fi

# Check 8: uv package manager
echo -e "${BLUE}[8/10] Checking uv package manager...${NC}"
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓ uv is installed${NC}\n"
else
    echo -e "${RED}✗ uv is not installed${NC}"
    echo -e "${YELLOW}   Run: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}\n"
    ERRORS=$((ERRORS + 1))
fi

# Check 9: File permissions
echo -e "${BLUE}[9/10] Checking file permissions...${NC}"
if [ -d "$DEPLOY_DIR" ]; then
    OWNER=$(stat -c '%U:%G' "$DEPLOY_DIR" 2>/dev/null || stat -f '%Su:%Sg' "$DEPLOY_DIR" 2>/dev/null)
    if [ "$OWNER" = "www-data:www-data" ]; then
        echo -e "${GREEN}✓ File permissions are correct${NC}\n"
    else
        echo -e "${YELLOW}⚠️  File owner is $OWNER (expected www-data:www-data)${NC}"
        echo -e "${YELLOW}   Run: sudo chown -R www-data:www-data $DEPLOY_DIR${NC}\n"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check 10: Port availability
echo -e "${BLUE}[10/10] Checking port 1337...${NC}"
if lsof -i :1337 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Port 1337 is already in use${NC}"
    echo -e "${YELLOW}   Check with: sudo lsof -i :1337${NC}\n"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ Port 1337 is available${NC}\n"
fi

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Verification Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Your installation looks good.${NC}\n"
    echo -e "You can now start the service:"
    echo -e "  ${GREEN}sudo systemctl start mcpx.service${NC}\n"
    echo -e "Check status with:"
    echo -e "  ${GREEN}sudo systemctl status mcpx.service${NC}\n"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found${NC}"
    echo -e "The service should work, but some features may be limited.\n"
    echo -e "You can start the service:"
    echo -e "  ${GREEN}sudo systemctl start mcpx.service${NC}\n"
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found${NC}"
    fi
    echo -e "\n${RED}Please fix the errors above before starting the service.${NC}\n"
    exit 1
fi

