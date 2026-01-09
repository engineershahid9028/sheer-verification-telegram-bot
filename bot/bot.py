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

# ================== CONFIG ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

TOOLS_DIR = "tools/multi-tools"

# ================== LOAD TOOLS ==================

def load_tools():
    tools = {}

    if not os.path.exists(TOOLS_DIR):
        print("❌ Tools directory not found:", TOOLS_DIR)
        return tools

    for name in os.listdir(TOOLS_DIR):
        path = os.path.join(TOOLS_DIR, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "main.py")):
            key = name.replace("-verify-tool", "").replace("-tool", "")
            tools[key] = name

    print("✅ Loaded tools:", tools)
    return tools


# Load tools on startup
TOOLS = load_tools()

# Store user sessions
sessions = {}

# ================== START MENU ==================

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global TOOLS
    TOOLS = load_tools()   # reload in case new tools were added

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

    buttons.append([InlineKeyboardButton("💳 Balance", callback_data="balance")])

    await update.message.reply_text(
        "🔹 Choose service:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================== BUTTON HANDLER ==================

async def on_click(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global TOOLS
    TOOLS = load_tools()

    q = update.callback_query
    await q.answer()

    # Tool selected
    if q.data in TOOLS:
        sessions[q.from_user.id] = q.data
        await q.message.reply_text("🔗 Send verification URL:")
        return

    # Balance button
    if q.data == "balance":
        if not API_URL:
            await q.message.reply_text("❌ API_URL not configured on server.")
            return

        try:
            r = requests.get(
                f"{API_URL}/balance/{q.from_user.id}",
                timeout=10
            )

            if r.status_code != 200:
                await q.message.reply_text(
                    f"❌ Balance service error ({r.status_code})"
                )
                return

            data = r.json()
            await q.message.reply_text(
                f"💳 Your Balance: {data['credits']} credits"
            )

        except Exception as e:
            await q.message.reply_text(
                "❌ Cannot connect to balance server.\n"
                "Please try again later."
            )
            print("Balance error:", e)

        return

# ================== URL HANDLER ==================

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    if uid not in sessions:
        return

    tool_key = sessions.pop(uid)
    tool = TOOLS.get(tool_key)

    if not tool:
        await update.message.reply_text("❌ Tool not found.")
        return

    url = update.message.text.strip()

    await update.message.reply_text("⏳ Job queued...")

    try:
        r = requests.post(
            f"{API_URL}/run",
            params={
                "user_id": uid,
                "tool": tool,
                "args": url
            },
            timeout=20
        )

        if r.status_code != 200:
            await update.message.reply_text(r.text)
            return

        d = r.json()

        await update.message.reply_text(
            f"✅ Job queued successfully!\n\n"
            f"🆔 Job ID: {d['job_id']}\n"
            f"💳 Remaining Credits: {d['remaining_credits']}"
        )

    except Exception as e:
        await update.message.reply_text(
            "❌ Backend server not reachable.\nPlease try again later."
        )
        print("Run job error:", e)

# ================== RUN BOT ==================

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is not set")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(on_click))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

print("🤖 Bot started...")
app.run_polling()
