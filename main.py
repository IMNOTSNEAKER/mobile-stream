import socket
import threading
import json
import urllib.request
from flask import Flask
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# ===== إعدادات السيرفر والديسكورد =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1551491653498437662/ZKV710LxZs-7Q9BxZldPVP3qfnFF1oUIOv3S2tNXAmsP4e4U0Y9e1n7DawPzGHjVmp4F"
PORT = 8080

server_app = Flask(__name__)

@server_app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Server Connected</title>
        <style>
            body { background-color: #121212; color: #ffffff; font-family: Arial; text-align: center; padding: 50px; }
            h1 { color: #00e676; }
        </style>
    </head>
    <body>
        <h1>Connected Successfully!</h1>
        <p>Flask server is running on mobile.</p>
    </body>
    </html>
    '''

def run_flask():
    try:
        server_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server Error: {e}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def send_to_discord(ip):
    url = f"http://{ip}:{PORT}"
    payload = {
        "embeds": [{
            "title": "📱 Server Started Automatically!",
            "color": 5814783,
            "fields": [
                {"name": "🔗 Link", "value": f"`{url}`"},
            ]
        }]
    }
    try:
        req = urllib.request.Request(
            WEBHOOK_URL, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Discord Error: {e}")

class AutoServerApp(App):
    def build(self):
        self.title = "Auto Server"
        
        # تشغيل السيرفر وإرسال الديسكورد تلقائياً فور فتح التطبيق
        ip = get_local_ip()
        threading.Thread(target=run_flask, daemon=True).start()
        threading.Thread(target=send_to_discord, args=(ip,), daemon=True).start()

        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        # استخدام اللغة الإنجليزية لتجنب ظهور المربعات
        self.status_label = Label(
            text=f"Server is Running Automatically!\n\nLocal IP:\nhttp://{ip}:{PORT}",
            font_size='18sp',
            halign='center'
        )
        layout.add_widget(self.status_label)
        
        return layout

if __name__ == '__main__':
    AutoServerApp().run()
