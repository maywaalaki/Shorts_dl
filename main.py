import os
import asyncio
import threading
import math
import time
from flask import Flask
from pyrogram import Client, filters
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
            body { background: #0f0f0f; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif; }
            .container { text-align: center; }
            h1 { color: #00ff88; font-size: 3rem; text-transform: uppercase; letter-spacing: 5px; animation: pulse 1.5s infinite alternate; }
            @keyframes pulse { from { opacity: 0.4; transform: scale(0.95); } to { opacity: 1; transform: scale(1.05); } }
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

bot = Client("video_dl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def format_size(size):
    if not size: return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size, 1024)))
    return f"{round(size / (1024**i), 2)} {units[i]}"

def progress_bar(current, total, status):
    percentage = current * 100 / total
    finished_blocks = int(percentage / 10)
    remaining_blocks = 10 - finished_blocks
    bar = "✅" * finished_blocks + "⬜" * remaining_blocks
    return f"**{status}**\n`{bar}` {round(percentage, 2)}%\n📦 `{format_size(current)}` / `{format_size(total)}`"

async def ydl_progress_hook(d, msg, last_update):
    if d['status'] == 'downloading':
        current_time = time.time()
        if current_time - last_update[0] < 4:
            return
        
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total:
            try:
                await msg.edit(progress_bar(downloaded, total, "📥 Soo dejinta"))
                last_update[0] = current_time
            except:
                pass

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("**Haye!** Iisoo dir linkiga muuqaalka aad rabto inaan kuu soo dejiyo.")

@bot.on_message(filters.text & ~filters.command("start"))
async def handler(client, message):
    url = message.text
    if not url.startswith(("http://", "https://")):
        return

    msg = await message.reply_text("⏳ **Xogta ayaan soo qaadayaa...**")
    last_update = [time.time()]

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video_%(id)s.%(ext)s',
        'writethumbnail': True,
        'quiet': True,
        'progress_hooks': [lambda d: asyncio.get_event_loop().create_task(ydl_progress_hook(d, msg, last_update))],
    }

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: YoutubeDL(ydl_opts).extract_info(url, download=True))
        filename = YoutubeDL(ydl_opts).prepare_filename(info)
        
        duration = int(info.get('duration', 0))
        width = int(info.get('width', 0))
        height = int(info.get('height', 0))

        thumb_path = None
        base_name = os.path.splitext(filename)[0]
        for ext in ['jpg', 'png', 'webp', 'jpeg']:
            p_thumb = f"{base_name}.{ext}"
            if os.path.exists(p_thumb):
                thumb_path = p_thumb
                break

        last_up = [time.time()]
        async def upload_progress(current, total):
            curr_t = time.time()
            if curr_t - last_up[0] < 4:
                return
            try:
                await msg.edit(progress_bar(current, total, "📤 Dirista"))
                last_up[0] = curr_t
            except:
                pass

        await client.send_video(
            chat_id=message.chat.id,
            video=filename,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb_path,
            progress=upload_progress,
            reply_to_message_id=message.id
        )

        if os.path.exists(filename): os.remove(filename)
        if thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ Khalad: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run()
