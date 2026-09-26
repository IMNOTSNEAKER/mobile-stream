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
            text="=== Mobile Tunnel Console ===\n",
            size_hint_y=None,
            font_size='11sp',
            color=(0, 1, 0, 1),
            halign='left',
            valign='top'
        )
        self.log_label.bind(width=lambda instance, value: setattr(instance, 'text_size', (value - 20, None)))
        self.log_label.bind(texture_size=lambda instance, value: setattr(instance, 'size', value))
        self.scroll.add_widget(self.log_label)
        return self.scroll

    @mainthread
    def log(self, text):
        print(text)
        self.log_label.text += f"{text}\n"

    def on_start(self):
        self.log(f"[CREDENTIALS] User: {USERNAME} | Pass: {PASSWORD}")
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
            self.log(f"[WARN] PyJnius lookup: {e}")

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
                self.log("[CRITICAL ERROR] libcloudflared.so not found!")
                return

            self.log(f"[INFO] Cloudflare binary path: {cf_bin}")
            self.log("[INFO] Starting Cloudflare Tunnel via Direct Pipe...")

            cmd = [
                cf_bin, "tunnel",
                "--no-autoupdate",
                "--protocol", "http2",
                "--edge-ip-version", "4",
                "--url", f"http://127.0.0.1:{PORT}"
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            url_found = False

            # قراءة مخرجات السيرفر مباشرة وبدون تخزين مؤقت
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                line_str = line.strip()

                if "trycloudflare.com" in line_str or "ERROR" in line_str or "ERR" in line_str:
                    self.log(f"[CF] {line_str[:120]}")

                matches = re.findall(r"https://[a-zA-Z0-9\.\-]+\.trycloudflare\.com", line_str)
                for url in matches:
                    if "api.trycloudflare.com" not in url:
                        self.log(f"[SUCCESS] Public URL: {url}")
                        self.send_to_discord(url)
                        url_found = True
                        break

                if url_found:
                    break

            if not url_found:
                self.log("[WARN] Cloudflare tunnel process ended.")

        except Exception as e:
            self.log(f"[ERROR] {e}")
            self.log(f"[TRACEBACK]\n{traceback.format_exc()}")

    def send_to_discord(self, public_url):
        self.log("[INFO] Sending URL to Discord Webhook...")
        payload = {
            "embeds": [
                {
                    "title": "📱 تم تشغيل سيرفر الموبايل بنجاح!",
                    "color": 5814783,
                    "fields": [
                        {"name": "🔗 رابط التحكم المباشر", "value": f"[اضغط هنا]({public_url})\n`{public_url}`"},
                        {"name": "👤 Username", "value": f"`{USERNAME}`", "inline": True},
                        {"name": "🔑 Password", "value": f"`{PASSWORD}`", "inline": True}
                    ],
                    "footer": {"text": "Android Mobile Server"}
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
            self.log(f"[SUCCESS] Discord Webhook Status: {res.getcode()}")
        except Exception as e:
            self.log(f"[ERROR] Discord Webhook Failed: {e}")

if __name__ == "__main__":
    DebugApp().run()
