import os
import asyncio
import threading
import requests
from flask import Flask
from telethon import TelegramClient, events

API_ID = 29169428
API_HASH = '55742b16a85aac494c7944568b5507e5'
BOT_TOKEN = '8006815965:AAEb00GC21KEKbRaTz-_O_cvSlaMl2nhAwY'
SERVER_API_URL = "https://lakiup3-ytdlsr.hf.space/api?url="

bot = TelegramClient('video_dl_bot', API_ID, API_HASH)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running! 🚀"

def run_web():
    app.run(host='0.0.0.0', port=8080)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("**Haye!** Iisoo dir linkiga TikTok, Instagram ama Pinterest.")

@bot.on(events.NewMessage)
async def handler(event):
    if event.text.startswith('/start') or not event.text.startswith("http"):
        return
        
    url = event.text
    msg = await event.reply("⏳ **Processing... Linkiga ayaan hubinayaa.**")

    try:
        response = requests.get(f"{SERVER_API_URL}{url}", timeout=25)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                direct_link = data.get("direct_url")
                
                await msg.edit("📥 **Telegram ayaa hadda soo dejinaya muuqaalka...**")
                
                await bot.send_file(
                    event.chat_id, 
                    direct_link, 
                    caption="Halkan ka daawo muuqaalkaaga! ✅",
                    supports_streaming=True,
                    reply_to=event.id
                )
                await msg.delete()
            else:
                await msg.edit("❌ Server-ka ayaa ku fashilmay inuu helo muuqaalkaas.")
        else:
            await msg.edit("❌ Server-ka HF ayaa cilad bixiyay.")

    except Exception as e:
        await msg.edit(f"❌ Khalad ayaa dhacay xilli la xiriirayay server-ka.")

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(main())
