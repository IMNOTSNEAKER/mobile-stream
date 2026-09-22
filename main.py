import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window
import webbrowser

class RemoteControlApp(App):
    def build(self):
        self.title = "MobileStream Remote Control"
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text="أدخل رابط التحكم (Cloudflare URL):", font_size='18sp'))
        
        self.url_input = TextInput(
            text="https://", 
            multiline=False, 
            size_hint_y=None, 
            height=50
        )
        layout.add_widget(self.url_input)
        
        btn = Button(
            text="فتح شاشة التحكم والملفات", 
            size_hint_y=None, 
            height=60, 
            background_color=(0, 0.5, 1, 1)
        )
        btn.bind(on_press=self.open_url)
        layout.add_widget(btn)
        
        return layout

    def open_url(self, instance):
        url = self.url_input.text.strip()
        if url:
            webbrowser.open(url)

if __name__ == "__main__":
    RemoteControlApp().run()
