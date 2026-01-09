import os, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN=os.getenv("BOT_TOKEN")
API_URL=os.getenv("API_URL")

import os

TOOLS_DIR = "tools/multi-tools"

def load_tools():
    tools = {}
    for name in os.listdir(TOOLS_DIR):
        path = os.path.join(TOOLS_DIR, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "main.py")):
            key = name.replace("-verify-tool", "").replace("-tool", "")
            tools[key] = name
    return tools


sessions={}

async def start(update:Update, ctx:ContextTypes.DEFAULT_TYPE):
    kb=[
      [InlineKeyboardButton("Spotify",callback_data="spotify"),
       InlineKeyboardButton("YouTube",callback_data="youtube")],
      [InlineKeyboardButton("💳 Balance",callback_data="balance")]
    ]
    await update.message.reply_text("Choose service:", reply_markup=InlineKeyboardMarkup(kb))

async def on_click(update:Update, ctx:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if q.data in TOOLS:
        sessions[q.from_user.id]=q.data
        await q.message.reply_text("Send URL:")
    elif q.data=="balance":
        r=requests.get(f"{API_URL}/balance/{q.from_user.id}")
        await q.message.reply_text(f"Balance: {r.json()['credits']} credits")

async def on_text(update:Update, ctx:ContextTypes.DEFAULT_TYPE):
    uid=update.message.from_user.id
    if uid not in sessions: return
    tool_key=sessions.pop(uid)
    tool=TOOLS[tool_key]
    url=update.message.text.strip()
    r=requests.post(f"{API_URL}/run", params={"user_id":uid,"tool":tool,"args":url})
    if r.status_code!=200:
        await update.message.reply_text(r.text); return
    d=r.json()
    await update.message.reply_text(f"Job {d['job_id']} queued. Remaining credits: {d['remaining_credits']}")

app=ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(on_click))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
app.run_polling()
