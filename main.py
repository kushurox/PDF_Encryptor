import io
import os
import uuid

import cryptography.fernet
import fitz
from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.image import Image as KImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.clipboard import Clipboard

from cryptography.fernet import Fernet  # Safe, better options are AESGCM


class EncFields(RelativeLayout):
    def __init__(self, **kwargs):
        super(EncFields, self).__init__(**kwargs)


class DecPage(Screen):
    def __init__(self, **kwargs):
        super(DecPage, self).__init__(**kwargs)
        self.binds = None
        self.popup = Popup(title="msg", content=Label(text="Invalid Token"), size_hint=(0.4, 0.3))
        self.file_set = False

    def on_pre_enter(self, *args):
        self.binds = Window.fbind("on_drop_file", self.on_file_drop)

    def on_file_drop(self, window_widget, path: bytes, x: int, y: int):
        path = path.decode('utf-8')
        self.path_label.text = path
        if path.endswith(".kenc"):
            self.file_set = True
        else:
            self.path_label.text = "Invalid File type"

    def on_pre_leave(self, *args):
        Window.unbind_uid("on_drop_file", self.binds)
        self.path_label.text = "Drop your encrypted file"
        self.file_set = False

    def back(self):
        self.parent.current = "main page"

    def decrypt(self):
        if self.key_input.text and self.file_set:
            try:
                key = self.key_input.text.encode()
                f = Fernet(key)
                output = os.path.join(os.path.expanduser("~"), "Downloads", str(uuid.uuid4()) + ".pdf")
                with open(output, "wb") as fp:
                    to_decrypt = open(self.path_label.text, "rb")
                    fp.write(f.decrypt(to_decrypt.read()))
                    to_decrypt.close()
                    self.path_label.text = "Decrypted, saved to " + output
                self.key_input.text = ""
            except:
                self.popup.open()
        else:
            self.path_label.text = "Please Enter your Key!"


class EncPage(Screen):
    def __init__(self, **kwargs):
        super(EncPage, self).__init__(**kwargs)
        self.binds = None
        self.path_label = ObjectProperty(None)
        self.thumbnail = KImage()
        self.thumbnail.pos_hint = {"y": 0.1}
        self.thumbnail.size_hint_y = 0.8
        self.popup = Popup(title="Encryption Details", content=EncFields(), auto_dismiss=False)
        self.popup.size_hint = (0.5, 0.4)
        self.file_set = False
        self.key = None

    def on_pre_enter(self, *args):
        self.binds = Window.fbind("on_drop_file", self.on_file_drop)

    def on_file_drop(self, window_widget, path: bytes, x: int, y: int):
        path = path.decode('utf-8')
        self.path_label.text = path
        if path.endswith(".pdf"):
            file = fitz.open(path)
            page = file[0]
            pix = page.get_pixmap()
            data = pix.pil_tobytes(format="png", optimize=False)
            data = io.BytesIO(data)
            img = CoreImage(data, ext="png")
            self.thumbnail.texture = img.texture
            self.add_widget(self.thumbnail)
            self.file_set = True
            del img
            del file
            del pix
            del data
        else:
            self.path_label.text = "Invalid File type"

    def on_pre_leave(self, *args):
        Window.unbind_uid("on_drop_file", self.binds)
        self.remove_widget(self.thumbnail)
        self.path_label.text = "Drop your pdf"
        self.file_set = False

    def back(self):
        self.parent.current = "main page"

    def ask_enc(self):
        if self.file_set:
            self.popup.open()
        else:
            self.path_label.text = "Please Upload a file before you encrypt"

    def set_encryption(self):
        self.popup.dismiss()
        self.popup.content.key.text = "Please Generate a Key"
        output = os.path.join(os.path.expanduser("~"), "Downloads", str(uuid.uuid4()) + ".kenc")
        with open(self.path_label.text, "rb") as fp, open(output, "wb") as fp1:
            f = Fernet(self.key)
            encrypted = f.encrypt(fp.read())
            fp1.write(encrypted)

            self.path_label.text = "Saved to " + output
        del self.key

    def generate_key(self):
        self.key = Fernet.generate_key()
        self.popup.content.key.text = self.key.decode('utf-8') + "\nCopied To clipboard"
        Clipboard.copy(self.key.decode('utf-8'))


class MainPage(Screen):
    def to_enc_page(self):
        self.parent.current = "enc page"

    def to_dec_page(self):
        self.parent.current = "dec page"

    def on_pre_enter(self, *args):
        self.parent.transition.direction = "right"

    def on_pre_leave(self, *args):
        self.parent.transition.direction = "left"


class RootLayout(ScreenManager):
    def __init__(self, **kwargs):
        super(RootLayout, self).__init__(**kwargs)


class MainApp(App):
    def build(self):
        Window.maximize()


if __name__ == '__main__':
    app = MainApp()

    app.run()
