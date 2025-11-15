# MCPX Installation Guide

Get MCPX up and running in 4 simple steps!

## Prerequisites

- A server running Ubuntu/Debian Linux (20.04+ recommended)
- Root or sudo access
- A domain name pointing to your server (optional but recommended for SSL)

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/rossja/mcpx.git
cd mcpx
```

### Step 2: Run the Installation Script

```bash
sudo ./deployment/install.sh
```

This script will automatically:
- ✅ Install all system dependencies (Python 3.12, nginx, certbot, uv)
- ✅ Create the deployment directory at `/data/web/mcpx.lol`
- ✅ Copy all necessary files
- ✅ Install Python dependencies
- ✅ Configure nginx and systemd
- ✅ Create a template `.env` file for you to edit

The installation takes 2-5 minutes depending on your server.

### Step 3: Edit the Environment File

The installation creates a `.env` file at `/data/web/mcpx.lol/.env` with default values. You **must** edit this file with your own configuration:

```bash
sudo nano /data/web/mcpx.lol/.env
```

**Required changes:**

1. **JWT_SECRET_KEY** - Generate a secure random key:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Copy the output and paste it as the value for `JWT_SECRET_KEY`

2. **OPENAI_API_KEY** - Your OpenAI API key (required for web search tool)
   - Get yours at: https://platform.openai.com/api-keys
   - Format: `sk-...`

3. **WEATHER_API_KEY** - Your OpenWeatherMap API key (optional)
   - Get yours at: https://openweathermap.org/api
   - Leave as default if you don't need weather lookups

**Example `.env` file:**
```env
JWT_SECRET_KEY=Kq8Pz9Xw2Yc5Vb7Nm4Lh6Jd3Fg1Ts0Rp
OPENAI_API_KEY=sk-proj-abc123xyz...
WEATHER_API_KEY=your-weather-api-key-here
```

Save and exit (Ctrl+X, then Y, then Enter in nano).

**Optional but recommended:** Verify your configuration is correct:

```bash
sudo ./deployment/verify-config.sh
```

This will check that all required settings are in place before you start the service.

### Step 4: Start the Service

#### Option A: Using a Domain with SSL (Recommended)

If you have a domain pointing to your server:

```bash
# First, obtain SSL certificate
sudo certbot --nginx -d yourdomain.com

# Then start the service
sudo systemctl start mcpx.service

# Check it's running
sudo systemctl status mcpx.service
```

Test your deployment:
```bash
curl https://yourdomain.com/mcpx/health
```

#### Option B: HTTP Only (Development/Testing)

If you're just testing or don't have a domain:

```bash
# Start the service
sudo systemctl start mcpx.service

# Check it's running
sudo systemctl status mcpx.service
```

Test your deployment:
```bash
curl http://localhost/mcpx/health
curl http://your-server-ip/mcpx/health
```

## That's It! 🎉

Your MCPX server is now running:
- **Static site**: Available at your domain root
- **MCP server**: Available at `/mcpx` path
- **Service management**: Automatically starts on boot

## Useful Commands

### View Logs
```bash
# Follow service logs in real-time
sudo journalctl -u mcpx.service -f

# View last 50 lines
sudo journalctl -u mcpx.service -n 50
```

### Manage the Service
```bash
# Start/stop/restart
sudo systemctl start mcpx.service
sudo systemctl stop mcpx.service
sudo systemctl restart mcpx.service

# Check status
sudo systemctl status mcpx.service

# Enable/disable autostart on boot
sudo systemctl enable mcpx.service
sudo systemctl disable mcpx.service
```

### Update After Editing .env
Whenever you edit the `.env` file, restart the service:
```bash
sudo systemctl restart mcpx.service
```

### Test the MCP Server
```bash
# Health check
curl http://localhost:1337/health

# Or through nginx
curl https://yourdomain.com/mcpx/health
```

## Troubleshooting

### Service Won't Start

Check the logs:
```bash
sudo journalctl -u mcpx.service -n 50
```

Common issues:
- Missing or invalid API keys in `.env`
- Port 1337 already in use
- File permission issues

### Authentication Not Working

Check that you've set a secure `JWT_SECRET_KEY` in the `.env` file. The default credentials are:
- Username: `mcpuser`
- Password: `OMG!letmein`

### Can't Access from Outside

1. Check firewall settings:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw status
   ```

2. Verify nginx is running:
   ```bash
   sudo systemctl status nginx
   ```

3. Check nginx configuration:
   ```bash
   sudo nginx -t
   ```

## Updating MCPX

To update to the latest version:

```bash
cd /path/to/your/mcpx/repo
git pull
sudo ./deployment/install.sh
sudo systemctl restart mcpx.service
```

Your `.env` file and data will be preserved.

## Development vs Production

This installation guide is for **production deployment**. If you want to run MCPX locally for development:

1. Clone the repo
2. Create a `.env` file from `env.example`:
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```
3. Install dependencies:
   ```bash
   uv sync
   ```
4. Run the server:
   ```bash
   uv run python -m mcp_server.main
   ```

See the main [README.md](README.md) for full development documentation.

## Getting Help

- **Full documentation**: See [README.md](README.md)
- **Deployment details**: See [deployment/README.md](deployment/README.md)
- **Authentication guide**: See [AUTHENTICATION.md](AUTHENTICATION.md)
- **Issues**: Open an issue on GitHub

## Next Steps

Once your server is running, you can:
- Test the 5 built-in tools (echo, weather, web_search, ip_lookup, request_info)
- Connect MCP clients to test authentication flows
- Explore the OAuth 2.0 endpoints
- Build custom adversarial test scenarios

Happy testing! 🚀

