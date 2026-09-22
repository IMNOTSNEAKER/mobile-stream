import json
import socket
import threading
import time
import urllib.request
from flask import Flask, Response, request
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# ===== 1. رابط الـ Webhook الخاص بك في ديسكورد =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1551491653498437662/ZKV710LxZs-7Q9BxZldPVP3qfnFF1oUIOv3S2tNXAmsP4e4U0Y9e1n7DawPzGHjVmp4F"

# ===== 2. بيانات الأمان =====
USERNAME = "IMNOTSNEAKER"
PASSWORD = "3mko@3omar"
PORT = 8080

app = Flask(__name__)


def check_auth(username, password):
    return username == USERNAME and password == PASSWORD


def authenticate():
    return Response(
        'Login Required',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'},
    )


@app.route('/')
def index():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mobile Server Share</title>
        <style>
            body { margin: 0; background: #121212; color: #00e676; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; }
            .box { background: #1e1e1e; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            h1 { margin-bottom: 10px; }
            p { color: #ccc; }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>Mobile Server Active</h1>
            <p>Connection established successfully.</p>
        </div>
    </body>
    </html>
    '''


def run_flask():
    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server error: {e}")


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def send_to_discord(server_url):
    if not WEBHOOK_URL or "discord" not in WEBHOOK_URL:
        return

    payload = {
        "embeds": [
            {
                "title": "📱 Server Started Automatically!",
                "color": 5814783,
                "fields": [
                    {
                        "name": "🔗 Connection Link",
                        "value": f"[Click Here]({server_url})\n`{server_url}`",
                    },
                    {
                        "name": "👤 Username",
                        "value": f"`{USERNAME}`",
                        "inline": True,
                    },
                    {
                        "name": "🔑 Password",
                        "value": f"`{PASSWORD}`",
                        "inline": True,
                    },
                ],
                "footer": {"text": "Mobile App • Running in background"},
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
        print(f"Discord error: {e}")


def initialize_background():
    time.sleep(1)
    ip = get_local_ip()
    local_url = f"http://{ip}:{PORT}"
    send_to_discord(local_url)


class MainApp(App):

    def build(self):
        self.title = "Mobile Server"

        # تشغيل السيرفر وإرسال رابط الديسكورد تلقائياً فور فتح التطبيق
        threading.Thread(target=run_flask, daemon=True).start()
        threading.Thread(target=initialize_background, daemon=True).start()

        ip = get_local_ip()

        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        self.status_label = Label(
            text=f"Server Running Automatically!\n\nAccess Link:\nhttp://{ip}:{PORT}",
            font_size='18sp',
            halign='center',
        )
        layout.add_widget(self.status_label)
        return layout


if __name__ == "__main__":
    MainApp().run()
