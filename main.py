import socket
import threading
import json
import urllib.request
from flask import Flask, Response, request
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# ===== إعدادات السيرفر والأمان والديسكورد =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1551205294405582928/DI-CIWvAr1dYSICa5I0Gf6pmn0hTtUksrLaWtL5XXSyrYCOwBOmy8V0mazn_fDVVJ-bp"
PORT = 8080
USERNAME = "IMNOTSNEAKER"
PASSWORD = "3mko@3omar"

server_app = Flask(__name__)

def check_auth(username, password):
    """التحقق من اسم المستخدم وكلمة المرور"""
    return username == USERNAME and password == PASSWORD

def authenticate():
    """طلب تسجيل الدخول في حال لم يتم إدخال البيانات"""
    return Response(
        'Login Required', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

@server_app.route('/')
def home():
    # حماية الصفحة بكلمة سر
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
        
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Secure Server</title>
        <style>
            body { background-color: #121212; color: #ffffff; font-family: Arial; text-align: center; padding: 50px; }
            h1 { color: #00e676; }
        </style>
    </head>
    <body>
        <h1>Access Granted!</h1>
        <p>Logged in successfully to mobile server.</p>
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
            "title": "📱 Mobile Server Started Automatically!",
            "color": 5814783,
            "fields": [
                {"name": "🔗 Link", "value": f"`{url}`", "inline": False},
                {"name": "👤 Username", "value": f"`{USERNAME}`", "inline": True},
                {"name": "🔑 Password", "value": f"`{PASSWORD}`", "inline": True}
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
        print("Sent to Discord successfully.")
    except Exception as e:
        print(f"Discord Error: {e}")

class AutoServerApp(App):
    def build(self):
        self.title = "Auto Server"
        
        # تشغيل السيرفر وإرسال البيانات للديسكورد فوراً في الخلفية بمجرد فتح التطبيق
        ip = get_local_ip()
        threading.Thread(target=run_flask, daemon=True).start()
        threading.Thread(target=send_to_discord, args=(ip,), daemon=True).start()

        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        self.status_label = Label(
            text=f"Server is Running!\n\nIP:\nhttp://{ip}:{PORT}",
            font_size='18sp',
            halign='center'
        )
        layout.add_widget(self.status_label)
        
        return layout

if __name__ == '__main__':
    AutoServerApp().run()
