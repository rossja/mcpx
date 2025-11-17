# MCPX Deployment Guide

This directory contains all the files needed to deploy MCPX to production at `/data/web/mcpx.lol`.

## Two Deployment Options

### Option 1: Local Installation (Recommended - Simplest!)

Clone the repo on your server and install directly:

```bash
# On your server
git clone https://github.com/rossja/mcpx.git
cd mcpx
sudo ./deployment/install.sh
```

This is the **simplest** approach - just 4 steps total! See [INSTALL.md](../INSTALL.md) for the complete guide.

### Option 2: Remote Deployment

Deploy from your local machine to a remote server:

```bash
# On your local machine
./deployment/deploy.sh root@mcpx.lol
```

This is useful if you want to manage deployments from your workstation.

## What Gets Deployed

The deployment script will:

1. **Static Website** → `/data/web/mcpx.lol/public/`
   - `index.html`, `styles.css`, `script.js`
   - Served directly by nginx at the root URL

2. **MCP Server** → `/data/web/mcpx.lol/`
   - Python application running on port 1337
   - Accessible at `https://mcpx.lol/mcp`
   - Managed by systemd service

3. **Configuration Files**
   - nginx config → `/etc/nginx/sites-available/mcpx.lol`
   - systemd service → `/etc/systemd/system/mcpx.service`
   - Environment → `/data/web/mcpx.lol/.env`

## File Overview

- **`install.sh`** - Local installation script (run on the server) ⭐ **USE THIS!**
- **`deploy.sh`** - Remote deployment script (run from your local machine)
- **`verify-config.sh`** - Configuration verification script
- **`mcpx.service`** - systemd service configuration
- **`mcpx.lol.nginx.conf`** - nginx configuration (static site + MCP proxy)
- **`production.env.example`** - Environment template for production
- **`QUICKSTART.md`** - Ultra-condensed installation guide
- **`CHECKLIST.md`** - Step-by-step installation checklist
- **`QUICK_REFERENCE.md`** - Command reference for common tasks
- **`README.md`** - This detailed deployment guide

## Architecture

```
                                  ┌──────────────────┐
                                  │   mcpx.lol       │
                                  │   (HTTPS:443)    │
                                  └────────┬─────────┘
                                           │
                              ┌────────────┴──────────────┐
                              │                           │
                              │         nginx             │
                              │                           │
                              └─┬─────────────────────┬──┘
                                │                     │
                   ┌────────────┴────────┐   ┌────────┴──────────┐
                   │  Static Files       │   │  /mcpx → proxy    │
                   │  /data/web/mcpx.lol │   │  to localhost:1337│
                   │  /public/           │   └────────┬──────────┘
                   └─────────────────────┘            │
                                              ┌────────┴──────────┐
                                              │  MCPX Server      │
                                              │  (Python/uvicorn) │
                                              │  Port: 1337       │
                                              └───────────────────┘
```

## Prerequisites

### On Your Local Machine

- SSH access to the server
- rsync installed

### On The Server

The deployment script will install:
- Python 3.10+ (tries 3.12, 3.11, or falls back to available version)
- uv (package manager)
- nginx
- certbot (for SSL)

## Step-by-Step Deployment

### 1. Initial Setup

First time deploying? The script handles everything:

```bash
cd /Users/ross.j/src/rossja/mcpx
./deployment/deploy.sh root@your-server-ip
```

### 2. Configure Environment

After the first deployment, you MUST configure your API keys:

```bash
ssh root@mcpx.lol
nano /data/web/mcpx.lol/.env
```

Update these values:
- `JWT_SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `OPENAI_API_KEY` - Your OpenAI API key
- `WEATHER_API_KEY` - Your weather API key (optional)

### 3. Restart the Service

After editing `.env`:

```bash
sudo systemctl restart mcpx.service
```

### 4. Verify Deployment

Check the service is running:

```bash
sudo systemctl status mcpx.service
sudo journalctl -u mcpx.service -f  # Follow logs
```

Test the endpoints:

```bash
# Static website
curl https://mcpx.lol

# MCP server health check
curl https://mcpx.lol/mcp/health
```

## Updating the Deployment

To deploy updates, just run the script again:

```bash
./deployment/deploy.sh root@mcpx.lol
```

The script will:
- Sync new code
- Restart services
- Preserve your `.env` configuration

## Manual Operations

### View Logs

```bash
# MCP server logs
sudo journalctl -u mcpx.service -f

# nginx logs
sudo tail -f /var/log/nginx/mcpx.lol_access.log
sudo tail -f /var/log/nginx/mcpx.lol_error.log
```

### Service Management

```bash
# Start/stop/restart
sudo systemctl start mcpx.service
sudo systemctl stop mcpx.service
sudo systemctl restart mcpx.service

# Check status
sudo systemctl status mcpx.service

# Enable/disable autostart
sudo systemctl enable mcpx.service
sudo systemctl disable mcpx.service
```

### nginx Management

```bash
# Test configuration
sudo nginx -t

# Reload (no downtime)
sudo systemctl reload nginx

# Restart
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

### SSL Certificate Renewal

Certificates auto-renew via certbot. To manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Troubleshooting

### MCP Server Won't Start

1. Check the logs:
   ```bash
   sudo journalctl -u mcpx.service -n 50
   ```

2. Verify `.env` file exists and has correct permissions:
   ```bash
   ls -la /data/web/mcpx.lol/.env
   sudo cat /data/web/mcpx.lol/.env
   ```

3. Check Python dependencies:
   ```bash
   cd /data/web/mcpx.lol
   sudo -u www-data uv sync
   ```

### nginx Configuration Errors

Test the configuration:

```bash
sudo nginx -t
```

If errors, check:
- SSL certificate paths in `/etc/nginx/sites-available/mcpx.lol`
- Upstream configuration points to correct port (1337)

### Port Already in Use

Check what's using port 1337:

```bash
sudo lsof -i :1337
```

### Permission Issues

Ensure www-data owns the files:

```bash
sudo chown -R www-data:www-data /data/web/mcpx.lol
sudo chmod 600 /data/web/mcpx.lol/.env
```

### Database Issues

If authentication fails, reset the database:

```bash
sudo rm /data/web/mcpx.lol/data/auth.db
sudo systemctl restart mcpx.service
```

## Security Considerations

1. **Environment Variables**: The `.env` file contains secrets. It's set to `chmod 600` and owned by `www-data`.

2. **Authentication**: By default, OAuth is enabled. For testing, you can set `AUTH_MODE=noauth` in `.env` (NOT recommended for production).

3. **Firewall**: Ensure ports 80 and 443 are open:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

4. **SSL**: The deployment uses Let's Encrypt certificates with auto-renewal.

5. **systemd Security**: The service runs with security hardening enabled (see `mcpx.service`).

## File Permissions

```
/data/web/mcpx.lol/
├── .env                   (600, www-data:www-data)
├── public/                (755, www-data:www-data)
├── data/                  (755, www-data:www-data)
│   └── auth.db           (644, www-data:www-data)
├── logs/                  (755, www-data:www-data)
└── mcp_server/           (755, www-data:www-data)
```

## Additional Resources

- [MCPX Main README](../README.md)
- [Authentication Guide](../AUTHENTICATION.md)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)

