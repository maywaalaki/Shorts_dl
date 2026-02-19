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
RENDER_URL = "https://your-app-name.onrender.com"

bot = TelegramClient('video_dl_bot', API_ID, API_HASH)
app = Flask(__name__)

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

    if success and video_url:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.send_file(
            chat_id, 
            video_url, 
            caption=f"✅ **{title}**\n\nHalkan ka daawo muuqaalkaaga!",
            supports_streaming=True
        ))
    return jsonify({"status": "ok"}), 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("**Haye Laki!** Iisoo dir linkiga TikTok, Instagram ama Pinterest si aan HF Engine ugu diro.")

@bot.on(events.NewMessage)
async def handler(event):
    if event.text.startswith('/start') or not event.text.startswith("http"):
        return
        
    url = event.text
    msg = await event.reply("⏳ **Codsigaaga waxaa loo diray HF Engine (16GB RAM)...**")

    payload = {
        "url": url,
        "chat_id": event.chat_id,
        "webhook": f"{RENDER_URL}/webhook"
    }

    try:
        response = requests.post(HF_SERVER_URL, json=payload, timeout=10)
        if response.status_code == 200:
            await msg.edit("📥 **HF waa uu bilaabay soo dejinta. Markuu dhameeyo Telegram ayaa si toos ah kuugu soo diri doona.**")
        else:
            await msg.edit("❌ Cilad ayaa ka dhacday la xiriirka Engine-ka.")
    except Exception as e:
        await msg.edit(f"❌ Khalad: Server-ka Engine-ka ma shaqaynayo.")

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(main())
