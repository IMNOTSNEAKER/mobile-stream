import json
import re
import socket
import select
import threading
import time
import urllib.request
import paramiko
from flask import Flask, Response, request
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# ===== 1. بيانات الأمان والإعدادات =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1551491653498437662/ZKV710LxZs-7Q9BxZldPVP3qfnFF1oUIOv3S2tNXAmsP4e4U0Y9e1n7DawPzGHjVmp4F"
USERNAME = "IMNOTSNEAKER"
PASSWORD = "3mko@3omar"
PORT = 8080

app = Flask(__name__)
public_url_global = "Generating link..."


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
        <title>Mobile Server Public Access</title>
        <style>
            body { margin: 0; background: #121212; color: #00e676; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; }
            .box { background: #1e1e1e; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            h1 { margin-bottom: 10px; }
            p { color: #ccc; }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>Connected via Public Internet!</h1>
            <p>Mobile Data Server Access Granted.</p>
        </div>
    </body>
    </html>
    '''


def run_flask():
    try:
        app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask Error: {e}")


def send_to_discord(public_url):
    if not WEBHOOK_URL or "discord" not in WEBHOOK_URL:
        return

    payload = {
        "embeds": [
            {
                "title": "🌐 Public Mobile Server Live!",
                "color": 5814783,
                "fields": [
                    {
                        "name": "🔗 Public Internet Link",
                        "value": f"[Open Server]({public_url})\n`{public_url}`",
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
                "footer": {"text": "Mobile Data Tunnel • Active"},
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
        print(f"Discord Error: {e}")


def forward_stream(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception:
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


def start_ssh_tunnel(app_instance):
    global public_url_global
    time.sleep(1.5)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # الاتصال بخدمة Pinggy المجانية عبر منفذ SSH
        client.connect('a.pinggy.io', port=443, username='a', password='', timeout=15)
        transport = client.get_transport()
        transport.request_port_forward('', PORT)

        chan = client.invoke_shell()

        url_sent = False
        def read_output():
            nonlocal url_sent
            global public_url_global
            while True:
                if chan.recv_ready():
                    data = chan.recv(2048).decode('utf-8', errors='ignore')
                    match = re.search(r'https://[a-zA-Z0-9\.-]+\.pinggy\.link', data)
                    if match and not url_sent:
                        public_url_global = match.group(0)
                        url_sent = True
                        send_to_discord(public_url_global)
                        if app_instance and hasattr(app_instance, 'status_label'):
                            app_instance.status_label.text = f"Server Active on Mobile Data!\n\nPublic Link:\n{public_url_global}"
                time.sleep(0.5)

        threading.Thread(target=read_output, daemon=True).start()

        while True:
            chan_channel = transport.accept(1000)
            if chan_channel is None:
                continue
            threading.Thread(
                target=forward_stream,
                args=(chan_channel, '127.0.0.1', PORT),
                daemon=True,
            ).start()

    except Exception as e:
        print(f"Tunnel Connection Failed: {e}")


class MainApp(App):

    def build(self):
        self.title = "Mobile Public Server"

        # تشغيل السيرفر والنفق في الخلفية
        threading.Thread(target=run_flask, daemon=True).start()
        threading.Thread(target=start_ssh_tunnel, args=(self,), daemon=True).start()

        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        self.status_label = Label(
            text="Starting Public Tunnel...\nPlease wait...",
            font_size='16sp',
            halign='center',
        )
        layout.add_widget(self.status_label)
        return layout


if __name__ == "__main__":
    MainApp().run()
