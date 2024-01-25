from kivymd.uix.snackbar import Snackbar
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.core.text import Label as CoreLabel
from kivy.metrics import dp, sp
from kivy.clock import Clock


class CustomSnackbar(Snackbar):
    label = ObjectProperty(None)

    def __init__(self, font_size_, color, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        core_label = CoreLabel(text=self.text, font_size=font_size_, markup=True)
        core_label.refresh()
        text_width, _ = core_label.texture.size
        padding = dp(40)
        self.width = text_width + padding
        self.label = Label(text=self.text, size_hint=(1, 1), halign="center", valign="middle", color=color, font_size=font_size_)
        self.clear_widgets()
        self.add_widget(self.label)


def alert_window(camera_type, zone, zona_box, video_play):
    if "momentinio" not in camera_type:
        snackbar_text = f"{camera_type} Zona: {zone}"
    else:
        snackbar_text = f"{camera_type}"
    snackbar1 = CustomSnackbar(
        text=snackbar_text,
        font_size_=dp(15),
        color=(0, 0, 0, 1),
        bg_color=(1, 1, 1, 0.8),
        duration=3,
        pos_hint={"center_x": .5},
        snackbar_y=dp(10)
    )
    snackbar1.open()
    if "momentinio" not in camera_type and video_play is None:
        zona_box.clear_widgets()
        zone = "–" if zone == "nenuskaityta" else zone
        label = Label(
            text=zone,
            font_size=dp(15),
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            color=(0, 0, 0, 1)
        )
        zona_box.add_widget(label)
        zona_box.opacity = 1
    elif video_play is None:
        zona_box.clear_widgets()
        zona_box.opacity = 0
