import os
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo
from yt_dlp import YoutubeDL

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot Status</title>
        <style>
            body { 
                background: #0f0f0f; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                margin: 0; 
                font-family: sans-serif;
            }
            .container { text-align: center; }
            h1 {
                color: #00ff88;
                font-size: 3rem;
                text-transform: uppercase;
                letter-spacing: 5px;
                animation: pulse 1.5s infinite alternate;
            }
            @keyframes pulse {
                from { opacity: 0.4; transform: scale(0.95); }
                to { opacity: 1; transform: scale(1.05); }
            }
            p { color: white; font-size: 1.2rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>I'M RUNNING</h1>
            <p>Laki, Your Video Downloader Bot is Active! 🚀</p>
        </div>
    </body>
    </html>
    """

def run_web():
    app.run(host='0.0.0.0', port=8080)

API_ID = 29169428
API_HASH = '55742b16a85aac494c7944568b5507e5'
BOT_TOKEN = '8504050677:AAF1JM3DBMAZLPuWcpyKmCU3yot0uPrAvTc'

bot = TelegramClient('video_dl_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def extract_metadata_from_info(info):
    width = info.get("width")
    height = info.get("height")
    duration = info.get("duration")
    if not width or not height:
        formats = info.get("formats") or []
        for f in formats:
            if f.get("width") and f.get("height"):
                width = f.get("width")
                height = f.get("height")
                break
    return width, height, duration

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("**Haye!** Iisoo dir linkiga muuqaalka aad rabto inaan kuu soo dejiyo,")

@bot.on(events.NewMessage)
async def handler(event):
    url = event.text
    if not url.startswith(("http://", "https://")):
        return

    msg = await event.reply("⏳ **Waan ku guda jiraa, fadlan sug...**")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video_%(id)s.%(ext)s',
        'writethumbnail': True,
        'quiet': True,
        'cookiefile': 'cookies.txt'
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Video')
            width, height, duration = extract_metadata_from_info(info)
            
            thumb_path = None
            for ext in ['jpg', 'png', 'webp', 'jpeg']:
                potential_thumb = filename.rsplit('.', 1)[0] + f".{ext}"
                if os.path.exists(potential_thumb):
                    thumb_path = potential_thumb
                    break

            caption = f" **{title}**"

            attr = []
            if width and height and duration:
                attr.append(DocumentAttributeVideo(
                    duration=int(duration),
                    w=int(width),
                    h=int(height),
                    supports_streaming=True
                ))

            await bot.send_file(
                event.chat_id, 
                filename, 
                caption=caption,
                thumb=thumb_path,
                supports_streaming=True,
                attributes=attr
            )

        if os.path.exists(filename):
            os.remove(filename)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
            
        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ Khalad ayaa dhacay: {str(e)}")

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    bot.run_until_disconnected()
