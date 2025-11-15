# Getting Started with MCPX

Welcome! Choose your path based on what you want to do:

## 🚀 I Want to Deploy MCPX to Production

**→ [INSTALL.md](INSTALL.md)** — Simple 4-step installation guide (recommended)

Takes about 10 minutes:
```bash
git clone https://github.com/rossja/mcpx.git
cd mcpx
sudo ./deployment/install.sh
sudo nano /data/web/mcpx.lol/.env  # Add your API keys
sudo systemctl start mcpx.service
```

## 💻 I Want to Develop Locally

**→ [README.md](README.md#local-development-setup)** — Local development setup

```bash
git clone https://github.com/rossja/mcpx.git
cd mcpx
uv sync
cp env.example .env
# Edit .env with your API keys
uv run python -m mcp_server.main
```

## 📖 I Want to Understand What MCPX Is

**→ [README.md](README.md)** — Complete project documentation

MCPX is an adversarial MCP server for AI red-teaming - a controlled environment for testing how AI systems behave when connected to external tools.

## 🔧 I Need Deployment Details

Choose based on your needs:

- **[INSTALL.md](INSTALL.md)** — Simple 4-step guide (start here!)
- **[deployment/QUICKSTART.md](deployment/QUICKSTART.md)** — Ultra-condensed version
- **[deployment/README.md](deployment/README.md)** — Detailed guide with architecture
- **[deployment/CHECKLIST.md](deployment/CHECKLIST.md)** — Step-by-step checklist
- **[deployment/QUICK_REFERENCE.md](deployment/QUICK_REFERENCE.md)** — Command reference

## 🔐 I Need Help With Authentication

**→ [AUTHENTICATION.md](AUTHENTICATION.md)** — Complete authentication guide

Covers OAuth 2.0 setup, token management, and security best practices.

## ❓ I Need Help / Something Isn't Working

1. Check **[INSTALL.md](INSTALL.md)** troubleshooting section
2. Run verification: `sudo ./deployment/verify-config.sh`
3. Check logs: `sudo journalctl -u mcpx.service -f`
4. Review **[deployment/README.md](deployment/README.md)** troubleshooting
5. Open an issue on GitHub

## Need API Keys?

Get your API keys before installation:
- **OpenAI**: https://platform.openai.com/api-keys (required for web search)
- **Weather**: https://openweathermap.org/api (optional)

---

**New to MCPX?** Start with [INSTALL.md](INSTALL.md) for production deployment or [README.md](README.md) for an overview.

