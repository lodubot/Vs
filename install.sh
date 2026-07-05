#!/bin/bash

echo "🤖 VPS Bot Manager v2.0 - Installer"
echo "===================================="

# 1. Update system
echo "📦 Updating system..."
apt-get update -y && apt-get upgrade -y

# 2. Install Python and pip
echo "🐍 Installing Python..."
apt-get install -y python3 python3-pip python3-venv

# 3. Install Node.js 24 (Proper way for apt)
echo "🟢 Installing Node.js 24..."
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
apt-get install -y nodejs

# 4. Install PM2 (using sudo to avoid permission errors)
echo "⚙️ Installing PM2..."
npm install -g pm2

# 5. Install Python dependencies
echo "📦 Installing Python packages..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --break-system-packages
else
    echo "⚠️ requirements.txt not found, skipping..."
fi

echo ""
echo "✅ Installation complete!"
echo "Node version: $(node -v)"
echo "NPM version: $(npm -v)"
echo ""
echo "Next steps:"
echo "1. Edit config.py with your BOT_TOKEN and ADMIN_IDS"
echo "2. Run: python3 main.py"
echo ""
