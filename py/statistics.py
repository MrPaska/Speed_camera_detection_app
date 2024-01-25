import pickle

import cv2
import base64
import firebase_conn
from datetime import datetime
from io import BytesIO
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.list import MDList
from kivy.metrics import dp


class CustomCard(MDCard):
    def __init__(self, texture, camera_type, zone, date, time, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.width = "350dp"
        self.height = "150dp"
        self.pos_hint = {'center_x': 0.5}
        self.md_bg_color = (0, 0, 0, 0)

        self.layout = MDBoxLayout(orientation='horizontal', padding=10)
        self.image = Image()
        self.image.texture = texture
        self.image.keep_ratio = True
        self.image.allow_stretch = True

        self.label = MDLabel(text=f"Tipas - {camera_type}", halign="left")
        self.label1 = MDLabel(text=f"Zona - {zone}", halign="left")
        self.label2 = MDLabel(text=f"Data - {date}", halign="left")
        self.label3 = MDLabel(text=f"Laikas - {time}", halign="left")

        self.layout.add_widget(self.image)

        self.layout1 = MDBoxLayout(orientation='vertical', padding="10dp")
        self.layout1.add_widget(self.label)
        if zone != 0:
            self.layout1.add_widget(self.label1)
        self.layout1.add_widget(self.label2)
        self.layout1.add_widget(self.label3)

        self.layout.add_widget(self.layout1)

        self.add_widget(self.layout)


class CustomMDBoxLayout(MDBoxLayout):
    def __init__(self):
        super().__init__()
        self.size_hint = (0.8, 0.1)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        label = MDLabel(text="Norėdami matyti aptikimų sąrašą – prisijunkite".upper(), halign="center", bold=True,)
        self.add_widget(label)


def get_statistics(user_id, box):
    box_layout = CustomMDBoxLayout()
    box.clear_widgets()
    scroll = ScrollView()
    list = MDList(spacing="24dp", size_hint_x=1)
    if user_id == "guest":
        box.add_widget(box_layout)
    if user_id is not None and user_id != "guest":
        ref = firebase_conn.db.reference("/stats")
        label = MDLabel(
            text="Aptikti matuokliai",
            bold=True,
            font_style="H5",
            adaptive_height=True,
            padding=("24dp", "20dp", "0dp", "30dp")
        )
        box.add_widget(label)
        stats = ref.get()
        try:
            for key, values in stats.items():
                if values["user_id"] == user_id:
                    image = BytesIO(base64.b64decode(values["image"]))  # Method of encoding binary data as ASCII text
                    texture = CoreImage(image, ext='jpg').texture
                    box_ = MDBoxLayout(orientation="vertical", size_hint=(1, None), height=dp(150))
                    card = CustomCard(texture, camera_type=values["class"], zone=values["zone"], date=values['data'], time=values["time"])
                    box_.add_widget(card)
                    list.add_widget(box_)
            scroll.add_widget(list)
            box.add_widget(scroll)
        except Exception as e:
            print(e)


def post_statistics(cls, zone, user_id, image):
    if user_id is not None and user_id != "guest":
        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        result, compressed = cv2.imencode(".jpg", gray_img)  # Encodes image data in a binary .jpg format
        io_buf = BytesIO(compressed) # Allows it to be treated as a file-like object in memory
        base64_ = base64.b64encode(io_buf.getvalue()).decode('utf-8') # encode binary data as ASCII characters, which is useful for transmitting binary data over net
        ref = firebase_conn.db.reference("/stats")
        current_datetime = datetime.now()
        try:
            ref.push(
                {
                    "user_id": user_id,
                    "class": cls,
                    "zone": zone,
                    "data": datetime.now().date().isoformat(),
                    "time": current_datetime.strftime("%H:%M:%S"),
                    "image": base64_
                }
            )
            print("posting")
        except Exception as e:
            print(e)