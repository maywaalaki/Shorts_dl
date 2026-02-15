import os
import threading
import time
import requests
from flask import Flask, Response, jsonify
from pyrogram import Client, filters
from yt_dlp import YoutubeDL

API_ID = int(os.environ.get("API_ID", "29169428"))
API_HASH = os.environ.get("API_HASH", "55742b16a85aac494c7944568b5507e5")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8380607635:AAE9PexZaUMYqpmfZ3FpkvS2ywbyDErSHYE")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
WEB_URL = os.environ.get("WEB_URL", f"http://{os.environ.get('HOST','localhost')}:{PORT}/")
COOKIE_FILE = os.environ.get("COOKIE_FILE", "cookies.txt")
COOKIE_TEXT = os.environ.get("COOKIE_TEXT", "")

if COOKIE_TEXT:
    try:
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write(COOKIE_TEXT)
    except Exception:
        pass

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Bot Status</title><style>body{font-family:Inter,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#0f1724;color:#e6eef8;display:flex;align-items:center;justify-content:center;height:100vh;margin:0} .frame{width:360px;height:720px;border-radius:28px;padding:22px;background:linear-gradient(180deg,rgba(255,255,255,0.03),rgba(0,0,0,0.12));box-shadow:0 10px 30px rgba(2,6,23,0.6),inset 0 1px 0 rgba(255,255,255,0.02);display:flex;flex-direction:column;gap:18px;align-items:center} .status{width:100%;display:flex;flex-direction:column;align-items:center;gap:12px} .title{font-size:18px;font-weight:700} .badge{padding:6px 12px;border-radius:999px;background:linear-gradient(90deg,#06b6d4,#7c3aed);font-weight:600;font-size:13px} .screen{width:100%;height:420px;background:linear-gradient(180deg,#081025,#051226);border-radius:14px;padding:18px;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;border:1px solid rgba(255,255,255,0.03)} .pulse{width:88px;height:88px;border-radius:999px;background:radial-gradient(circle at 30% 30%,rgba(124,58,237,0.18),transparent 30%),radial-gradient(circle at 70% 70%,rgba(6,182,212,0.12),transparent 30%);display:flex;align-items:center;justify-content:center;position:relative;overflow:visible;animation:pulse 2.6s infinite} .dot{width:18px;height:18px;border-radius:50%;background:#fff;transform:scale(.95);box-shadow:0 6px 18px rgba(124,58,237,0.18);animation:breathe 1.6s infinite} .dots{display:flex;gap:10px;align-items:center;justify-content:center} @keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.06)}100%{transform:scale(1)}} @keyframes breathe{0%{transform:translateY(0) scale(.95);opacity:.9}50%{transform:translateY(-8px) scale(1.05);opacity:1}100%{transform:translateY(0) scale(.95);opacity:.9}} .hint{font-size:13px;color:rgba(230,238,248,0.78);text-align:center;padding:0 8px} .action{display:flex;gap:8px} .btn{padding:10px 14px;border-radius:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.03);font-weight:700;cursor:pointer} .small{font-size:12px;color:rgba(230,238,248,0.6)}</style></head><body><div class="frame"><div class="status"><div class="title">Video Download Bot</div><div class="badge">Running</div></div><div class="screen" role="region" aria-label="bot status screen"><div class="pulse" aria-hidden="true"><div class="dots"><div class="dot" style="animation-delay:0s"></div><div class="dot" style="animation-delay:.2s"></div><div class="dot" style="animation-delay:.4s"></div></div></div><div class="hint">Botka wuu ordayaa. Waxay u muuqataa sida app, laakiin waa adeeg software oo server ku shaqeeya. Si uu u ekaado app, fur boggan fullscreen ama ku dar sida webview app gudaha mobile.</div><div class="action"><button class="btn" onclick="copyUrl()">Copy Link</button><div class="small" id="copied"> </div></div></div><div style="font-size:12px;color:rgba(230,238,248,0.6);text-align:center">URL: <span id="urlText"></span></div></div><script>function copyUrl(){navigator.clipboard.writeText(location.href).then(()=>{const c=document.getElementById('copied');c.textContent='Link la koobiyey';setTimeout(()=>c.textContent='',2000)})}document.getElementById('urlText').textContent=location.href</script></body></html>"""

flask_app = Flask("video_bot_web")

@flask_app.route("/")
def root():
    return Response(HTML, mimetype="text/html")

@flask_app.route("/status")
def status():
    cookie_present = os.path.exists(COOKIE_FILE)
    data = {"status":"running","bot":"video_download_bot","web_url":WEB_URL,"cookie_file":COOKIE_FILE,"cookie_present":cookie_present}
    return jsonify(data)

@flask_app.route("/health")
def health():
    return "ok", 200

def run_flask():
    flask_app.run(host=HOST, port=PORT, threaded=True)

bot = Client("video_dl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

@bot.on_message(filters.command("start"))
async def start(client, message):
    welcome_text = "**Haye Laki!** Iisoo dir linkiga muuqaalka aad rabto inaan kuu soo dejiyo."
    await message.reply_text(welcome_text, quote=True)

@bot.on_message(filters.command("web"))
async def web_command(client, message):
    url = WEB_URL
    await message.reply_text(f"Web status bogga: {url}", quote=True)

@bot.on_message(filters.text & ~filters.command(["start","web"]))
async def handler(client, message):
    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        return
    msg = await message.reply_text("⏳ **Waan ku guda jiraa, fadlan sug...**", quote=True)
    ydl_opts = {
        "format": "best",
        "outtmpl": "video_%(id)s.%(ext)s",
        "quiet": True,
        "noplaylist": True
    }
    if os.path.exists(COOKIE_FILE):
        ydl_opts["cookiefile"] = COOKIE_FILE
    filename = None
    thumb_filename = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get("title", "Video")
            width, height, duration = extract_metadata_from_info(info)
            thumbnail_url = info.get("thumbnail")
            if not thumbnail_url:
                thumbs = info.get("thumbnails") or []
                if thumbs:
                    last = thumbs[-1]
                    if isinstance(last, dict):
                        thumbnail_url = last.get("url") or last.get("thumbnail_url")
            if thumbnail_url:
                try:
                    r = requests.get(thumbnail_url, timeout=15, stream=True)
                    if r.status_code == 200:
                        ext = os.path.splitext(thumbnail_url.split("?")[0])[1]
                        if not ext or ext.lower() not in [".jpg", ".jpeg", ".png"]:
                            ext = ".jpg"
                        thumb_filename = f"thumb_{info.get('id')}{ext}"
                        with open(thumb_filename, "wb") as tf:
                            for chunk in r.iter_content(8192):
                                if not chunk:
                                    continue
                                tf.write(chunk)
                except Exception:
                    thumb_filename = None
            caption = f" **{title}**"
            await message.reply_video(
                video=filename,
                caption=caption,
                duration=int(duration) if duration else 0,
                width=int(width) if width else 0,
                height=int(height) if height else 0,
                supports_streaming=True,
                thumb=thumb_filename,
                quote=True
            )
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
        if thumb_filename and os.path.exists(thumb_filename):
            try:
                os.remove(thumb_filename)
            except Exception:
                pass
        await msg.delete()
    except Exception as e:
        try:
            await msg.edit_text(f"❌ Khalad ayaa dhacay: {str(e)}")
        except Exception:
            pass
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass
        if thumb_filename and os.path.exists(thumb_filename):
            try:
                os.remove(thumb_filename)
            except Exception:
                pass

if __name__ == "__main__":
    thread = threading.Thread(target=run_flask, daemon=True)
    thread.start()
    time.sleep(0.5)
    bot.run()
