# MCPX Deployment Checklist

Use this checklist to ensure a smooth installation.

## Pre-Installation

- [ ] Server running Ubuntu/Debian 20.04+
- [ ] Root or sudo access to the server
- [ ] Git installed on the server (`sudo apt install git`)
- [ ] (Optional) Domain name with DNS pointing to server IP
- [ ] (Optional) Ports 80 and 443 open in firewall

## API Keys Ready

Before you start, gather these API keys:

- [ ] **OpenAI API Key** (required for web search)
  - Get it: https://platform.openai.com/api-keys
  - Format: `sk-proj-...` or `sk-...`

- [ ] **Weather API Key** (optional)
  - Get it: https://openweathermap.org/api
  - Free tier is sufficient

## Installation Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/rossja/mcpx.git
cd mcpx
```
- [ ] Repository cloned successfully
- [ ] Changed into mcpx directory

### Step 2: Run Installation Script
```bash
sudo ./deployment/install.sh
```
- [ ] Script completed without errors
- [ ] All system dependencies installed
- [ ] Files copied to `/data/web/mcpx.lol`
- [ ] nginx configured
- [ ] systemd service created

### Step 3: Configure Environment
```bash
sudo nano /data/web/mcpx.lol/.env
```

Update these values:

- [ ] **JWT_SECRET_KEY** - Generate and paste:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  
- [ ] **OPENAI_API_KEY** - Paste your OpenAI key

- [ ] **WEATHER_API_KEY** - Paste your weather key (or leave default)

- [ ] **MCP_SERVER_NAME** - Update if using a custom domain

- [ ] Saved and exited the editor

### Step 3.5: Verify Configuration (Optional but Recommended)
```bash
sudo ./deployment/verify-config.sh
```
- [ ] All checks passed
- [ ] Any warnings addressed

### Step 4a: SSL Certificate (If Using Domain)
```bash
sudo certbot --nginx -d yourdomain.com
```
- [ ] DNS is pointing to server IP
- [ ] Certificate obtained successfully
- [ ] nginx reloaded with SSL config

### Step 4b: Start the Service
```bash
sudo systemctl start mcpx.service
```
- [ ] Service started without errors
- [ ] Service shows "active (running)"

## Post-Installation Verification

### Check Service Status
```bash
sudo systemctl status mcpx.service
```
- [ ] Status shows "active (running)"
- [ ] No error messages in output

### Check Logs
```bash
sudo journalctl -u mcpx.service -n 50
```
- [ ] No error messages in logs
- [ ] Server started successfully

### Test Health Endpoint
```bash
curl http://localhost:1337/health
```
Expected response: `{"status":"healthy","service":"mcpx"}`
- [ ] Health check returns 200 OK
- [ ] JSON response is correct

### Test Through nginx
```bash
# With SSL
curl https://yourdomain.com/mcpx/health

# Or without SSL
curl http://yourdomain.com/mcpx/health
```
- [ ] nginx proxy working
- [ ] Health check accessible externally

### Test Static Website
```bash
# With SSL
curl https://yourdomain.com/

# Or without SSL
curl http://yourdomain.com/
```
- [ ] Returns HTML content
- [ ] No 502/504 errors

### Test OAuth Login Page
Visit in browser: `https://yourdomain.com/oauth/authorize?response_type=code&client_id=mcpx-client&redirect_uri=http://localhost&state=test`

- [ ] Login page displays
- [ ] No SSL errors
- [ ] Can see login form

### Test Authentication
Default credentials:
- Username: `mcpuser`
- Password: `OMG!letmein`

- [ ] Can log in with default credentials
- [ ] Gets redirected properly

## Security Checklist

- [ ] `.env` file has 600 permissions
- [ ] `.env` file owned by www-data
- [ ] JWT_SECRET_KEY is unique and secure (not default value)
- [ ] Firewall configured (if using UFW):
  ```bash
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```
- [ ] SSH key authentication enabled (not password)
- [ ] Root login disabled (if not needed)
- [ ] SSL certificate is valid and auto-renewal is working

## Optional Production Hardening

- [ ] Changed default OAuth username/password in database
- [ ] Set up monitoring/alerting
- [ ] Configured log rotation
- [ ] Set up automated backups of `/data/web/mcpx.lol/data/`
- [ ] Reviewed and adjusted rate limits if needed
- [ ] Set up fail2ban or similar intrusion prevention
- [ ] Documented your customizations

## Troubleshooting Resources

If anything goes wrong, consult:

1. **Service logs**: `sudo journalctl -u mcpx.service -f`
2. **nginx logs**: `sudo tail -f /var/log/nginx/error.log`
3. **Installation guide**: [../INSTALL.md](../INSTALL.md)
4. **Getting started**: [../GETTING_STARTED.md](../GETTING_STARTED.md)
5. **Deployment guide**: [README.md](README.md)
6. **Quick reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

## Success! 🎉

- [ ] All checks passed
- [ ] Service is running
- [ ] Accessible from the internet
- [ ] Authentication working
- [ ] Tools responding correctly

Your MCPX server is now ready for use!

## Next Steps

- Connect an MCP client to test the tools
- Set up monitoring and alerting
- Review the authentication documentation
- Plan your adversarial test scenarios
- Join the community and share your experience

---

Installation Date: _______________

Domain: _______________

Server IP: _______________

Notes:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

