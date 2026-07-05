#!/usr/bin/env python3
"""
🤖 VPS BOT HOSTING MANAGER - Telegram Bot v2.0
Added: WhatsApp bot hosting, Package Manager, Pair Code, Password protection

BOT MAD BY @Hx5x5x5x
TELEGRAM CHANNEL: https://t.me/Dev_Null_X_NODE_JS
YOUTUBE CHANNEL: https://www.youtube.com/@Dev_Null_X
"""

import os
import sys
import zipfile
import shutil
import subprocess
import json
import time
import asyncio
import psutil
import re
from pathlib import Path
from datetime import datetime, timedelta

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.error import BadRequest

from config import (
    BOT_TOKEN, ADMIN_IDS, HOSTED_BOTS_DIR, 
    LOGS_DIR, MAX_BOTS, MAX_ZIP_SIZE_MB,
    AUTO_START_AFTER_DEPLOY
)

os.makedirs(HOSTED_BOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ============ CREDITS CONFIG ============
CREDITS = {
    "dev": "@Hx5x5x5x",
    "telegram_channel": "https://t.me/Dev_Null_X_NODE_JS",
    "youtube_channel": "https://www.youtube.com/@Dev_Null_X",
    "home_video": "https://files.catbox.moe/q6civ6.mp4"
}

class S:
    BOT = "🤖"
    WHATSAPP = "💬"
    START = "🟢"
    STOP = "🔴"
    RESTART = "🔄"
    LOGS = "📋"
    STATUS = "📊"
    DEPLOY = "📦"
    DELETE = "🗑️"
    CPU = "💻"
    RAM = "🧠"
    DISK = "💾"
    UPTIME = "⏱️"
    ERROR = "❌"
    SUCCESS = "✅"
    WARNING = "⚠️"
    LOADING = "⏳"
    ARROW = "➡️"
    BACK = "🔙"
    HOME = "🏠"
    INFO = "ℹ️"
    SETTINGS = "⚙️"
    REFRESH = "🔄"
    USER = "👤"
    TIME = "🕐"
    FILE = "📁"
    LOCK = "🔒"
    UNLOCK = "🔓"
    CROWN = "👑"
    PACKAGE = "📦"
    DOWNLOAD = "⬇️"
    PHONE = "📱"
    KEY = "🔑"
    SKIP = "⏭️"
    INSTALL = "🔧"
    NODEJS = "🟢"
    PYTHON = "🐍"
    NPM = "📦"
    PIP = "🐍"
    VIDEO = "🎬"
    DEV = "👨‍💻"
    TG = "📢"
    YT = "▶️"
    HEART = "❤️"


# ============ IN-MEMORY SESSION (NO FREEZE) ============
class UserSession:
    """In-memory session storage - prevents bot freeze"""
    _sessions = {}

    @classmethod
    def get(cls, user_id, key, default=None):
        return cls._sessions.get(user_id, {}).get(key, default)

    @classmethod
    def set(cls, user_id, key, value):
        if user_id not in cls._sessions:
            cls._sessions[user_id] = {}
        cls._sessions[user_id][key] = value

    @classmethod
    def delete(cls, user_id, key):
        if user_id in cls._sessions and key in cls._sessions[user_id]:
            del cls._sessions[user_id][key]

class PremiumManager:
    PREMIUM_FILE = f"{HOSTED_BOTS_DIR}/.premium_users.json"
    UNLOCK_FILE = f"{HOSTED_BOTS_DIR}/.unlock_state.json"

    @classmethod
    def load_premium(cls):
        if os.path.exists(cls.PREMIUM_FILE):
            try:
                with open(cls.PREMIUM_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @classmethod
    def save_premium(cls, data):
        with open(cls.PREMIUM_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_unlock(cls):
        if os.path.exists(cls.UNLOCK_FILE):
            try:
                with open(cls.UNLOCK_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {"unlocked": False}
        return {"unlocked": False}

    @classmethod
    def save_unlock(cls, data):
        with open(cls.UNLOCK_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def is_unlocked(cls):
        state = cls.load_unlock()
        return state.get("unlocked", False)

    @classmethod
    def set_unlock(cls, unlocked: bool):
        cls.save_unlock({"unlocked": unlocked})

    @classmethod
    def is_premium(cls, user_id: int):
        data = cls.load_premium()
        return str(user_id) in data

    @classmethod
    def add_premium(cls, user_id: int, added_by: int = None):
        data = cls.load_premium()
        data[str(user_id)] = {
            "added_at": datetime.now().isoformat(),
            "added_by": added_by
        }
        cls.save_premium(data)

    @classmethod
    def remove_premium(cls, user_id: int):
        data = cls.load_premium()
        if str(user_id) in data:
            del data[str(user_id)]
            cls.save_premium(data)
            return True
        return False

    @classmethod
    def get_premium_list(cls):
        return cls.load_premium()

    @classmethod
    def can_use_bot(cls, user_id: int):
        return True  # FREE FOR ALL - Everyone can use

def log_error(msg):
    log_file = f"{LOGS_DIR}/errors.log"
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def log_deploy(msg, bot_name="general"):
    log_file = f"{LOGS_DIR}/deploy_{bot_name}.log"
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def safe_execute(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            elif "message to edit not found" in str(e):
                pass
            else:
                await send_error(update, f"BadRequest: {str(e)}")
        except Exception as e:
            await send_error(update, str(e))
            log_error(f"Error in {func.__name__}: {str(e)}")
    return wrapper

async def send_error(update, msg):
    error_msg = f"{S.ERROR} **Error:** `{msg[:200]}`"
    if update.callback_query:
        try:
            await update.callback_query.answer("Error!", show_alert=True)
        except:
            pass
        try:
            await update.callback_query.edit_message_text(
                error_msg, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]])
            )
        except:
            pass
    elif update.message:
        await update.message.reply_text(error_msg, parse_mode="Markdown")

class SystemMonitor:
    @staticmethod
    def get_stats():
        cpu = psutil.cpu_percent(interval=0)  # Non-blocking read
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = time.time() - psutil.boot_time()
        return {
            'cpu': cpu, 'ram_used': ram.used / (1024**3),
            'ram_total': ram.total / (1024**3), 'ram_percent': ram.percent,
            'disk_used': disk.used / (1024**3), 'disk_total': disk.total / (1024**3),
            'disk_percent': disk.percent, 'uptime': uptime
        }
    @staticmethod
    def format_uptime(seconds):
        td = timedelta(seconds=int(seconds))
        days, hours, minutes = td.days, td.seconds // 3600, (td.seconds % 3600) // 60
        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        return " ".join(parts) if parts else "0m"

class HostedBot:
    def __init__(self, bot_id, name, bot_dir, bot_type, user_id=None):
        self.bot_id = bot_id
        self.name = name
        self.bot_dir = str(bot_dir)
        self.bot_type = bot_type
        self.user_id = user_id
        self.service_name = f"hosted-bot-{bot_id}"

    def is_running(self):
        try:
            result = subprocess.run(
                ["pm2", "jlist"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout:
                try:
                    processes = json.loads(result.stdout)
                    for proc in processes:
                        if proc.get("name") == self.service_name:
                            status = proc.get("pm2_env", {}).get("status")
                            return status == "online"
                except:
                    pass

            if self.bot_type in ["python", "whatsapp"]:
                result = subprocess.run(
                    ["systemctl", "is-active", self.service_name],
                    capture_output=True, text=True, timeout=5
                )
                return result.stdout.strip() == "active"
            return False
        except Exception as e:
            log_error(f"is_running check failed: {e}")
            return False

    def get_logs(self, lines=30):
        try:
            result = subprocess.run(
                ["pm2", "logs", self.service_name, "--lines", str(lines), "--nostream"],
                capture_output=True, text=True, timeout=15
            )
            if result.stdout and result.stdout.strip():
                return result.stdout[-3500:]

            for log_suffix in ["-out.log", "-error.log", ".log"]:
                log_file = f"/root/.pm2/logs/{self.service_name}{log_suffix}"
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                        return content[-3500:] if content else "No logs yet"

            if self.bot_type in ["python", "whatsapp"]:
                result = subprocess.run(
                    ["journalctl", "-u", self.service_name, "-n", str(lines), "--no-pager"],
                    capture_output=True, text=True, timeout=10
                )
                if result.stdout and result.stdout.strip():
                    return result.stdout[-3500:]

            return "No logs available. Bot may not have started yet.\nCheck if credentials are set correctly."
        except Exception as e:
            return f"Error reading logs: {str(e)}"

    def start(self):
        try:
            if self.bot_type == "nodejs":
                pkg_path = os.path.join(self.bot_dir, "package.json")

                # Check if package.json has start script - use npm start
                use_npm_start = False
                if os.path.exists(pkg_path):
                    try:
                        with open(pkg_path) as f:
                            pkg = json.load(f)
                            if pkg.get("scripts", {}).get("start"):
                                use_npm_start = True
                    except:
                        pass

                if use_npm_start:
                    result = subprocess.run(
                        ["pm2", "start", "npm", "--name", self.service_name,
                         "--", "start"],
                        capture_output=True, text=True, timeout=30, cwd=self.bot_dir
                    )
                else:
                    main_file = "index.js"
                    if os.path.exists(pkg_path):
                        with open(pkg_path) as f:
                            pkg = json.load(f)
                            main_file = pkg.get("main", "index.js")

                    target = os.path.join(self.bot_dir, main_file)
                    if not os.path.exists(target):
                        for f in os.listdir(self.bot_dir):
                            if f.endswith('.js'):
                                target = os.path.join(self.bot_dir, f)
                                break

                    result = subprocess.run(
                        ["pm2", "start", target, "--name", self.service_name],
                        capture_output=True, text=True, timeout=30, cwd=self.bot_dir
                    )
                if result.returncode != 0:
                    log_error(f"PM2 start failed for {self.name}: {result.stderr}")
                subprocess.run(["pm2", "save"], capture_output=True, timeout=10)
                return result.returncode == 0

            elif self.bot_type == "whatsapp":
                # Check if package.json has start script, use npm start
                pkg_path = os.path.join(self.bot_dir, "package.json")
                use_npm_start = False
                if os.path.exists(pkg_path):
                    try:
                        with open(pkg_path) as f:
                            pkg = json.load(f)
                            if pkg.get("scripts", {}).get("start"):
                                use_npm_start = True
                    except:
                        pass

                if use_npm_start:
                    result = subprocess.run(
                        ["pm2", "start", "npm", "--name", self.service_name,
                         "--", "start"],
                        capture_output=True, text=True, timeout=30, cwd=self.bot_dir
                    )
                else:
                    main_file = "index.js"
                    for mf in ["index.js", "main.js", "bot.js", "app.js"]:
                        if os.path.exists(f"{self.bot_dir}/{mf}"):
                            main_file = mf
                            break
                    target = os.path.join(self.bot_dir, main_file)

                    result = subprocess.run(
                        ["pm2", "start", target, "--name", self.service_name, 
                         "--cwd", self.bot_dir],
                        capture_output=True, text=True, timeout=30
                    )
                if result.returncode != 0:
                    log_error(f"PM2 start failed for WhatsApp {self.name}: {result.stderr}")
                subprocess.run(["pm2", "save"], capture_output=True, timeout=10)
                return result.returncode == 0

            else:
                eco_path = f"{self.bot_dir}/ecosystem.json"
                if os.path.exists(eco_path):
                    result = subprocess.run(
                        ["pm2", "start", eco_path],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        subprocess.run(["pm2", "save"], capture_output=True, timeout=10)
                        return True
                    else:
                        log_error(f"PM2 ecosystem start failed: {result.stderr}")

                main_file = "main.py"
                for mf in ["main.py", "bot.py", "app.py", "run.py"]:
                    if os.path.exists(f"{self.bot_dir}/{mf}"):
                        main_file = mf
                        break
                target = os.path.join(self.bot_dir, main_file)

                result = subprocess.run(
                    ["pm2", "start", target, "--name", self.service_name, 
                     "--interpreter", "python3", "--cwd", self.bot_dir],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    log_error(f"PM2 direct start failed for {self.name}: {result.stderr}")

                subprocess.run(["pm2", "save"], capture_output=True, timeout=10)

                subprocess.run(
                    ["systemctl", "start", self.service_name],
                    capture_output=True, text=True, timeout=30
                )
                return True
        except Exception as e:
            log_error(f"Start failed for {self.name}: {e}")
            return False

    def stop(self):
        try:
            subprocess.run(
                ["pm2", "stop", self.service_name],
                capture_output=True, text=True, timeout=30
            )
            if self.bot_type in ["python", "whatsapp"]:
                subprocess.run(
                    ["systemctl", "stop", self.service_name],
                    capture_output=True, text=True, timeout=30
                )
            return True
        except Exception as e:
            log_error(f"Stop failed for {self.name}: {e}")
            return False

    def restart(self):
        try:
            subprocess.run(
                ["pm2", "restart", self.service_name],
                capture_output=True, text=True, timeout=30
            )
            if self.bot_type in ["python", "whatsapp"]:
                subprocess.run(
                    ["systemctl", "restart", self.service_name],
                    capture_output=True, text=True, timeout=30
                )
            return True
        except Exception as e:
            log_error(f"Restart failed for {self.name}: {e}")
            return False

    def install_npm_package(self, package_name):
        try:
            result = subprocess.run(
                ["npm", "install", package_name],
                cwd=self.bot_dir, capture_output=True, text=True, timeout=300
            )
            log_deploy(f"npm install {package_name}: rc={result.returncode}", self.name)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def install_pip_package(self, package_name):
        try:
            result = subprocess.run(
                ["pip3", "install", package_name],
                cwd=self.bot_dir, capture_output=True, text=True, timeout=300
            )
            log_deploy(f"pip install {package_name}: rc={result.returncode}", self.name)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def get_installed_packages(self):
        packages = {}
        if self.bot_type in ["nodejs", "whatsapp"]:
            pkg_json = os.path.join(self.bot_dir, "package.json")
            if os.path.exists(pkg_json):
                try:
                    with open(pkg_json) as f:
                        pkg = json.load(f)
                        packages['dependencies'] = pkg.get('dependencies', {})
                        packages['devDependencies'] = pkg.get('devDependencies', {})
                except:
                    pass
        elif self.bot_type == "python":
            req_file = os.path.join(self.bot_dir, "requirements.txt")
            if os.path.exists(req_file):
                try:
                    with open(req_file) as f:
                        packages['requirements'] = [l.strip() for l in f if l.strip() and not l.startswith('#')]
                except:
                    pass
        return packages

class BotDatabase:
    DB_FILE = f"{HOSTED_BOTS_DIR}/.bot_db.json"

    @classmethod
    def load(cls):
        if os.path.exists(cls.DB_FILE):
            try:
                with open(cls.DB_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @classmethod
    def save(cls, data):
        with open(cls.DB_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    @classmethod
    def get_all_bots(cls):
        return cls.load()

    @classmethod
    def get_user_bots(cls, user_id):
        data = cls.load()
        if user_id in ADMIN_IDS:
            return data
        # USER ISOLATION: Each user sees ONLY their own bots
        return {k: v for k, v in data.items() if v.get('user_id') == user_id}

    @classmethod
    def add_bot(cls, bot_id, name, bot_dir, bot_type, user_id=None, extra_data=None):
        data = cls.load()
        bot_data = {
            'name': name, 'dir': bot_dir, 'type': bot_type,
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        if extra_data:
            bot_data.update(extra_data)
        data[bot_id] = bot_data
        cls.save(data)

    @classmethod
    def remove_bot(cls, bot_id):
        data = cls.load()
        if bot_id in data:
            del data[bot_id]
            cls.save(data)

    @classmethod
    def update_bot(cls, bot_id, key, value):
        data = cls.load()
        if bot_id in data:
            data[bot_id][key] = value
            cls.save(data)

class KB:
    @staticmethod
    def main():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.BOT} My Bots", callback_data="my_bots")],
            [InlineKeyboardButton(f"{S.DEPLOY} Deploy New Bot", callback_data="deploy")],
            [InlineKeyboardButton(f"{S.PACKAGE} Package Manager", callback_data="pkg_manager")],
            [InlineKeyboardButton(f"{S.STATUS} VPS Status", callback_data="vps_status")],
            [InlineKeyboardButton(f"{S.SETTINGS} Settings", callback_data="settings")]
        ])

    @staticmethod
    def credits():
        """Credit buttons for home page"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.DEV} BOT MAD BY @Hx5x5x5x", url="https://t.me/Hx5x5x5x")],
            [InlineKeyboardButton(f"{S.TG} Telegram Channel", url="https://t.me/Dev_Null_X_NODE_JS")],
            [InlineKeyboardButton(f"{S.YT} YouTube Channel", url="https://www.youtube.com/@Dev_Null_X")],
            [InlineKeyboardButton(f"{S.HOME} Enter Dashboard", callback_data="enter_menu")]
        ])

    @staticmethod
    def bot_actions(bot_id, is_running, bot_type):
        keyboard = []
        if is_running:
            keyboard.append([
                InlineKeyboardButton(f"{S.STOP} Stop", callback_data=f"stop:{bot_id}"),
                InlineKeyboardButton(f"{S.RESTART} Restart", callback_data=f"restart:{bot_id}")
            ])
        else:
            keyboard.append([InlineKeyboardButton(f"{S.START} Start", callback_data=f"start:{bot_id}")])

        keyboard.append([
            InlineKeyboardButton(f"{S.LOGS} View Logs", callback_data=f"logs:{bot_id}"),
            InlineKeyboardButton(f"{S.STATUS} Bot Status", callback_data=f"bot_status:{bot_id}")
        ])

        keyboard.append([
            InlineKeyboardButton(f"{S.PACKAGE} Packages", callback_data=f"packages:{bot_id}"),
            InlineKeyboardButton(f"{S.INSTALL} Install Pkg", callback_data=f"install_pkg:{bot_id}")
        ])

        keyboard.append([InlineKeyboardButton(f"{S.DELETE} Delete Bot", callback_data=f"delete:{bot_id}")])
        keyboard.append([InlineKeyboardButton(f"{S.BACK} Back", callback_data="my_bots")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back(callback="menu"):
        return InlineKeyboardMarkup([[InlineKeyboardButton(f"{S.BACK} Back", callback_data=callback)]])

    @staticmethod
    def confirm_delete(bot_id):
        return InlineKeyboardMarkup([[
            InlineKeyboardButton(f"No, Cancel", callback_data=f"bot_detail:{bot_id}"),
            InlineKeyboardButton(f"Yes, Delete", callback_data=f"confirm_delete:{bot_id}")
        ]])

    @staticmethod
    def deploy_type():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.NODEJS} Node.js Bot", callback_data="deploy_type:nodejs")],
            [InlineKeyboardButton(f"{S.PYTHON} Python Bot", callback_data="deploy_type:python")],
            [InlineKeyboardButton(f"{S.WHATSAPP} WhatsApp Bot (Baileys)", callback_data="deploy_type:whatsapp")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
        ])

    @staticmethod
    def premium_menu():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.CROWN} Add Premium User", callback_data="premium_add")],
            [InlineKeyboardButton(f"{S.USER} Remove Premium User", callback_data="premium_remove")],
            [InlineKeyboardButton(f"{S.INFO} List Premium Users", callback_data="premium_list")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="settings")]
        ])

    @staticmethod
    def whatsapp_setup(bot_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.KEY} Set Password", callback_data=f"wa_password:{bot_id}")],
            [InlineKeyboardButton(f"{S.SKIP} Skip Password", callback_data=f"wa_skip_pass:{bot_id}")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="my_bots")]
        ])

    @staticmethod
    def package_manager(bot_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.NPM} Install npm package", callback_data=f"npm_install:{bot_id}")],
            [InlineKeyboardButton(f"{S.PIP} Install pip package", callback_data=f"pip_install:{bot_id}")],
            [InlineKeyboardButton(f"{S.INFO} View Installed", callback_data=f"view_packages:{bot_id}")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
        ])

    @staticmethod
    def install_type_menu():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{S.NPM} npm install <pkg>", callback_data="install_type:npm")],
            [InlineKeyboardButton(f"{S.PIP} pip install <pkg>", callback_data="install_type:pip")],
            [InlineKeyboardButton(f"{S.BACK} Back", callback_data="pkg_manager")]
        ])

async def check_access(update: Update):
    user = update.effective_user
    if not PremiumManager.can_use_bot(user.id):
        if update.callback_query:
            try:
                await update.callback_query.answer("Premium Only!", show_alert=True)
            except:
                pass
        elif update.message:
            await update.message.reply_text(
                f"{S.LOCK} **Access Denied**\n\n"
                f"This bot is **locked**.\n"
                f"Only **Premium Users** can access.\n\n"
                f"Your ID: `{user.id}`",
                parse_mode="Markdown"
            )
        return False
    return True

@safe_execute
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not PremiumManager.can_use_bot(user.id):
        await update.message.reply_text(
            f"{S.LOCK} **Access Denied**\n\n"
            f"This bot is **locked**.\n"
            f"Only **Premium Users** can access.\n\n"
            f"Your ID: `{user.id}`",
            parse_mode="Markdown"
        )
        return

    # Send video with credits buttons on /start
    # When user clicks "Enter Dashboard", it switches to menu
    caption = (
        f"{S.BOT} **VPS Bot Manager v3.0**\n\n"
        f"{S.NODEJS} Node.js Bots\n"
        f"{S.PYTHON} Python Bots\n"
        f"{S.WHATSAPP} WhatsApp Bots (Baileys)\n"
        f"{S.PACKAGE} Package Manager\n\n"
        f"{S.DEV} **BOT MAD BY @Hx5x5x5x**\n"
        f"{S.HEART} Powered by Dev_Null_X"
    )

    try:
        await update.message.reply_video(
            video=CREDITS["home_video"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=KB.credits()
        )
    except Exception as e:
        # Fallback if video fails
        log_error(f"Video send failed: {e}")
        await update.message.reply_text(
            caption,
            parse_mode="Markdown",
            reply_markup=KB.credits()
        )

@safe_execute
async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text(
            f"{S.ERROR} **Admin Only!**\nYour ID: `{user.id}`", parse_mode="Markdown"
        )
        return

    args = context.args
    if not args or args[0].lower() not in ["on", "off"]:
        current = PremiumManager.is_unlocked()
        status = f"{S.UNLOCK} **UNLOCKED** (Anyone can use)" if current else f"{S.LOCK} **LOCKED** (Premium only)"
        await update.message.reply_text(
            f"{S.SETTINGS} **Unlock Settings**\n\n"
            f"Current: {status}\n\n"
            f"**Usage:**\n"
            f"`/unlock on` - Anyone can use the bot\n"
            f"`/unlock off` - Only Premium Users can use\n\n"
            f"**Admin Commands:**\n"
            f"`/addprem <user_id>` - Add premium user\n"
            f"`/delprem <user_id>` - Remove premium user\n"
            f"`/premusers` - List all premium users",
            parse_mode="Markdown"
        )
        return

    action = args[0].lower()
    if action == "on":
        PremiumManager.set_unlock(True)
        await update.message.reply_text(
            f"{S.UNLOCK} **Bot Unlocked!**\n\n"
            f"Now **anyone** can use this bot.\n"
            f"Use `/unlock off` to restrict to Premium users.",
            parse_mode="Markdown"
        )
    else:
        PremiumManager.set_unlock(False)
        await update.message.reply_text(
            f"{S.LOCK} **Bot Locked!**\n\n"
            f"Now only **Premium Users** can use this bot.\n"
            f"Use `/unlock on` to allow everyone.\n\n"
            f"Manage premium users with `/addprem` and `/delprem`",
            parse_mode="Markdown"
        )

@safe_execute
async def add_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text(f"{S.ERROR} **Admin Only!**", parse_mode="Markdown")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            f"{S.ERROR} **Usage:** `/addprem <user_id>`", parse_mode="Markdown"
        )
        return

    try:
        target_id = int(args[0])
        PremiumManager.add_premium(target_id, user.id)
        await update.message.reply_text(
            f"{S.SUCCESS} **Premium Added!**\n\n"
            f"{S.CROWN} User ID: `{target_id}`\n"
            f"{S.USER} Added by: `{user.id}`",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text(f"{S.ERROR} Invalid user ID!", parse_mode="Markdown")

@safe_execute
async def del_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text(f"{S.ERROR} **Admin Only!**", parse_mode="Markdown")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            f"{S.ERROR} **Usage:** `/delprem <user_id>`", parse_mode="Markdown"
        )
        return

    try:
        target_id = int(args[0])
        if PremiumManager.remove_premium(target_id):
            await update.message.reply_text(
                f"{S.SUCCESS} **Premium Removed!**\n\n"
                f"{S.USER} User ID: `{target_id}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"{S.WARNING} User `{target_id}` was not premium.", parse_mode="Markdown"
            )
    except ValueError:
        await update.message.reply_text(f"{S.ERROR} Invalid user ID!", parse_mode="Markdown")

@safe_execute
async def list_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text(f"{S.ERROR} **Admin Only!**", parse_mode="Markdown")
        return

    premium_users = PremiumManager.get_premium_list()

    if not premium_users:
        await update.message.reply_text(
            f"{S.INFO} **No Premium Users**\n\n"
            f"Use `/addprem <user_id>` to add users.",
            parse_mode="Markdown"
        )
        return

    text = f"{S.CROWN} **Premium Users** ({len(premium_users)})\n{'─' * 25}\n\n"
    for uid, info in premium_users.items():
        added = info.get("added_at", "Unknown")[:10]
        text += f"{S.USER} `{uid}` - Added: `{added}`\n"

    await update.message.reply_text(text, parse_mode="Markdown")

@safe_execute
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user  # FIX: Define user before using it

    if not await check_access(update):
        return

    try:
        await query.answer()
    except:
        pass

    data = query.data

    # Handle enter_menu - switch from video to main menu
    if data == "enter_menu":
        await safe_edit(query, 
            f"{S.BOT} **VPS Bot Manager v3.0**\n\n"
            f"{S.NODEJS} Node.js | {S.PYTHON} Python | {S.WHATSAPP} WhatsApp\n"
            f"{S.PACKAGE} Package Manager\n\n"
            f"{S.ARROW} Select an option:", KB.main())
        return

    if data == "menu":
        await safe_edit(query, 
            f"{S.BOT} **VPS Bot Manager v3.0**\n\n"
            f"{S.NODEJS} Node.js | {S.PYTHON} Python | {S.WHATSAPP} WhatsApp\n"
            f"{S.PACKAGE} Package Manager\n\n"
            f"{S.ARROW} Select an option:", KB.main())

    elif data == "my_bots":
        await show_bots_list(update, context)

    elif data.startswith("bot_detail:"):
        await show_bot_detail(update, context, data.split(":")[1])

    elif data.startswith("start:"):
        await handle_action(update, context, data.split(":")[1], "start")

    elif data.startswith("stop:"):
        await handle_action(update, context, data.split(":")[1], "stop")

    elif data.startswith("restart:"):
        await handle_action(update, context, data.split(":")[1], "restart")

    elif data.startswith("logs:"):
        await show_logs(update, context, data.split(":")[1])

    elif data.startswith("bot_status:"):
        await show_bot_status(update, context, data.split(":")[1])

    elif data.startswith("delete:"):
        await confirm_delete(update, context, data.split(":")[1])

    elif data.startswith("confirm_delete:"):
        await delete_bot(update, context, data.split(":")[1])

    elif data == "deploy":
        await safe_edit(query, f"{S.DEPLOY} **Deploy New Bot**\n\n{S.ARROW} Select type:", KB.deploy_type())

    elif data.startswith("deploy_type:"):
        bot_type = data.split(":")[1]
        UserSession.set(user.id, 'deploy_type', bot_type)
        UserSession.set(user.id, 'awaiting_zip', True)

        type_name = {"nodejs": "Node.js", "python": "Python", "whatsapp": "WhatsApp (Baileys)"}.get(bot_type, bot_type.title())

        req_text = ""
        if bot_type == "nodejs":
            req_text = "• `package.json` required"
        elif bot_type == "python":
            req_text = "• `main.py` or `bot.py` required"
        elif bot_type == "whatsapp":
            req_text = "• Baileys-based bot code\n• `package.json` required"

        await safe_edit(query,
            f"{S.DEPLOY} **Deploy {type_name} Bot**\n\n"
            f"{S.ARROW} Send me a **zip file** with your bot code.\n\n"
            f"{S.INFO} Requirements:\n"
            f"{req_text}\n"
            f"• Max: {MAX_ZIP_SIZE_MB}MB",
            KB.back("deploy")
        )

    elif data == "vps_status":
        await show_vps_status(update, context)

    elif data == "refresh_vps":
        await show_vps_status(update, context)

    elif data == "settings":
        await show_settings(update, context)

    elif data == "premium_menu":
        await show_premium_menu(update, context)

    elif data == "premium_add":
        UserSession.set(user.id, 'awaiting_premium_add', True)
        await safe_edit(query,
            f"{S.CROWN} **Add Premium User**\n\n"
            f"{S.ARROW} Send me the **User ID** to add as premium.",
            KB.back("premium_menu")
        )

    elif data == "premium_remove":
        UserSession.set(user.id, 'awaiting_premium_remove', True)
        await safe_edit(query,
            f"{S.USER} **Remove Premium User**\n\n"
            f"{S.ARROW} Send me the **User ID** to remove from premium.",
            KB.back("premium_menu")
        )

    elif data == "premium_list":
        await show_premium_list_callback(update, context)

    # WhatsApp specific handlers
    elif data.startswith("wa_password:"):
        bot_id = data.split(":")[1]
        UserSession.set(user.id, 'awaiting_wa_password', bot_id)
        await safe_edit(query,
            f"{S.KEY} **Set WhatsApp Password**\n\n"
            f"{S.ARROW} Send me the password for this bot.\n"
            f"Users will need this password to use the bot.",
            KB.back(f"bot_detail:{bot_id}")
        )

    elif data.startswith("wa_skip_pass:"):
        bot_id = data.split(":")[1]
        BotDatabase.update_bot(bot_id, 'wa_password', None)
        BotDatabase.update_bot(bot_id, 'wa_password_skipped', True)
        await safe_edit(query,
            f"{S.SKIP} **Password Skipped**\n\n"
            f"No password protection set.\n"
            f"{S.ARROW} Now send the phone number (e.g., 919876543210)",
            KB.back(f"bot_detail:{bot_id}")
        )
        UserSession.set(user.id, 'awaiting_wa_phone', bot_id)

    # Package manager handlers
    elif data == "pkg_manager":
        await show_pkg_manager_menu(update, context)

    elif data.startswith("packages:"):
        bot_id = data.split(":")[1]
        await show_installed_packages(update, context, bot_id)

    elif data.startswith("install_pkg:"):
        bot_id = data.split(":")[1]
        UserSession.set(user.id, 'install_target_bot', bot_id)
        await safe_edit(query,
            f"{S.PACKAGE} **Install Package**\n\n"
            f"{S.ARROW} Select package manager:",
            KB.install_type_menu()
        )

    elif data.startswith("npm_install:"):
        bot_id = data.split(":")[1]
        UserSession.set(user.id, 'awaiting_npm_pkg', bot_id)
        await safe_edit(query,
            f"{S.NPM} **Install npm Package**\n\n"
            f"{S.ARROW} Send package name to install.\n"
            f"Examples: `chalk`, `axios`, `@whiskeysockets/baileys`",
            KB.back(f"bot_detail:{bot_id}")
        )

    elif data.startswith("pip_install:"):
        bot_id = data.split(":")[1]
        UserSession.set(user.id, 'awaiting_pip_pkg', bot_id)
        await safe_edit(query,
            f"{S.PIP} **Install pip Package**\n\n"
            f"{S.ARROW} Send package name to install.\n"
            f"Examples: `requests`, `pillow`, `aiohttp`",
            KB.back(f"bot_detail:{bot_id}")
        )

    elif data.startswith("view_packages:"):
        bot_id = data.split(":")[1]
        await show_installed_packages(update, context, bot_id)

    elif data.startswith("install_type:"):
        pkg_type = data.split(":")[1]
        UserSession.set(user.id, 'install_type', pkg_type)

        # Show bot selection for package installation
        user = update.effective_user
        bots = BotDatabase.get_user_bots(user.id)

        if not bots:
            await safe_edit(query,
                f"{S.WARNING} No bots deployed!",
                KB.back("pkg_manager")
            )
            return

        keyboard = []
        for bot_id, info in bots.items():
            if pkg_type == "npm" and info['type'] in ['nodejs', 'whatsapp']:
                keyboard.append([InlineKeyboardButton(
                    f"{S.BOT} {info['name']} ({info['type']})", 
                    callback_data=f"pkg_bot_select:{bot_id}"
                )])
            elif pkg_type == "pip" and info['type'] == 'python':
                keyboard.append([InlineKeyboardButton(
                    f"{S.BOT} {info['name']} ({info['type']})", 
                    callback_data=f"pkg_bot_select:{bot_id}"
                )])

        if not keyboard:
            await safe_edit(query,
                f"{S.WARNING} No compatible bots found for {pkg_type} install!",
                KB.back("pkg_manager")
            )
            return

        keyboard.append([InlineKeyboardButton(f"{S.BACK} Back", callback_data="pkg_manager")])

        await safe_edit(query,
            f"{S.PACKAGE} **Select Bot**\n\n"
            f"Choose a bot to install {pkg_type} package:",
            InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("pkg_bot_select:"):
        bot_id = data.split(":")[1]
        pkg_type = UserSession.get(user.id, 'install_type', 'npm')

        if pkg_type == "npm":
            UserSession.set(user.id, 'awaiting_npm_pkg', bot_id)
            await safe_edit(query,
                f"{S.NPM} **Install npm Package**\n\n"
                f"{S.ARROW} Send package name to install.\n"
                f"Examples: `chalk`, `axios`, `express`",
                KB.back(f"bot_detail:{bot_id}")
            )
        else:
            UserSession.set(user.id, 'awaiting_pip_pkg', bot_id)
            await safe_edit(query,
                f"{S.PIP} **Install pip Package**\n\n"
                f"{S.ARROW} Send package name to install.\n"
                f"Examples: `requests`, `pillow`, `aiohttp`",
                KB.back(f"bot_detail:{bot_id}")
            )

async def safe_edit(query, text, reply_markup=None):
    try:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        elif "There is no text in the message to edit" in str(e) or "message is not modified" in str(e).lower():
            # Video/animation message - delete and send new text
            try:
                await query.delete_message()
            except:
                pass
            await query.message.chat.send_message(text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            raise

async def show_bots_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if not bots:
        await safe_edit(query,
            f"{S.WARNING} **No bots deployed!**\n\n{S.ARROW} Click 'Deploy New Bot'",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.DEPLOY} Deploy New Bot", callback_data="deploy")],
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
            ])
        )
        return

    keyboard = []
    for bot_id, info in bots.items():
        bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))
        status = S.START if bot_obj.is_running() else S.STOP
        type_emoji = {"nodejs": S.NODEJS, "python": S.PYTHON, "whatsapp": S.WHATSAPP}.get(info['type'], S.BOT)
        keyboard.append([InlineKeyboardButton(f"{status} {type_emoji} {info['name']}", callback_data=f"bot_detail:{bot_id}")])
    keyboard.append([InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")])

    await safe_edit(query,
        f"{S.BOT} **Your Bots** ({len(bots)}/{MAX_BOTS})\n\n{S.ARROW} Click to manage:",
        InlineKeyboardMarkup(keyboard)
    )

async def show_bot_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        await safe_edit(query, f"{S.ERROR} Bot not found or access denied!", KB.back("my_bots"))
        return

    info = bots[bot_id]
    bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))
    is_running = bot_obj.is_running()

    status_emoji = S.START if is_running else S.STOP
    status_text = "Running" if is_running else "Stopped"
    type_emoji = {"nodejs": S.NODEJS, "python": S.PYTHON, "whatsapp": S.WHATSAPP}.get(info['type'], S.BOT)

    # WhatsApp specific info
    wa_info = ""
    if info['type'] == 'whatsapp':
        wa_phone = info.get('wa_phone', 'Not set')
        wa_pass = info.get('wa_password', 'None')
        wa_info = f"\n{S.PHONE} Phone: `{wa_phone}`\n{S.KEY} Password: `{'Set' if wa_pass else 'None'}`\n"

    text = (
        f"{type_emoji} **{info['name']}**\n"
        f"{'─' * 25}\n"
        f"{status_emoji} Status: `{status_text}`\n"
        f"{S.FILE} Type: `{info['type'].title()}`\n"
        f"{S.FILE} Dir: `{info['dir']}`\n"
        f"{S.TIME} Created: `{info['created_at'][:10]}`"
        f"{wa_info}\n\n"
        f"{S.ARROW} Select action:"
    )

    await safe_edit(query, text, KB.bot_actions(bot_id, is_running, info['type']))

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str, action: str):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except:
            pass
        return

    info = bots[bot_id]
    bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))

    action_texts = {"start": "Starting", "stop": "Stopping", "restart": "Restarting"}

    try:
        await query.edit_message_text(
            f"{S.LOADING} {action_texts[action]} **{info['name']}**...",
            parse_mode="Markdown"
        )
    except:
        pass

    success = False
    if action == "start":
        success = bot_obj.start()
    elif action == "stop":
        success = bot_obj.stop()
    elif action == "restart":
        success = bot_obj.restart()

    await asyncio.sleep(1)
    await show_bot_detail(update, context, bot_id)

    try:
        status = f"{S.SUCCESS} {action_texts[action]}!" if success else f"{S.ERROR} Failed!"
        await query.answer(status, show_alert=True)
    except:
        pass

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except:
            pass
        return

    info = bots[bot_id]
    bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))

    try:
        await query.edit_message_text(
            f"{S.LOADING} Fetching logs...", parse_mode="Markdown"
        )
    except:
        pass

    logs = bot_obj.get_logs(30)
    logs = logs.replace("`", "\'")

    if len(logs) > 3500:
        logs = logs[-3500:] + "\n\n... (truncated)"

    text = f"{S.LOGS} **Logs: {info['name']}**\n{'─' * 25}\n\n```\n{logs}\n```"

    await safe_edit(query, text, InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{S.REFRESH} Refresh", callback_data=f"logs:{bot_id}")],
        [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
    ]))

async def show_bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except:
            pass
        return

    info = bots[bot_id]
    bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))
    is_running = bot_obj.is_running()

    process_info = "N/A"
    if is_running:
        try:
            result = subprocess.run(
                ["pm2", "describe", bot_obj.service_name],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout:
                process_info = result.stdout[:800]
            else:
                result = subprocess.run(
                    ["systemctl", "status", bot_obj.service_name],
                    capture_output=True, text=True, timeout=10
                )
                if result.stdout:
                    process_info = result.stdout[:800]
        except:
            pass

    process_info = process_info.replace("`", "\'")
    status_emoji = S.START if is_running else S.STOP
    type_emoji = {"nodejs": S.NODEJS, "python": S.PYTHON, "whatsapp": S.WHATSAPP}.get(info['type'], S.BOT)

    text = (
        f"{S.STATUS} **Status: {info['name']}**\n"
        f"{'─' * 25}\n"
        f"{type_emoji} Type: `{info['type'].title()}`\n"
        f"{status_emoji} State: `{'Running' if is_running else 'Stopped'}`\n"
        f"{S.FILE} Path: `{info['dir']}`\n"
        f"{S.TIME} Created: `{info['created_at'][:19]}`\n\n"
        f"{S.INFO} Process Info:\n"
        f"```\n{process_info}\n```"
    )

    await safe_edit(query, text, InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{S.REFRESH} Refresh", callback_data=f"bot_status:{bot_id}")],
        [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
    ]))

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except:
            pass
        return

    info = bots[bot_id]

    await safe_edit(query,
        f"{S.WARNING} **Delete Bot?**\n\n"
        f"Delete **{info['name']}**?\n\n"
        f"{S.ERROR} This cannot be undone!",
        KB.confirm_delete(bot_id)
    )

async def delete_bot(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        try:
            await query.answer("Bot not found or access denied!", show_alert=True)
        except:
            pass
        return

    info = bots[bot_id]
    bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))

    bot_obj.stop()

    try:
        subprocess.run(["pm2", "delete", bot_obj.service_name], capture_output=True, timeout=10)
        subprocess.run(["pm2", "save"], capture_output=True, timeout=10)

        if bot_obj.bot_type in ["python", "whatsapp"]:
            subprocess.run(["systemctl", "disable", bot_obj.service_name], capture_output=True, timeout=10)
            service_file = f"/etc/systemd/system/{bot_obj.service_name}.service"
            if os.path.exists(service_file):
                os.remove(service_file)
            subprocess.run(["systemctl", "daemon-reload"], capture_output=True, timeout=10)
    except:
        pass

    try:
        if os.path.exists(info['dir']):
            shutil.rmtree(info['dir'])
    except Exception as e:
        log_error(f"Failed to remove dir: {e}")

    BotDatabase.remove_bot(bot_id)

    await safe_edit(query,
        f"{S.SUCCESS} **{info['name']}** deleted!",
        KB.back("my_bots")
    )

async def show_vps_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stats = SystemMonitor.get_stats()

    cpu_bar = "█" * int(stats['cpu'] / 10) + "░" * (10 - int(stats['cpu'] / 10))
    ram_bar = "█" * int(stats['ram_percent'] / 10) + "░" * (10 - int(stats['ram_percent'] / 10))
    disk_bar = "█" * int(stats['disk_percent'] / 10) + "░" * (10 - int(stats['disk_percent'] / 10))

    text = (
        f"{S.STATUS} **VPS System Status**\n"
        f"{'─' * 25}\n\n"
        f"{S.CPU} **CPU**\n`{cpu_bar}` {stats['cpu']:.1f}%\n\n"
        f"{S.RAM} **RAM**\n`{ram_bar}` {stats['ram_percent']:.1f}%\n"
        f"`{stats['ram_used']:.2f}GB / {stats['ram_total']:.2f}GB`\n\n"
        f"{S.DISK} **Disk**\n`{disk_bar}` {stats['disk_percent']:.1f}%\n"
        f"`{stats['disk_used']:.2f}GB / {stats['disk_total']:.2f}GB`\n\n"
        f"{S.UPTIME} **Uptime:** `{SystemMonitor.format_uptime(stats['uptime'])}`"
    )

    await safe_edit(query, text, InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{S.REFRESH} Refresh", callback_data="refresh_vps")],
        [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
    ]))

async def show_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    premium_users = PremiumManager.get_premium_list()
    is_unlocked = PremiumManager.is_unlocked()

    lock_status = f"{S.UNLOCK} Unlocked (Anyone)" if is_unlocked else f"{S.LOCK} Locked (Premium Only)"

    text = (
        f"{S.CROWN} **Premium Management**\n"
        f"{'─' * 25}\n\n"
        f"{S.INFO} **Status:** {lock_status}\n"
        f"{S.USER} **Premium Users:** `{len(premium_users)}`\n\n"
        f"{S.ARROW} Select action:"
    )

    await safe_edit(query, text, KB.premium_menu())

async def show_premium_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    premium_users = PremiumManager.get_premium_list()

    if not premium_users:
        await safe_edit(query,
            f"{S.INFO} **No Premium Users**\n\nUse Add Premium to add users.",
            KB.back("premium_menu")
        )
        return

    text = f"{S.CROWN} **Premium Users** ({len(premium_users)})\n{'─' * 25}\n\n"
    for uid, info in premium_users.items():
        added = info.get("added_at", "Unknown")[:10]
        text += f"{S.USER} `{uid}` - Added: `{added}`\n"

    await safe_edit(query, text, KB.back("premium_menu"))

# ==================== PACKAGE MANAGER ====================

async def show_pkg_manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    total = len(bots)
    node_bots = sum(1 for b in bots.values() if b['type'] in ['nodejs', 'whatsapp'])
    py_bots = sum(1 for b in bots.values() if b['type'] == 'python')

    text = (
        f"{S.PACKAGE} **Package Manager**\n"
        f"{'─' * 25}\n\n"
        f"{S.INFO} **Your Bots:**\n"
        f"{S.NODEJS} Node.js/WhatsApp: `{node_bots}`\n"
        f"{S.PYTHON} Python: `{py_bots}`\n\n"
        f"{S.ARROW} Install packages directly from Telegram!"
    )

    await safe_edit(query, text, KB.install_type_menu())

async def show_installed_packages(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        await safe_edit(query, f"{S.ERROR} Bot not found!", KB.back("pkg_manager"))
        return

    info = bots[bot_id]
    bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))
    packages = bot_obj.get_installed_packages()

    text = f"{S.PACKAGE} **Installed Packages: {info['name']}**\n{'─' * 25}\n\n"

    if not packages:
        text += f"{S.WARNING} No packages found or unable to read."
    else:
        if 'dependencies' in packages:
            text += f"{S.NPM} **npm Dependencies:**\n"
            for pkg, ver in packages['dependencies'].items():
                text += f"• `{pkg}`: `{ver}`\n"
            text += "\n"
        if 'devDependencies' in packages:
            text += f"{S.NPM} **npm Dev Dependencies:**\n"
            for pkg, ver in packages['devDependencies'].items():
                text += f"• `{pkg}`: `{ver}`\n"
            text += "\n"
        if 'requirements' in packages:
            text += f"{S.PIP} **pip Requirements:**\n"
            for pkg in packages['requirements']:
                text += f"• `{pkg}`\n"

    await safe_edit(query, text, InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{S.INSTALL} Install More", callback_data=f"install_pkg:{bot_id}")],
        [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
    ]))

async def handle_npm_install(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str, package_name: str):
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        await update.message.reply_text(f"{S.ERROR} Bot not found!", parse_mode="Markdown")
        return

    info = bots[bot_id]
    bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))

    msg = await update.message.reply_text(
        f"{S.LOADING} Installing `{package_name}` in **{info['name']}**...",
        parse_mode="Markdown"
    )

    success, stdout, stderr = bot_obj.install_npm_package(package_name)

    if success:
        # Update package.json if exists
        pkg_json = os.path.join(bot_obj.bot_dir, "package.json")
        if os.path.exists(pkg_json):
            try:
                subprocess.run(
                    ["npm", "install", package_name, "--save"],
                    cwd=bot_obj.bot_dir, capture_output=True, timeout=60
                )
            except:
                pass

        await msg.edit_text(
            f"{S.SUCCESS} **Package Installed!**\n\n"
            f"{S.NPM} `{package_name}`\n"
            f"{S.BOT} Bot: `{info['name']}`\n\n"
            f"{S.INFO} You may need to restart the bot.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.RESTART} Restart Bot", callback_data=f"restart:{bot_id}")],
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
            ])
        )
    else:
        error_text = stderr[:300] if stderr else "Unknown error"
        await msg.edit_text(
            f"{S.ERROR} **Installation Failed!**\n\n"
            f"{S.NPM} Package: `{package_name}`\n"
            f"```\n{error_text}\n```",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
            ])
        )

async def handle_pip_install(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str, package_name: str):
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)

    if bot_id not in bots:
        await update.message.reply_text(f"{S.ERROR} Bot not found!", parse_mode="Markdown")
        return

    info = bots[bot_id]
    bot_obj = HostedBot(bot_id, info['name'], info['dir'], info['type'], info.get('user_id'))

    msg = await update.message.reply_text(
        f"{S.LOADING} Installing `{package_name}` in **{info['name']}**...",
        parse_mode="Markdown"
    )

    success, stdout, stderr = bot_obj.install_pip_package(package_name)

    if success:
        # Update requirements.txt
        req_file = os.path.join(bot_obj.bot_dir, "requirements.txt")
        try:
            with open(req_file, 'a') as f:
                f.write(f"\n{package_name}\n")
        except:
            pass

        await msg.edit_text(
            f"{S.SUCCESS} **Package Installed!**\n\n"
            f"{S.PIP} `{package_name}`\n"
            f"{S.BOT} Bot: `{info['name']}`\n\n"
            f"{S.INFO} You may need to restart the bot.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.RESTART} Restart Bot", callback_data=f"restart:{bot_id}")],
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
            ])
        )
    else:
        error_text = stderr[:300] if stderr else "Unknown error"
        await msg.edit_text(
            f"{S.ERROR} **Installation Failed!**\n\n"
            f"{S.PIP} Package: `{package_name}`\n"
            f"```\n{error_text}\n```",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
            ])
        )

# ==================== DOCUMENT HANDLER ====================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user  # FIX: Define user before using it
    if not UserSession.get(user.id, 'awaiting_zip'):
        return

    user = update.effective_user
    if not PremiumManager.can_use_bot(user.id):
        await update.message.reply_text(
            f"{S.LOCK} **Access Denied**\n\n"
            f"This bot is **locked**.\n"
            f"Only **Premium Users** can access.",
            parse_mode="Markdown"
        )
        return

    document = update.message.document

    if not document.file_name.endswith('.zip'):
        await update.message.reply_text(f"{S.ERROR} Please send a **.zip** file!", parse_mode="Markdown")
        return

    if document.file_size > MAX_ZIP_SIZE_MB * 1024 * 1024:
        await update.message.reply_text(f"{S.ERROR} File too large! Max: {MAX_ZIP_SIZE_MB}MB", parse_mode="Markdown")
        return

    bot_type = UserSession.get(user.id, 'deploy_type', 'python')

    msg = await update.message.reply_text(f"{S.LOADING} Processing zip file...")

    try:
        file = await context.bot.get_file(document.file_id)
        temp_zip = f"/tmp/bot_deploy_{int(time.time())}.zip"
        await file.download_to_drive(temp_zip)

        await msg.edit_text(f"{S.LOADING} Extracting...")

        bot_id = f"bot_{int(time.time())}"
        bot_dir = f"{HOSTED_BOTS_DIR}/{bot_id}"
        os.makedirs(bot_dir, exist_ok=True)

        with zipfile.ZipFile(temp_zip, 'r') as zf:
            zf.extractall(bot_dir)

        os.remove(temp_zip)

        await msg.edit_text(f"{S.LOADING} Validating...")

        bot_name = document.file_name.replace('.zip', '')

        if bot_type == "nodejs":
            pkg_file = f"{bot_dir}/package.json"
            if not os.path.exists(pkg_file):
                shutil.rmtree(bot_dir)
                await msg.edit_text(
                    f"{S.ERROR} **Invalid!** `package.json` not found.",
                    parse_mode="Markdown", reply_markup=KB.back("deploy")
                )
                return
            with open(pkg_file) as f:
                pkg = json.load(f)
                bot_name = pkg.get('name', bot_name)

        elif bot_type == "whatsapp":
            pkg_file = f"{bot_dir}/package.json"
            if not os.path.exists(pkg_file):
                pkg = {
                    "name": bot_name,
                    "version": "1.0.0",
                    "main": "index.js",
                    "dependencies": {}
                }
                with open(pkg_file, 'w') as f:
                    json.dump(pkg, f, indent=2)
            else:
                with open(pkg_file) as f:
                    pkg = json.load(f)
                    bot_name = pkg.get('name', bot_name)

            main_found = False
            for mf in ["index.js", "main.js", "bot.js", "app.js"]:
                if os.path.exists(f"{bot_dir}/{mf}"):
                    main_found = True
                    break

            if not main_found:
                shutil.rmtree(bot_dir)
                await msg.edit_text(
                    f"{S.ERROR} **Invalid!** No `.js` main file found.",
                    parse_mode="Markdown", reply_markup=KB.back("deploy")
                )
                return

        else:
            py_files = [f for f in os.listdir(bot_dir) if f.endswith('.py')]
            if not py_files:
                shutil.rmtree(bot_dir)
                await msg.edit_text(
                    f"{S.ERROR} **Invalid!** No `.py` files found.",
                    parse_mode="Markdown", reply_markup=KB.back("deploy")
                )
                return

        await msg.edit_text(f"{S.LOADING} Installing dependencies...")

        if bot_type in ["nodejs", "whatsapp"]:
            subprocess.run(["npm", "install"], cwd=bot_dir, capture_output=True, text=True, timeout=300)
            if bot_type == "whatsapp":
                wa_packages = ["@whiskeysockets/baileys", "qrcode-terminal", "pino"]
                for pkg in wa_packages:
                    subprocess.run(["npm", "install", pkg], cwd=bot_dir, capture_output=True, timeout=120)
        else:
            req_file = f"{bot_dir}/requirements.txt"
            if os.path.exists(req_file):
                result = subprocess.run(
                    ["pip3", "install", "-r", req_file], 
                    cwd=bot_dir, capture_output=True, text=True, timeout=300
                )
                log_deploy(f"pip install result: rc={result.returncode}", bot_name)

                if result.returncode != 0:
                    result2 = subprocess.run(
                        ["pip3", "install", "-r", req_file], 
                        capture_output=True, text=True, timeout=300
                    )
                    log_deploy(f"pip global install result: rc={result2.returncode}", bot_name)

                result3 = subprocess.run(
                    ["pip3", "install", "--user", "-r", req_file], 
                    capture_output=True, text=True, timeout=300
                )
                log_deploy(f"pip user install result: rc={result3.returncode}", bot_name)

        await msg.edit_text(f"{S.LOADING} Creating service...")

        bot_obj = HostedBot(bot_id, bot_name, bot_dir, bot_type, user_id=user.id)

        if bot_type == "python":
            main_file = "main.py"
            for mf in ["main.py", "bot.py", "app.py", "run.py"]:
                if os.path.exists(f"{bot_dir}/{mf}"):
                    main_file = mf
                    break

            target = os.path.join(bot_dir, main_file)

            pip_show = subprocess.run(
                ["python3", "-c", "import site; print(site.getsitepackages()[0])"],
                capture_output=True, text=True, timeout=10
            )
            python_path = pip_show.stdout.strip() if pip_show.returncode == 0 else "/usr/local/lib/python3.10/dist-packages"

            ecosystem = {
                "apps": [{
                    "name": bot_obj.service_name,
                    "script": target,
                    "interpreter": "/usr/bin/python3",
                    "cwd": bot_dir,
                    "autorestart": True,
                    "max_restarts": 5,
                    "min_uptime": "10s",
                    "env": {
                        "PYTHONUNBUFFERED": "1",
                        "PYTHONPATH": f"{python_path}:{bot_dir}"
                    },
                    "log_file": f"/root/.pm2/logs/{bot_obj.service_name}-out.log",
                    "error_file": f"/root/.pm2/logs/{bot_obj.service_name}-error.log"
                }]
            }

            eco_path = f"{bot_dir}/ecosystem.json"
            with open(eco_path, 'w') as f:
                json.dump(ecosystem, f, indent=2)

            log_deploy(f"Created ecosystem file: {eco_path}", bot_name)

            service_content = f"""[Unit]
Description=Hosted Bot - {bot_name}
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={bot_dir}
ExecStart=/usr/bin/python3 {target}
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
            service_path = f"/etc/systemd/system/{bot_obj.service_name}.service"
            try:
                with open(service_path, 'w') as f:
                    f.write(service_content)
                subprocess.run(["systemctl", "daemon-reload"], capture_output=True, timeout=10)
                subprocess.run(["systemctl", "enable", bot_obj.service_name], capture_output=True, timeout=10)
                log_deploy(f"Created systemd service: {service_path}", bot_name)
            except Exception as e:
                log_deploy(f"Systemd service creation failed: {e}", bot_name)

        BotDatabase.add_bot(bot_id, bot_name, bot_dir, bot_type, user_id=user.id)

        started = False
        if AUTO_START_AFTER_DEPLOY:
            if bot_type == "python":
                req_file = f"{bot_dir}/requirements.txt"
                if os.path.exists(req_file):
                    with open(req_file) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                pkg = line.split('>=')[0].split('==')[0].strip()
                                check = subprocess.run(
                                    ["python3", "-c", f"import {pkg.split('-')[0].replace('python-', '')}"],
                                    capture_output=True, text=True, timeout=10
                                )
                                log_deploy(f"Package check {pkg}: rc={check.returncode}", bot_name)

            started = bot_obj.start()
            log_deploy(f"Auto-start result: {started}", bot_name)

        UserSession.set(user.id, 'awaiting_zip', False)

        status_text = "\n🟢 Auto-started!" if started else "\n⚠️ Deployed. Click Start to run."

        await msg.edit_text(
            f"{S.SUCCESS} **Deployed!**{status_text}\n\n"
            f"{S.BOT} Name: `{bot_name}`\n"
            f"{S.FILE} ID: `{bot_id}`\n"
            f"{S.FILE} Type: `{bot_type.title()}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.BOT} My Bots", callback_data="my_bots")],
                [InlineKeyboardButton(f"{S.HOME} Main Menu", callback_data="menu")]
            ])
        )

    except Exception as e:
        log_error(f"Deploy failed: {e}")
        await msg.edit_text(
            f"{S.ERROR} **Failed!**\n\n`{str(e)[:300]}`",
            parse_mode="Markdown", reply_markup=KB.back("deploy")
        )

# ==================== TEXT HANDLER ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user  # Already defined here, good

    if not PremiumManager.can_use_bot(user.id):
        return

    if user.id not in ADMIN_IDS:
        return

    text = update.message.text.strip()

    # Handle WhatsApp password input
    if UserSession.get(user.id, 'awaiting_wa_password'):
        bot_id = UserSession.get(user.id, 'awaiting_wa_password')
        BotDatabase.update_bot(bot_id, 'wa_password', text)
        UserSession.set(user.id, 'awaiting_wa_password', False)
        UserSession.set(user.id, 'awaiting_wa_phone', bot_id)
        await update.message.reply_text(
            f"{S.SUCCESS} **Password Set!**\n\n"
            f"{S.KEY} Password saved.\n"
            f"{S.ARROW} Now send the phone number (e.g., 919876543210)",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
            ])
        )
        return

    # Handle WhatsApp phone input
    if UserSession.get(user.id, 'awaiting_wa_phone'):
        bot_id = UserSession.get(user.id, 'awaiting_wa_phone')
        phone = text.replace("+", "").replace(" ", "").replace("-", "")
        BotDatabase.update_bot(bot_id, 'wa_phone', phone)
        UserSession.set(user.id, 'awaiting_wa_phone', False)
        await update.message.reply_text(
            f"{S.SUCCESS} **Phone Number Set!**\n\n"
            f"{S.PHONE} Number: `{phone}`\n"
            f"{S.INFO} The bot will now try to connect.\n"
            f"Check logs for pair code.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{S.LOGS} View Logs", callback_data=f"logs:{bot_id}")],
                [InlineKeyboardButton(f"{S.BACK} Back", callback_data=f"bot_detail:{bot_id}")]
            ])
        )
        return

    # Handle npm package install
    if UserSession.get(user.id, 'awaiting_npm_pkg'):
        bot_id = UserSession.get(user.id, 'awaiting_npm_pkg')
        UserSession.set(user.id, 'awaiting_npm_pkg', False)
        await handle_npm_install(update, context, bot_id, text)
        return

    # Handle pip package install
    if UserSession.get(user.id, 'awaiting_pip_pkg'):
        bot_id = UserSession.get(user.id, 'awaiting_pip_pkg')
        UserSession.set(user.id, 'awaiting_pip_pkg', False)
        await handle_pip_install(update, context, bot_id, text)
        return

    if UserSession.get(user.id, 'awaiting_premium_add'):
        try:
            target_id = int(text)
            PremiumManager.add_premium(target_id, user.id)
            UserSession.set(user.id, 'awaiting_premium_add', False)
            await update.message.reply_text(
                f"{S.SUCCESS} **Premium Added!**\n\n"
                f"{S.CROWN} User ID: `{target_id}`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{S.BACK} Premium Menu", callback_data="premium_menu")]
                ])
            )
        except ValueError:
            await update.message.reply_text(f"{S.ERROR} Invalid User ID! Send a number.", parse_mode="Markdown")
        return

    if UserSession.get(user.id, 'awaiting_premium_remove'):
        try:
            target_id = int(text)
            if PremiumManager.remove_premium(target_id):
                UserSession.set(user.id, 'awaiting_premium_remove', False)
                await update.message.reply_text(
                    f"{S.SUCCESS} **Premium Removed!**\n\n"
                    f"{S.USER} User ID: `{target_id}`",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"{S.BACK} Premium Menu", callback_data="premium_menu")]
                    ])
                )
            else:
                await update.message.reply_text(
                    f"{S.WARNING} User `{target_id}` was not premium.", parse_mode="Markdown"
                )
        except ValueError:
            await update.message.reply_text(f"{S.ERROR} Invalid User ID! Send a number.", parse_mode="Markdown")
        return

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    bots = BotDatabase.get_user_bots(user.id)
    total = len(bots)

    running = 0
    for b_id, b_info in bots.items():
        if HostedBot(b_id, b_info['name'], b_info['dir'], b_info['type'], b_info.get('user_id')).is_running():
            running += 1

    is_unlocked = PremiumManager.is_unlocked()
    lock_status = f"{S.UNLOCK} Unlocked" if is_unlocked else f"{S.LOCK} Premium Only"
    premium_count = len(PremiumManager.get_premium_list())

    text = (
        f"{S.SETTINGS} **Settings**\n"
        f"{'─' * 25}\n\n"
        f"{S.BOT} **Info**\n"
        f"{S.FILE} Bots: `{total}/{MAX_BOTS}`\n"
        f"{S.START} Running: `{running}`\n"
        f"{S.STOP} Stopped: `{total - running}`\n\n"
        f"{S.INFO} **Paths**\n"
        f"{S.FILE} Bots: `{HOSTED_BOTS_DIR}`\n"
        f"{S.FILE} Logs: `{LOGS_DIR}`\n\n"
        f"{S.LOCK} **Access Control**\n"
        f"Status: {lock_status}\n"
        f"{S.CROWN} Premium Users: `{premium_count}`"
    )

    await safe_edit(query, text, InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{S.CROWN} Premium Management", callback_data="premium_menu")],
        [InlineKeyboardButton(f"{S.BACK} Back", callback_data="menu")]
    ]))

async def post_init(application: Application):
    commands = [
        BotCommand("start", "Start bot manager"),
        BotCommand("menu", "Show main menu"),
        BotCommand("unlock", "Toggle unlock mode (on/off)"),
        BotCommand("addprem", "Add premium user"),
        BotCommand("delprem", "Remove premium user"),
        BotCommand("premusers", "List premium users")
    ]
    await application.bot.set_my_commands(commands)

def main():
    print(f"{S.BOT} Starting VPS Bot Manager v3.0...")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("menu", start_cmd))
    application.add_handler(CommandHandler("unlock", unlock_cmd))
    application.add_handler(CommandHandler("addprem", add_premium_cmd))
    application.add_handler(CommandHandler("delprem", del_premium_cmd))
    application.add_handler(CommandHandler("premusers", list_premium_cmd))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.Document.ZIP, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    async def error_handler(update, context):
        log_error(f"Update error: {context.error}")
    application.add_error_handler(error_handler)

    print(f"{S.SUCCESS} Bot Manager v2.0 started! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
