# 🤖 VPS Bot Manager v2.0

Telegram bot for hosting and managing Node.js, Python, and WhatsApp bots on your VPS.

## Features

- **Node.js Bot Hosting** - Deploy and manage Node.js bots
- **Python Bot Hosting** - Deploy and manage Python bots  
- **WhatsApp Bot Hosting** - Deploy Baileys-based WhatsApp bots with pair code support
- **Package Manager** - Install npm/pip packages directly from Telegram
- **Premium System** - Lock/unlock bot access with premium users
- **VPS Status** - Real-time CPU, RAM, Disk monitoring
- **PM2 Integration** - Automatic process management

## Setup

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Edit `config.py`:
   - Set your `BOT_TOKEN` from @BotFather
   - Add your Telegram user ID to `ADMIN_IDS`

3. Run the bot:
```bash
python3 main.py
```

## Commands

- `/start` - Start the bot manager
- `/menu` - Show main menu
- `/unlock on/off` - Toggle access control
- `/addprem <user_id>` - Add premium user
- `/delprem <user_id>` - Remove premium user
- `/premusers` - List premium users

## WhatsApp Bot Setup

1. Deploy your WhatsApp bot zip (Baileys-based)
2. Set password or skip
3. Enter phone number with country code
4. Check logs for pair code
5. Enter pair code in WhatsApp Linked Devices

## Package Manager

- Install npm packages: `npm install <package>` from bot menu
- Install pip packages: `pip install <package>` from bot menu
- View installed packages anytime

## Requirements

- Python 3.8+
- Node.js & npm (for Node.js/WhatsApp bots)
- PM2 (`npm install -g pm2`)
- systemd (for Python bot fallback)
