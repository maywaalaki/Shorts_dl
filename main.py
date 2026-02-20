import os, asyncio, threading, requests
from flask import Flask, request, jsonify
from telethon import TelegramClient, events, types

API_ID = 29169428
API_HASH = '55742b16a85aac494c7944568b5507e5'
BOT_TOKEN = '8006815965:AAEb00GC21KEKbRaTz-_O_cvSlaMl2nhAwY'
HF_SERVER_URL = "https://lakiup3-ytdlsr.hf.space/download"
RENDER_URL = "https://shorts-dl-43fa.onrender.com"

bot = TelegramClient('video_dl_bot', API_ID, API_HASH)
app = Flask(__name__)
main_loop = None

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data.get("success") and main_loop:
        asyncio.run_coroutine_threadsafe(handle_stream_upload(data), main_loop)
        return jsonify({"status": "streaming"}), 200
    return jsonify({"status": "failed"}), 400

async def handle_stream_upload(data):
    chat_id = data.get("chat_id")
    video_url = data.get("video_url")
    title = data.get("title", "Video")
    
    try:
        with requests.get(video_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            
            # MUHIIM: Waxaan u diraynaa sidii Video dhab ah
            await bot.send_file(
                chat_id,
                r.raw,
                caption=f"**{title}**\n\n@ShortsDL_Bot",
                file_name="video.mp4", # Magaca halkan ha ahaado video.mp4
                supports_streaming=True,
                attributes=[types.DocumentAttributeVideo(
                    duration=0,
                    w=0,
                    h=0,
                    supports_streaming=True,
                )]
            )
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Cilad upload-ka: {e}")

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Soo dir link-ga video-ga!")

@bot.on(events.NewMessage)
async def handler(event):
    if event.text.startswith('http'):
        msg = await event.reply("👀 **Checking...**")
        payload = {"url": event.text, "chat_id": event.chat_id, "webhook": f"{RENDER_URL}/webhook"}
        try:
            res = requests.post(HF_SERVER_URL, json=payload, timeout=15)
            if res.status_code == 200: await msg.edit("😜 **Downloading & Uploading...**")
            else: await msg.edit("❌ HF Error.")
        except: await msg.edit("❌ Connection Error.")

async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()
    asyncio.run(main())
