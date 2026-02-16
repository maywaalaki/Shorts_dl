import os
import asyncio
import time
import re
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template_string
import edge_tts
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://lakiup3_db_user:V4Nbt6YcqH0qCBix@cluster0.my3ety2.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['somtts_web']
history_col = db['history']

app = Flask(__name__)
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def tiri_soomaali(n):
    n = int(n)
    if n == 0: return "eber"
    unugyada = ["", "kow", "laba", "saddex", "afar", "shan", "lix", "toddoba", "siddeed", "sagaal"]
    tobaneeyada = ["", "toban", "labaatan", "soddon", "afartan", "konton", "lixdan", "todobaatan", "sideetan", "sagaashan"]

    def badal(n, is_leading=False):
        if n < 10:
            if n == 1 and is_leading: return "hal"
            return unugyada[n]
        elif n < 20:
            if n == 10: return "toban"
            return f"{unugyada[n%10]} iyo toban"
        elif n < 100:
            harre = n % 10
            return f"{tobaneeyada[n//10]}" + (f" iyo {unugyada[harre]}" if harre > 0 else "")
        elif n < 1000:
            boqol = n // 100
            harre = n % 100
            bilow = "boqol" if boqol == 1 else f"{unugyada[boqol]} boqol"
            return bilow + (f" iyo {badal(harre)}" if harre > 0 else "")
        elif n < 1000000:
            kun = n // 1000
            harre = n % 1000
            bilow = "kun" if kun == 1 else f"{badal(kun, True)} kun"
            return bilow + (f" iyo {badal(harre)}" if harre > 0 else "")
        elif n < 1000000000:
            milyan = n // 1000000
            harre = n % 1000000
            bilow = "hal milyan" if milyan == 1 else f"{badal(milyan, True)} milyan"
            return bilow + (f" iyo {badal(milyan, True)} milyan" if harre > 0 else "")
        else:
            bilyan = n // 1000000000
            harre = n % 1000000000
            bilow = "hal bilyan" if bilyan == 1 else f"{badal(bilyan, True)} bilyan"
            return bilow + (f" iyo {badal(harre)}" if harre > 0 else "")

    return badal(n, True)

def hagaaji_qoraalka(text):
    text = text.lower()
    text = text.replace(",", "")

    def process_float_or_int(val):
        if '.' in val:
            bidix, midig = val.split('.')
            return f"{tiri_soomaali(bidix)} dhibic {tiri_soomaali(midig)}"
        return tiri_soomaali(val)

    def convert_dollars(match):
        num_str = match.group(1)
        return f"{process_float_or_int(num_str)} doolar"

    text = re.sub(r'\$(\d+\.?\d*)', convert_dollars, text)
    text = re.sub(r'(\d+\.?\d*)\$', convert_dollars, text)

    def convert_kmb(match):
        num = float(match.group(1))
        unit = match.group(2)
        if unit == 'k': return str(int(num * 1000))
        if unit == 'm': return str(int(num * 1000000))
        if unit == 'b': return str(int(num * 1000000000))
        return match.group(0)

    text = re.sub(r'(\d+\.?\d*)(k|m|b)\b', convert_kmb, text)

    def process_percent(match):
        val = match.group(1)
        return "boqolkiiba " + process_float_or_int(val)

    text = re.sub(r'(\d+\.?\d*)%', process_percent, text)
    text = re.sub(r'%(\d+\.?\d*)', process_percent, text)

    def final_number_fix(match):
        val = match.group(0)
        return process_float_or_int(val)

    text = re.sub(r'\b\d+\.?\d*\b', final_number_fix, text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SomTTS - Qoraal ilaa Cod</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'DM Sans', sans-serif; background-color: #f8fafc; }
        .glass-panel { background: white; border: 1px solid #e5e7eb; box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.05); }
        input[type=range] { -webkit-appearance: none; background: transparent; }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 6px; background: #e5e7eb; border-radius: 10px; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 18px; width: 18px; border-radius: 50%; background: #2563eb; cursor: pointer; margin-top: -6px; }
        .voice-active { border-color: #2563eb; background-color: #eff6ff; color: #2563eb; }
        .wave { display: flex; align-items: center; justify-content: center; gap: 4px; height: 50px; }
        .bar { width: 4px; height: 8px; background: #2563eb; border-radius: 10px; transition: height 0.2s ease; }
        .bar.animating { animation: wave 1s ease-in-out infinite; }
        @keyframes wave { 0%, 100% { height: 8px; } 50% { height: 40px; } }
    </style>
</head>
<body class="min-h-screen py-10 px-4">
    <div class="max-w-3xl mx-auto space-y-8">
        <div class="text-center space-y-2">
            <h1 class="text-4xl font-bold text-gray-900">SomTTS Web</h1>
            <p class="text-gray-500 font-medium">Qoraalka u bedel Cod Soomaaliyeed oo Dabiici ah</p>
        </div>

        <div class="glass-panel p-6 rounded-3xl space-y-6">
            <div class="grid grid-cols-3 gap-3">
                <button id="v_muuse" onclick="setVoice('Muuse')" class="voice-active flex flex-col items-center p-4 rounded-2xl border-2 transition-all">
                    <span class="text-2xl mb-1">👨🏻‍🦱</span>
                    <span class="font-bold text-sm">Muuse</span>
                </button>
                <button id="v_ubax" onclick="setVoice('Ubax')" class="flex flex-col items-center p-4 rounded-2xl border-2 border-gray-100 text-gray-400 transition-all">
                    <span class="text-2xl mb-1">👩🏻‍🦳</span>
                    <span class="font-bold text-sm">Ubax</span>
                </button>
                <button id="v_wiil" onclick="setVoice('Wiil')" class="flex flex-col items-center p-4 rounded-2xl border-2 border-gray-100 text-gray-400 transition-all">
                    <span class="text-2xl mb-1">👶🏻</span>
                    <span class="font-bold text-sm">Cod Wiil</span>
                </button>
            </div>

            <div class="space-y-2">
                <textarea id="textInput" oninput="checkInput()" class="w-full min-h-[150px] p-4 rounded-2xl border-2 border-gray-100 focus:border-blue-500 outline-none transition-all text-gray-700" placeholder="Ku qor halkan qoraalka... (Tusaale: $100, 50%)"></textarea>
            </div>

            <div class="grid grid-cols-2 gap-6 p-4 bg-gray-50 rounded-2xl" id="slidersBox">
                <div class="space-y-3">
                    <div class="flex justify-between text-xs font-bold text-gray-500">
                        <span>XAWAARAHA (RATE)</span><span id="rateLabel">0%</span>
                    </div>
                    <input type="range" id="rate" min="-50" max="50" value="0" oninput="updateUI()">
                </div>
                <div class="space-y-3">
                    <div class="flex justify-between text-xs font-bold text-gray-500">
                        <span>DHUUBNIDA (PITCH)</span><span id="pitchLabel">0Hz</span>
                    </div>
                    <input type="range" id="pitch" min="-50" max="50" value="0" oninput="updateUI()">
                </div>
            </div>

            <button id="genBtn" onclick="generate()" disabled class="w-full h-14 bg-gray-200 text-gray-400 font-bold rounded-2xl transition-all flex items-center justify-center gap-2">
                <i data-lucide="mic"></i><span>Samee Codka</span>
            </button>
        </div>

        <div id="playerBox" class="hidden glass-panel p-6 rounded-3xl space-y-6">
            <div class="wave" id="waveform"></div>
            <div class="flex items-center justify-center gap-6">
                <button onclick="document.getElementById('audio').currentTime=0" class="text-gray-400 hover:text-blue-600"><i data-lucide="rotate-ccw"></i></button>
                <button onclick="togglePlay()" class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white shadow-xl hover:scale-105 transition">
                    <i data-lucide="play" id="playIcon" class="fill-current"></i>
                </button>
                <a id="dlBtn" href="#" download class="text-gray-400 hover:text-blue-600"><i data-lucide="download"></i></a>
            </div>
            <audio id="audio" class="hidden"></audio>
        </div>
    </div>

    <script>
        let voice = 'Muuse';
        const a = document.getElementById('audio');
        const btn = document.getElementById('genBtn');

        function setVoice(v) {
            voice = v;
            ['muuse', 'ubax', 'wiil'].forEach(id => {
                document.getElementById('v_'+id).className = 'flex flex-col items-center p-4 rounded-2xl border-2 border-gray-100 text-gray-400 transition-all';
            });
            document.getElementById('v_'+v.toLowerCase()).className = 'voice-active flex flex-col items-center p-4 rounded-2xl border-2 transition-all';
            
            const box = document.getElementById('slidersBox');
            if(v === 'Wiil') {
                box.style.opacity = '0.5';
                box.style.pointerEvents = 'none';
            } else {
                box.style.opacity = '1';
                box.style.pointerEvents = 'auto';
            }
        }

        function checkInput() {
            if(document.getElementById('textInput').value.trim().length > 0) {
                btn.disabled = false;
                btn.className = "w-full h-14 bg-blue-600 text-white font-bold rounded-2xl shadow-lg shadow-blue-200 hover:-translate-y-1 transition-all flex items-center justify-center gap-2";
            } else {
                btn.disabled = true;
                btn.className = "w-full h-14 bg-gray-200 text-gray-400 font-bold rounded-2xl transition-all flex items-center justify-center gap-2";
            }
        }

        function updateUI() {
            document.getElementById('rateLabel').innerText = document.getElementById('rate').value + '%';
            document.getElementById('pitchLabel').innerText = document.getElementById('pitch').value + 'Hz';
        }

        async function generate() {
            btn.disabled = true;
            btn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i><span>Wuu samaynayaa...</span>';
            lucide.createIcons();
            
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: document.getElementById('textInput').value,
                    voice: voice,
                    rate: document.getElementById('rate').value,
                    pitch: document.getElementById('pitch').value
                })
            });
            const data = await res.json();
            
            document.getElementById('playerBox').classList.remove('hidden');
            a.src = data.audioUrl;
            document.getElementById('dlBtn').href = data.audioUrl;
            document.getElementById('waveform').innerHTML = Array.from({length: 20}).map(() => '<div class="bar"></div>').join('');
            
            btn.innerHTML = '<i data-lucide="mic"></i><span>Samee Codka</span>';
            checkInput();
            lucide.createIcons();
            a.play();
        }

        function togglePlay() {
            if(a.paused) a.play(); else a.pause();
        }

        a.onplay = () => {
            document.getElementById('playIcon').setAttribute('data-lucide', 'pause');
            document.querySelectorAll('.bar').forEach((b, i) => {
                b.classList.add('animating');
                b.style.animationDelay = `${i * 0.05}s`;
            });
            lucide.createIcons();
        };

        a.onpause = () => {
            document.getElementById('playIcon').setAttribute('data-lucide', 'play');
            document.querySelectorAll('.bar').forEach(b => b.classList.remove('animating'));
            lucide.createIcons();
        };

        lucide.createIcons();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json
    raw_text = data.get('text', '')
    voice_choice = data.get('voice', 'Muuse')
    rate_val = int(data.get('rate', 0))
    pitch_val = int(data.get('pitch', 0))

    text = hagaaji_qoraalka(raw_text.replace("!", ","))

    if voice_choice == 'Ubax':
        voice_name = "so-SO-UbaxNeural"
    else:
        voice_name = "so-SO-MuuseNeural"

    if voice_choice == 'Wiil':
        rate_val = 15
        pitch_val = 30

    r = f"+{rate_val}%" if rate_val >= 0 else f"{rate_val}%"
    p = f"+{pitch_val}Hz" if pitch_val >= 0 else f"{pitch_val}Hz"

    filename = f"Codka_{uuid.uuid4().hex[:8]}_{int(time.time())}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    async def make_tts():
        tts = edge_tts.Communicate(text, voice_name, rate=r, pitch=p)
        await tts.save(filepath)

    asyncio.run(make_tts())

    try:
        history_col.insert_one({
            "original_text": raw_text,
            "processed_text": text,
            "voice": voice_choice,
            "file": filename,
            "time": time.time()
        })
    except Exception:
        pass

    return jsonify({"audioUrl": f"/static/audio/{filename}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, threaded=True)
