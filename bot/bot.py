import os
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

TOOLS_DIR = "tools/multi-tools"
sessions = {}

# ---------------- LOAD TOOLS ----------------

def load_tools():
    import os
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

# ---------------- START MENU ----------------

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global TOOLS
    TOOLS = load_tools()

    buttons = []
    row = []

    for key in TOOLS:
        label = key.replace("-", " ").title()
        row.append(InlineKeyboardButton(label, callback_data=key))
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("💳 Balance", callback_data="balance"),
        InlineKeyboardButton("📦 My Jobs", callback_data="jobs")
    ])

    await update.message.reply_text(
        "🔷 Choose a service:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------------- BUTTON HANDLER ----------------

async def on_click(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data in TOOLS:
        sessions[q.from_user.id] = q.data
        await q.message.reply_text("🔗 Send verification URL:")
        return

    if q.data == "balance":
        r = requests.get(f"{API_URL}/balance/{q.from_user.id}")
        await q.message.reply_text(f"💳 Balance: {r.json()['credits']} credits")
        return

    if q.data == "jobs":
        r = requests.get(f"{API_URL}/jobs/{q.from_user.id}")
        jobs = r.json()

        if not jobs:
            await q.message.reply_text("📦 No jobs yet.")
            return

        msg = "📦 Your Jobs:\n\n"
        for j in jobs:
            msg += f"• {j['tool']} → {j['status']}\n"

        await q.message.reply_text(msg)
        return

# ---------------- URL INPUT ----------------

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    if uid not in sessions:
        return

    tool_key = sessions.pop(uid)
    tool = TOOLS.get(tool_key)

    url = update.message.text.strip()

    await update.message.reply_text("⏳ Job queued...")

    r = requests.post(
        f"{API_URL}/run",
        params={"user_id": uid, "tool": tool, "args": url}
    )

    if r.status_code != 200:
        await update.message.reply_text(r.text)
        return

    data = r.json()
    job_id = data["job_id"]

    # Start progress tracker
    asyncio.create_task(track_job(update, ctx, job_id))

# ---------------- PROGRESS TRACKER ----------------

async def track_job(update: Update, ctx: ContextTypes.DEFAULT_TYPE, job_id: str):
    chat_id = update.message.chat_id
    msg = await ctx.bot.send_message(chat_id, "🔄 Processing... 0%")

    while True:
        await asyncio.sleep(3)

        r = requests.get(f"{API_URL}/status/{job_id}")
        data = r.json()

        status = data["status"]
        progress = data["progress"]

        bar = "▓" * (progress // 10) + "░" * (10 - progress // 10)

        await msg.edit_text(f"🔄 Processing...\n[{bar}] {progress}%")

        if status == "done":
            output = data.get("output", "Completed")
            await msg.edit_text(f"✅ Job completed!\n\n{output[:4000]}")
            return

        if status == "failed":
            output = data.get("output", "Failed")
            await msg.edit_text(f"❌ Job failed\n\n{output}")
            return

# ---------------- RUN BOT ----------------

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(on_click))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

print("🤖 Bot started...")
app.run_polling()
