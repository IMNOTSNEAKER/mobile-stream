import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import mainthread
from kivy.core.window import Window
import webbrowser
import requests
import re
import threading

# ==========================================
# 1. ضع التوكن الخاص ببوت الديسكورد هنا
DISCORD_BOT_TOKEN = "https://discord.com/api/webhooks/1551491653498437662/ZKV710LxZs-7Q9BxZldPVP3qfnFF1oUIOv3S2tNXAmsP4e4U0Y9e1n7DawPzGHjVmp4F"

# 2. ضع الـ ID الخاص بالروم (Channel ID) هنا
CHANNEL_ID = "https://discord.com/channels/1397528479016423515/1551944120312926309"
# ==========================================

class RemoteControlApp(App):
    def build(self):
        self.title = "MobileStream Remote Control"
        # إعداد واجهة المستخدم
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.status_label = Label(
            text="حالة الاتصال: في انتظار جلب الرابط...", 
            font_size='16sp', 
            color=(1, 1, 0, 1)
        )
        layout.add_widget(self.status_label)
        
        self.url_input = TextInput(
            text="", 
            hint_text="الرابط سيظهر هنا تلقائياً...",
            multiline=False, 
            size_hint_y=None, 
            height=50
        )
        layout.add_widget(self.url_input)
        
        fetch_btn = Button(
            text="🔄 جلب الرابط من ديسكورد تلقائياً", 
            size_hint_y=None, 
            height=60, 
            background_color=(0.2, 0.6, 0.8, 1)
        )
        fetch_btn.bind(on_press=self.fetch_url_thread)
        layout.add_widget(fetch_btn)

        connect_btn = Button(
            text="🚀 فتح شاشة التحكم والملفات", 
            size_hint_y=None, 
            height=60, 
            background_color=(0, 0.8, 0.4, 1)
        )
        connect_btn.bind(on_press=self.open_url)
        layout.add_widget(connect_btn)
        
        return layout

    def fetch_url_thread(self, instance):
        self.status_label.text = "جاري الاتصال بديسكورد لجلب الرابط..."
        self.status_label.color = (1, 1, 0, 1)
        # تشغيل الجلب في Thread خارجي حتى لا يتجمد التطبيق
        threading.Thread(target=self.get_latest_url, daemon=True).start()

    def get_latest_url(self):
        headers = {
            "Authorization": f"Bot {DISCORD_BOT_TOKEN}"
        }
        try:
            # قراءة آخر 5 رسائل في الروم
            url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=5"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                messages = res.json()
                for msg in messages:
                    # تجميع النص للبحث عن رابط كلاودفلير
                    content_to_search = msg.get('content', '')
                    if msg.get('embeds'):
                        for embed in msg['embeds']:
                            if 'fields' in embed:
                                for field in embed['fields']:
                                    content_to_search += field.get('value', '')
                    
                    # البحث عن الرابط بصيغة trycloudflare
                    match = re.search(r"https://[a-zA-Z0-9\.\-]+\.trycloudflare\.com", content_to_search)
                    if match:
                        found_url = match.group(0)
                        self.update_ui_success(found_url)
                        return
                
                self.update_ui_error("لم يتم العثور على رابط في الروم.")
            else:
                self.update_ui_error(f"خطأ في الاتصال: تأكد من التوكن والـ ID ({res.status_code})")
        except Exception as e:
            self.update_ui_error(f"فشل الاتصال بالإنترنت!")

    @mainthread
    def update_ui_success(self, found_url):
        self.url_input.text = found_url
        self.status_label.text = "تم جلب الرابط بنجاح!"
        self.status_label.color = (0, 1, 0, 1)

    @mainthread
    def update_ui_error(self, error_msg):
        self.status_label.text = error_msg
        self.status_label.color = (1, 0, 0, 1)

    def open_url(self, instance):
        target_url = self.url_input.text.strip()
        if target_url.startswith("http"):
            webbrowser.open(target_url)
        else:
            self.status_label.text = "يرجى جلب الرابط أولاً!"
            self.status_label.color = (1, 0, 0, 1)

if __name__ == "__main__":
    RemoteControlApp().run()
