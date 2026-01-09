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
        sessions[user_id] = "promo"
        await q.message.reply_text("🏷 Send promo code:")
        return

    # Referral
    if q.data == "ref":
        link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
        await q.message.reply_text(
            "👥 Invite friends & earn credits!\n\n"
            f"Your referral link:\n{link}"
        )
        return

    # Subscription
    if q.data == "sub":
        await q.message.reply_text(
            "🔁 Monthly Subscription\n\n"
            "✔ 20 credits per month\n"
            "✔ Priority queue\n\n"
            "Use Buy Credits to subscribe."
        )
        return

    # Buy credits
    if q.data == "buy":
        kb = [
            [InlineKeyboardButton("💳 Card (Stripe)", callback_data="pay:stripe")],
            [InlineKeyboardButton("🟡 Binance Pay", callback_data="pay:binance")],
            [InlineKeyboardButton("🪙 Crypto", callback_data="pay:crypto")],
            [InlineKeyboardButton("⭐ Telegram Stars", callback_data="pay:stars")]
        ]
        await q.message.reply_text(
            "🛒 Choose payment method:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # Payment handlers
    if q.data.startswith("pay:"):
        method = q.data.split(":", 1)[1]
        await q.message.reply_text(f"💰 {method.upper()} payment coming soon.")
        return

# ---------------- Text handler ----------------

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Promo input
    if sessions.get(user_id) == "promo":
        code = update.message.text.strip()
        sessions.pop(user_id)

        r = requests.post(f"{API_URL}/promo", params={"user_id": user_id, "code": code})
        if r.status_code == 200:
            await update.message.reply_text("✅ Promo code applied!")
        else:
            await update.message.reply_text("❌ Invalid promo code.")
        return

    # Tool input
    if user_id not in sessions:
        return

    tool_key = sessions.pop(user_id)
    tool = TOOLS.get(tool_key)
    url = update.message.text.strip()

    await update.message.reply_text("⏳ Job queued...")

    r = requests.post(
        f"{API_URL}/run",
        params={"user_id": user_id, "tool": tool, "args": url}
    )

    if r.status_code != 200:
        await update.message.reply_text(r.text)
        return

    d = r.json()
    await update.message.reply_text(
        f"✅ Job started!\n\n"
        f"🆔 Job ID: {d['job_id']}\n"
        f"📌 Queue Position: {d['queue_position']}\n"
        f"💳 Remaining Credits: {d['remaining_credits']}"
    )

# ---------------- Run bot ----------------

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(on_click))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

print("🤖 Bot running...")
app.run_polling()
