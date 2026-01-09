import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x]

TOOLS_DIR = "tools/multi-tools"

# ---------- Load tools ----------
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
sessions = {}

# ---------- Start Menu ----------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global TOOLS
    TOOLS = load_tools()

    buttons = []
    row = []

    for key in TOOLS:
        label = key.replace("-", " ").title()
        row.append(InlineKeyboardButton(label, callback_data=f"tool:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("💳 Balance", callback_data="balance"),
        InlineKeyboardButton("📦 My Jobs", callback_data="jobs")
    ])
    buttons.append([
        InlineKeyboardButton("🛒 Buy Credits", callback_data="buy")
    ])

    if update.message.from_user.id in ADMIN_IDS:
        buttons.append([
            InlineKeyboardButton("👑 Admin Panel", callback_data="admin")
        ])

    await update.message.reply_text(
        "🔹 Choose a service:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------- Button Handler ----------
async def on_click(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id

    # Tool selected
    if q.data.startswith("tool:"):
        tool_key = q.data.split(":",1)[1]
        sessions[user_id] = tool_key
        await q.message.reply_text("🔗 Send verification URL:")
        return

    # Balance
    if q.data == "balance":
        r = requests.get(f"{API_URL}/balance/{user_id}")
        await q.message.reply_text(f"💳 Balance: {r.json()['credits']} credits")
        return

    # Jobs
    if q.data == "jobs":
        r = requests.get(f"{API_URL}/jobs/{user_id}")
        jobs = r.json()
        if not jobs:
            await q.message.reply_text("No jobs yet.")
        else:
            text = "📦 Your Jobs:\n\n"
            for j in jobs:
                text += f"🆔 {j['id']} — {j['status']}\n"
            await q.message.reply_text(text)
        return

    # Buy credits
    if q.data == "buy":
        kb = [
            [InlineKeyboardButton("💳 Card (Stripe)", callback_data="buy:stripe")],
            [InlineKeyboardButton("🟡 Binance Pay", callback_data="buy:binance")],
            [InlineKeyboardButton("🪙 Crypto", callback_data="buy:crypto")],
            [InlineKeyboardButton("⭐ Telegram Stars", callback_data="buy:stars")]
        ]
        await q.message.reply_text("Choose payment method:", reply_markup=InlineKeyboardMarkup(kb))
        return

    # Admin panel
    if q.data == "admin" and user_id in ADMIN_IDS:
        kb = [
            [InlineKeyboardButton("Set Tool Price", callback_data="admin:setprice")],
            [InlineKeyboardButton("Grant Credits", callback_data="admin:grant")],
            [InlineKeyboardButton("View Queue", callback_data="admin:queue")]
        ]
        await q.message.reply_text("👑 Admin Panel:", reply_markup=InlineKeyboardMarkup(kb))
        return

# ---------- URL Handler ----------
async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

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
        f"✅ Job started!\n"
        f"🆔 Job ID: {d['job_id']}\n"
        f"📌 Queue Position: {d['queue_position']}\n"
        f"💳 Remaining Credits: {d['remaining_credits']}"
    )

# ---------- Status Command ----------
async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /status <job_id>")
        return

    job_id = ctx.args[0]
    r = requests.get(f"{API_URL}/status/{job_id}")
    data = r.json()

    await update.message.reply_text(
        f"📦 Job: {job_id}\n"
        f"Status: {data.get('status')}\n"
        f"Progress: {data.get('progress')}%"
    )

# ---------- Run Bot ----------
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CallbackQueryHandler(on_click))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

print("🤖 Bot running...")
app.run_polling()
