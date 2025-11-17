# MCPX Deployment Quick Reference

## 🚀 Deploy Everything

```bash
./deployment/deploy.sh root@mcpx.lol
```

## 📝 Configure API Keys

```bash
ssh root@mcpx.lol "sudo nano /data/web/mcpx.lol/.env"
```

Required values:
- `JWT_SECRET_KEY` - Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `OPENAI_API_KEY` - Your OpenAI key
- `WEATHER_API_KEY` - Your weather key (optional)

## 🔄 Restart After Config Changes

```bash
ssh root@mcpx.lol "sudo systemctl restart mcpx.service"
```

## 🔍 Check Status

```bash
# Service status
ssh root@mcpx.lol "sudo systemctl status mcpx.service"

# Live logs
ssh root@mcpx.lol "sudo journalctl -u mcpx.service -f"

# nginx status
ssh root@mcpx.lol "sudo systemctl status nginx"
```

## 🧪 Test Endpoints

```bash
# Static site
curl https://mcpx.lol

# MCP server
curl -X POST https://mcpx.lol/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## 📁 File Locations

| What | Where |
|------|-------|
| Static site | `/data/web/mcpx.lol/public/` |
| MCP server code | `/data/web/mcpx.lol/` |
| Config file | `/data/web/mcpx.lol/.env` |
| Auth database | `/data/web/mcpx.lol/data/auth.db` |
| nginx config | `/etc/nginx/sites-available/mcpx.lol` |
| systemd service | `/etc/systemd/system/mcpx.service` |
| SSL certs | `/etc/letsencrypt/live/mcpx.lol/` |

## 🔧 Common Commands

```bash
# Restart services
ssh root@mcpx.lol "sudo systemctl restart mcpx.service"
ssh root@mcpx.lol "sudo systemctl reload nginx"

# View logs
ssh root@mcpx.lol "sudo journalctl -u mcpx.service -n 100"
ssh root@mcpx.lol "sudo tail -f /var/log/nginx/mcpx.lol_error.log"

# Check what's on port 1337
ssh root@mcpx.lol "sudo lsof -i :1337"

# Test nginx config
ssh root@mcpx.lol "sudo nginx -t"

# Renew SSL
ssh root@mcpx.lol "sudo certbot renew"
```

## 🏗️ Architecture

```
https://mcpx.lol/        → nginx → /data/web/mcpx.lol/public/ (static)
https://mcpx.lol/mcp    → nginx → localhost:1337 (MCP server)
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Service won't start | Check logs: `sudo journalctl -u mcpx.service -n 50` |
| 502 Bad Gateway | MCP server down, check: `sudo systemctl status mcpx.service` |
| Permission errors | Fix ownership: `sudo chown -R www-data:www-data /data/web/mcpx.lol` |
| Port already in use | Find process: `sudo lsof -i :1337` |
| nginx won't start | Test config: `sudo nginx -t` |

## 📚 More Info

- **Installation guide**: [../INSTALL.md](../INSTALL.md)
- **Getting started**: [../GETTING_STARTED.md](../GETTING_STARTED.md)
- **Full deployment guide**: [README.md](README.md)
- **Checklist**: [CHECKLIST.md](CHECKLIST.md)

