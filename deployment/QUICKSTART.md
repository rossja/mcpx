# MCPX Quick Start

Get MCPX running in production with these 4 simple steps!

## The 4 Steps

### 1️⃣ Clone the Repository

On your server:

```bash
git clone https://github.com/rossja/mcpx.git
cd mcpx
```

### 2️⃣ Run the Installation Script

```bash
sudo ./deployment/install.sh
```

This takes 2-5 minutes and installs everything automatically.

### 3️⃣ Edit the Configuration

```bash
sudo nano /data/web/mcpx.lol/.env
```

**You must update these 3 values:**

```env
# Generate this:
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-generated-key-here

# Your OpenAI API key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-api-key

# Optional: Your weather API key
WEATHER_API_KEY=your-weather-key-or-leave-default
```

Save and exit (Ctrl+X, Y, Enter).

### 4️⃣ Start the Service

**If you have a domain with DNS configured:**

```bash
sudo certbot --nginx -d yourdomain.com
sudo systemctl start mcpx.service
```

**If you're testing without a domain:**

```bash
sudo systemctl start mcpx.service
```

### ✅ Verify It's Working

```bash
# Check service status
sudo systemctl status mcpx.service

# Test the health endpoint
curl http://localhost:1337/health
```

You should see: `{"status":"healthy","service":"mcpx"}`

## That's It!

Your MCPX server is now running at:
- **Static site**: `https://yourdomain.com/` (or `http://your-server-ip/`)
- **MCP API**: `https://yourdomain.com/mcp/` (or `http://your-server-ip/mcp/`)

## Common Next Steps

### View Logs
```bash
sudo journalctl -u mcpx.service -f
```

### Restart After Config Changes
```bash
sudo systemctl restart mcpx.service
```

### Test OAuth Authentication

Default credentials:
- Username: `mcpuser`
- Password: `OMG!letmein`

Visit: `https://yourdomain.com/oauth/authorize`

## Need More Help?

- **Full installation guide**: [../INSTALL.md](../INSTALL.md)
- **Getting started**: [../GETTING_STARTED.md](../GETTING_STARTED.md)
- **Detailed deployment docs**: [README.md](README.md)
- **Command reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

## Troubleshooting

### Service won't start?
```bash
sudo journalctl -u mcpx.service -n 50
```

### Can't connect from outside?
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Need to reset the database?
```bash
sudo rm /data/web/mcpx.lol/data/auth.db
sudo systemctl restart mcpx.service
```

