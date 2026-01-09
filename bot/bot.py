import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBotUsername")

TOOLS_DIR = "tools/multi-tools"
sessions = {}

# ---------------- Load tools ----------------

def load_tools():
    tools = {}
    if not os.path.exists(TOOLS_DIR):
        return tools

    for name in os.listdir(TOOLS_DIR):
        path = os.path.join(TOOLS_DIR, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "main.py")):
            key = name.replace("-verify-tool", "").replace("-tool", "")
            tools[key] = name
    return tools

TOOLS = load_tools()

# ---------------- Start menu ----------------

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global TOOLS
    TOOLS = load_tools()

    buttons = []
    row = []

    # Tool buttons
    for key in TOOLS:
        label = key.replace("-", " ").title()
        row.append(InlineKeyboardButton(label, callback_data=f"tool:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    # Utility buttons
    buttons.append([
        InlineKeyboardButton("💳 Balance", callback_data="balance"),
        InlineKeyboardButton("📦 My Jobs", callback_data="jobs")
    ])

    buttons.append([
        InlineKeyboardButton("🎁 Daily Credit", callback_data="daily"),
        InlineKeyboardButton("🏷 Promo Code", callback_data="promo")
    ])

    buttons.append([
        InlineKeyboardButton("👥 Referral", callback_data="ref"),
        InlineKeyboardButton("🔁 Subscription", callback_data="sub")
    ])

    buttons.append([
        InlineKeyboardButton("🛒 Buy Credits", callback_data="buy")
    ])

    await update.message.reply_text(
        "🔷 Choose a service:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------------- Button handler ----------------

async def on_click(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id

    # Tool click
    if q.data.startswith("tool:"):
        tool_key = q.data.split(":", 1)[1]
        sessions[user_id] = tool_key
        await q.message.reply_text("🔗 Send verification URL:")
        return

    # Balance
    if q.data == "balance":
        r = requests.get(f"{API_URL}/balance/{user_id}")
        await q.message.reply_text(f"💳 Balance: {r.json()['credits']} credits")
        return

    # My Jobs
    if q.data == "jobs":
        r = requests.get(f"{API_URL}/jobs/{user_id}")
        jobs = r.json()

        if not jobs:
            await q.message.reply_text("📦 You have no jobs yet.")
            return

        text = "📦 Your Jobs:\n\n"
        for j in jobs:
            text += f"🆔 {j['id']} — {j['status']}\n"

        await q.message.reply_text(text)
        return

    # Daily credit
    if q.data == "daily":
        r = requests.post(f"{API_URL}/daily/{user_id}")
        if r.json().get("claimed"):
            await q.message.reply_text("🎁 You received 1 free credit!")
        else:
            await q.message.reply_text("⏳ You already claimed today.")
        return

    # Promo code
    if q.data == "promo":
        sessions[user_id] =_]()
