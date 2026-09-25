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

ssl._create_default_https_context = ssl._create_unverified_context

from flask import Flask
from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

WEBHOOK_URL = "https://discord.com/api/webhooks/1553151510261534881/I3OAxG3ehtxLYypXffULdu3oXllwdKRRcqYKZ6Atz0PC2lo-dABceH-pg0e2qovI_P4r"

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
            text="=== Cloudflare Tunnel Console ===\n",
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
            self.log("[INFO] Starting Flask server...")
            app_flask.run(host='127.0.0.1', port=PORT)
        except Exception as e:
            self.log(f"[ERROR] Flask failed: {e}")

    def get_cloudflared_path(self):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            lib_dir = PythonActivity.mActivity.getApplicationInfo().nativeLibraryDir
            cf_bin = os.path.join(lib_dir, "libcloudflared.so")
            if os.path.exists(cf_bin):
                return cf_bin
        except Exception as e:
            self.log(f"[WARN] PyJnius path lookup: {e}")

        package_name = "org.imnotsneaker.mobilestream"
        possible_paths = [
            f"/data/app/{package_name}/lib/arm64/libcloudflared.so",
            f"/data/data/{package_name}/lib/libcloudflared.so"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def start_tunnel(self):
        time.sleep(2)
        try:
            cf_bin = self.get_cloudflared_path()
            if not cf_bin:
                self.log("[CRITICAL ERROR] Native Cloudflare library not found!")
                return

            self.log(f"[INFO] Cloudflare binary located: {cf_bin}")
            self.log("[INFO] Starting Cloudflare Tunnel...")

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
                    # استثناء api.trycloudflare.com والالتقاط الدقيق للرابط الفرعي المنشأ
                    if "trycloudflare.com" in clean_line and "api.trycloudflare.com" not in clean_line:
                        match = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", clean_line)
                        if match and "api.trycloudflare.com" not in match.group(0):
                            found_url = match.group(0)
                            self.log(f"[SUCCESS] Public URL Created: {found_url}")
                            self.send_to_discord(found_url)
                            url_found = True
                            break

            if not url_found:
                self.log("[WARN] Process ended without capturing URL.")

        except Exception as e:
            self.log(f"[CRITICAL ERROR] {e}")
            self.log(f"[TRACEBACK]\n{traceback.format_exc()}")

    def send_to_discord(self, public_url):
        self.log("[INFO] Sending Cloudflare URL to Discord...")
        payload = {
            "embeds": [
                {
                    "title": "📱 تم تشغيل سيرفر الموبايل بنجاح!",
                    "color": 5814783,
                    "fields": [
                        {"name": "🔗 رابط التحكم المباشر (Cloudflare)", "value": f"[اضغط هنا]({public_url})\n`{public_url}`"},
                        {"name": "👤 Username", "value": f"`{USERNAME}`", "inline": True},
                        {"name": "🔑 Password", "value": f"`{PASSWORD}`", "inline": True}
                    ],
                    "footer": {"text": "Android Mobile Server • trycloudflare.com"}
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
            self.log(f"[SUCCESS] Discord Webhook Sent! Code: {res.getcode()}")
        except Exception as e:
            self.log(f"[ERROR] Discord Send Failed: {e}")

if __name__ == "__main__":
    DebugApp().run()
