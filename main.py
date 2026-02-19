import os
import asyncio
import threading
import requests
from flask import Flask, request, jsonify
from telethon import TelegramClient, events

API_ID = 29169428
API_HASH = '55742b16a85aac494c7944568b5507e5'
BOT_TOKEN = '8006815965:AAEb00GC21KEKbRaTz-_O_cvSlaMl2nhAwY'
HF_SERVER_URL = "https://lakiup3-ytdlsr.hf.space/download"
RENDER_URL = "https://shorts-dl-43fa.onrender.com"

bot = TelegramClient('video_dl_bot', API_ID, API_HASH)
app = Flask(__name__)
main_loop = None

@app.route('/')
def home():
    return "Bot is Running! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    chat_id = data.get("chat_id")
    video_url = data.get("video_url")
    title = data.get("title", "Video")
    success = data.get("success")

    if success and video_url and main_loop:
        asyncio.run_coroutine_threadsafe(
            bot.send_file(
                chat_id, 
                video_url, 
                caption=f"**{title}**\n\nDownloaded by @ShortsDL_Bot",
                supports_streaming=True
            ), main_loop
        )
        return jsonify({"status": "sending"}), 200
    return jsonify({"status": "failed"}), 400

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Welcome 👋

This bot lets you download videos from
YouTube, TikTok, Instagram, and more.

👉 Just send the video link")

@bot.on(events.NewMessage)
async def handler(event):
    if event.text.startswith('/start') or not event.text.startswith("http"):
        return
        
    url = event.text
    msg = await event.reply("👀 ** Checking **")

    payload = {
        "url": url,
        "chat_id": event.chat_id,
        "webhook": f"{RENDER_URL}/webhook"
    }

    try:
        response = requests.post(HF_SERVER_URL, json=payload, timeout=10)
        if response.status_code == 200:
            await msg.edit("😜 **Downloading**")
        else:
            await msg.edit("❌ Cilad Server-ka ah.")
    except Exception:
        await msg.edit("❌ Khalad: Server-ka lama heli karo.")

async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(main())
