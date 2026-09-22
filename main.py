import json
import os
import random
import re
import select
import socket
import ssl
import string
import threading
import time
import traceback
import urllib.request

# تجاوز مشكلة شهادات SSL
ssl._create_default_https_context = ssl._create_unverified_context

import paramiko
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
            text="=== Android Tunnel Console ===\n",
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
        threading.Thread(target=self.start_ssh_tunnel, daemon=True).start()

    def run_flask(self):
        try:
            self.log("[INFO] Starting Flask server on port 5000...")
            app_flask.run(host='127.0.0.1', port=PORT)
        except Exception as e:
            self.log(f"[ERROR] Flask failed: {e}")

    def start_ssh_tunnel(self):
        time.sleep(2)
        self.log("[INFO] Connecting to SSH Tunnel (Serveo.net)...")
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # الاتصال بخدمة serveo لإنشاء النفق بدون ملفات exe أو binary
            client.connect('serveo.net', port=22, username='', password='', timeout=15)
            
            transport = client.get_transport()
            remote_port = transport.request_port_forward('', 80)
            
            self.log("[SUCCESS] SSH Tunnel connected successfully!")
            
            # الرابط العام الناتج
            public_url = f"https://serveo.net"
            self.send_to_discord(public_url)

            # الاستمرار في تمرير الحزم بين السيرفر المحلي والنفق
            while True:
                chan = transport.accept(1000)
                if chan is None:
                    continue
                thr = threading.Thread(target=self.handler, args=(chan,))
                thr.daemon = True
                thr.start()

        except Exception as e:
            self.log(f"[ERROR] Tunnel failed: {e}")
            self.log(f"[TRACEBACK]\n{traceback.format_exc()}")

    def handler(self, chan):
        sock = socket.socket()
        try:
            sock.connect(('127.0.0.1', PORT))
        except Exception as e:
            chan.close()
            return

        while True:
            r, w, x = select.select([sock, chan], [], [])
            if sock in r:
                data = sock.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                sock.send(data)
        chan.close()
        sock.close()

    def send_to_discord(self, public_url):
        self.log("[INFO] Sending URL to Discord Webhook...")
        payload = {
            "embeds": [
                {
                    "title": "📱 تم تشغيل سيرفر الموبايل بنجاح!",
                    "color": 5814783,
                    "fields": [
                        {"name": "🔗 رابط التحكم المباشر", "value": f"`{public_url}`"},
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
            self.log(f"[SUCCESS] Discord Webhook Sent! Status Code: {res.getcode()}")
        except Exception as e:
            self.log(f"[ERROR] Webhook failed: {e}")

if __name__ == "__main__":
    DebugApp().run()
