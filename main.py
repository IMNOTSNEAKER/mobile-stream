import socket
import threading
from flask import Flask
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

# ===== 1. إعداد سيرفر Flask =====
server_app = Flask(__name__)
is_server_running = False


@server_app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة التحكم</title>
        <style>
            body { 
                background-color: #121212; 
                color: #ffffff; 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 40px; 
            }
            .card { 
                background: #1e1e1e; 
                padding: 25px; 
                border-radius: 12px; 
                display: inline-block; 
                box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            }
            h1 { color: #00e676; }
            p { font-size: 18px; color: #ccc; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>تم الاتصال بنجاح!</h1>
            <p>سيرفر Flask يعمل على الهاتف وجاهز لاستقبال البيانات.</p>
        </div>
    </body>
    </html>
    '''


def run_flask():
    """تشغيل سيرفر Flask على البورت 8080"""
    try:
        server_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception as e:
        print(f"خطأ في السيرفر: {e}")


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


# ===== 2. إعداد واجهة Kivy =====
class ServerControlApp(App):

    def build(self):
        self.title = "Server Controller"

        # التصميم الرئيسي (راسي)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

        # عنوان الواجهة
        self.title_label = Label(
            text="تطبيق التحكم بالسيرفر",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.2),
        )
        layout.add_widget(self.title_label)

        # نص حالة السيرفر
        self.status_label = Label(
            text="الحالة: متوقف\nالرابط: ---",
            font_size='16sp',
            halign='center',
            size_hint=(1, 0.4),
        )
        layout.add_widget(self.status_label)

        # زر التحكم
        self.toggle_btn = Button(
            text="تشغيل السيرفر",
            font_size='18sp',
            bold=True,
            background_color=(0, 0.7, 0.3, 1),
            size_hint=(1, 0.2),
        )
        self.toggle_btn.bind(on_press=self.toggle_server)
        layout.add_widget(self.toggle_btn)

        return layout

    def toggle_server(self, instance):
        global is_server_running

        if not is_server_running:
            # بدء السيرفر في Thread منفصل
            is_server_running = True
            threading.Thread(target=run_flask, daemon=True).start()

            ip = get_local_ip()
            self.status_label.text = (
                f"الحالة: يعمل الآن\nالرابط المحلي: http://{ip}:8080"
            )
            self.toggle_btn.text = "السيرفر قيد التشغيل"
            self.toggle_btn.background_color = (0.2, 0.6, 1, 1)
            self.toggle_btn.disabled = True  # تعطيل الزر لمنع التكرار
        else:
            pass


if __name__ == '__main__':
    ServerControlApp().run()
