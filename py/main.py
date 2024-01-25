import os
from kivymd.app import MDApp
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
import validation
from kivy.clock import Clock
import cv2
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
import requests
from bounding_boxes import recognition
from socket_client import frames, ping_server
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget, OneLineListItem
from kivymd.uix.filemanager import MDFileManager
import shutil
from statistics import get_statistics
from kivy.uix.screenmanager import SlideTransition
from account import Account
import threading
from snackbar import alert_window
import play_voice

# Window.size = (360, 740)


class RecognitionApp(MDApp):
    path = os.path.expanduser("~") or os.path.expanduser("/")
    image_texture = ObjectProperty(None)  # attribute can holds any kind of object, and if the object changes, Kivy will automatically handle events related to this change
    show_stat_tab = BooleanProperty(False)
    logout_btn_text = StringProperty()
    screen_manager = ScreenManager()
    name = StringProperty()
    surname = StringProperty()
    email = StringProperty()
    user_name = StringProperty()
    bounding_box = None
    zona_box = None
    thread = None
    dialog = None
    account = None
    video_folder = "../video"
    video_play = None
    user_id = None
    capture = None
    server = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filemanager = MDFileManager(
            select_path=self.select_path,
            exit_manager=self.close_filemanager
        )

    def build(self):
        self.screen_manager.add_widget(Builder.load_file(
            "../kv/start_f.kv"))  # Used to manage multiple Screen widgets in an application. It helps in switching between different screens in the app.
        self.screen_manager.add_widget(Builder.load_file("../kv/start_s.kv"))
        self.screen_manager.add_widget(Builder.load_file("../kv/login.kv"))
        self.screen_manager.add_widget(Builder.load_file("../kv/reg.kv"))
        self.screen_manager.add_widget(Builder.load_file("../kv/main.kv"))
        self.screen_manager.add_widget(Builder.load_file("../kv/video.kv"))
        self.screen_manager.add_widget(Builder.load_file("../kv/account.kv"))
        self.theme_cls.material_style = "M3"
        return self.screen_manager

    def on_start(self):
        self.account = Account(app=self)
        Clock.schedule_once(self.start_window, 10)

    def start_window(self, *args):
        self.screen_manager.current = "start_sec"
        self.check_internet_conn()

    def login(self):
        if self.check_internet_conn():
            current_screen = self.root.current_screen
            login_denied = current_screen.ids.login_denied
            email = current_screen.ids.email
            password = current_screen.ids.password
            valid, user_id, user_name = validation.login_valid(email, password)
            if valid:
                email.text, password.text = "", ""
                self.user_id = user_id
                self.user_name = user_name
                self.logout_btn_text = "Atsijungti"
                self.screen_manager.current = "main"
            elif valid is None:
                pass
            else:
                login_denied.opacity = 1
                print(f"main.py not valid {valid}")

    def signup(self):
        if self.check_internet_conn():
            current_screen = self.root.current_screen
            name = current_screen.ids.name
            surname = current_screen.ids.surname
            email = current_screen.ids.email
            password = current_screen.ids.password
            valid = validation.signup_valid(name, surname, email, password, self.user_id)
            if valid:
                name.text, surname.text, email.text, password.text = "", "", "", ""
                self.screen_manager.current = "login"

    def frames_callback(self, result):

        def alert_on_main_thread():
            if result is not None:
                if result[0] == "vidutinis":
                    play_voice.play_voice(1)
                    alert_window("Aptiktas vidutinio greičio matuoklis!", result[1], self.zona_box, self.video_play)
                elif result == "momentinis":
                    play_voice.play_voice(0)
                    alert_window("Aptiktas momentinio greičio matuoklis!", 0, self.zona_box, self.video_play)
                else:
                    pass

        Clock.schedule_once(lambda dt: alert_on_main_thread(), 0)

    def thread_function(self, callback, i, frame, user_id, bounding_box):
        result = frames(i, frame, user_id, bounding_box)
        callback(result)

    def catching_frames(self, server):
        try:
            ok, frame = self.capture.read()
            if ok:
                if self.video_play is None:
                    resized_frame = cv2.resize(frame, (640, 640))
                else:
                    resized_frame = frame
                if server is True:
                    self.thread = threading.Thread(target=self.thread_function, args=(
                        self.frames_callback, server, resized_frame, self.user_id, self.bounding_box))
                    self.thread.start()
                else:
                    recognition(resized_frame, self.user_id, self.bounding_box, self.zona_box, self.video_play)
                self.root.current_screen.ids.image.opacity = 1
                buffer = cv2.flip(resized_frame, 0).tobytes()  # Flips the resized_frame vertically, and then to bytes, graphical interfaces typically require image data in a byte format to create textures
                texture = Texture.create(size=(resized_frame.shape[1], resized_frame.shape[0]), colorfmt="bgr")  # To match the size of the resized_frame (width, height),  color format of the texture. bgr
                texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")  # Transfers the byte data to this texture, ubyte common format for image data
                self.root.current_screen.ids.image.texture = texture
        except Exception as e:
            print(e)

    def camera_button(self, button):
        self.zona_box = self.root.current_screen.ids.zona_box
        self.root.current_screen.ids.cam_spinner.opacity = 1
        self.root.current_screen.ids.cam_label.opacity = 1
        if button == "server":
            self.root.current_screen.ids.cam_label.text = "Susisiekiama su serveriu..."
            Clock.schedule_once(self.check_server_conn, 1)
        else:
            self.root.current_screen.ids.cam_label.text = "Paleidžiamas modulis..."
            Clock.schedule_once(lambda dt: self.turn_on_camera(self.server), 1)

    def turn_on_camera(self, server):
        self.check_params()
        if self.root.current_screen.ids.image.opacity == 0:
            self.capture = cv2.VideoCapture(0)
            self.thread_start = True
            self.root.current_screen.ids.cam_spinner.opacity = 0
            self.root.current_screen.ids.cam_label.opacity = 0
            self.camera_play = Clock.schedule_interval(lambda dt: self.catching_frames(server), 1.0 / 30.0)

    def show_alert_dialog(self, title, text):
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="GERAI",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_release=self.close_dialog
                )
            ]
        )
        self.dialog.open()

    def check_internet_conn(self, *args):
        response = False
        url = "http://www.google.com"
        timeout = 1
        try:
            response = requests.get(url, timeout=timeout)  # Sends a GET request to the URL
            response.raise_for_status()  # Checks if the response from the server was successful.
        except Exception as e:
            title = "Nėra interneto ryšio :("
            text = "Patikrinkite, ar tikrai esate prisijungę prie interneto"
            self.show_alert_dialog(title, text)
        return response

    def check_server_conn(self, *args):
        if ping_server():
            self.server = True
            self.turn_on_camera(self.server)
            print(f"serveris:{self.server}")
        else:
            print("Can't conn to server!")
            title = "Nėra ryšio su serveriu :("
            text = "Neveiks ženklų aptikimo funkcija"
            self.show_alert_dialog(title, text)
            self.server = False
            self.root.current_screen.ids.cam_spinner.opacity = 0
            self.root.current_screen.ids.cam_label.opacity = 0

    def close_dialog(self, *args):
        self.dialog.dismiss()
        Clock.schedule_once(self.check_internet_conn, 1)
        # Clock.schedule_once(self.check_internet_conn, 1)

    def update_video_list(self):
        md_list = self.root.current_screen.ids.md_list
        md_list.clear_widgets()
        video_files = [f for f in os.listdir(self.video_folder) if f.endswith((".mp4", ".MOV", ".avi", ".mkv"))]

        if video_files:
            for video_file in video_files:
                item = OneLineAvatarIconListItem(
                    IconLeftWidget(icon="file-video-outline"),
                    IconRightWidget(icon="delete", on_release=lambda x, file=video_file: self.delete_video(file)),
                    text=video_file, on_release=lambda x, file=video_file: self.play_video(file)
                )
                md_list.add_widget(item)
        else:
            item = OneLineListItem(text="Sąrašas tuščias")
            md_list.add_widget(item)

    def delete_video(self, file):
        os.remove(os.path.join(self.video_folder, file))
        self.update_video_list()

    def open_filemanager(self):
        self.filemanager.show(self.path)

    def select_path(self, path):
        title = "Netinkamas formatas :("
        text = "Pasirinkite vaizdo įrašą"
        if path.endswith((".mp4", ".MOV", ".avi", ".mkv")):
            self.close_filemanager(path)
        else:
            self.show_alert_dialog(title, text)

    def close_filemanager(self, path, *args):
        self.filemanager.close()
        self.add_video(path)

    def add_video(self, path):
        try:
            shutil.copy(path, self.video_folder)
            self.update_video_list()
        except:
            pass

    def play_video(self, file):
        self.check_params()
        self.screen_manager.current = "video"
        self.screen_manager.transition.direction = "left"
        self.capture = cv2.VideoCapture(os.path.join(self.video_folder, file))
        self.video_play = Clock.schedule_interval(lambda dt: self.catching_frames(self.server), 1.0 / 30.0)

    def leave_video(self):
        self.capture = None
        try:
            self.video_play.cancel()
            self.video_play = None
        except:
            pass

    def camera_off(self):
        self.root.current_screen.ids.image.opacity = 0
        try:
            self.zona_box.clear_widgets()
            self.zona_box.opacity = 0
        except:
            pass
        self.server = False
        try:
            self.capture.release()
            self.camera_play.cancel()
        except Exception as e:
            pass

    def statistics(self):
        box = self.root.current_screen.ids.stats_box
        get_statistics(self.user_id, box)

    def check_params(self):
        self.bounding_box = self.root.current_screen.ids.bounding_box.active

    def logout(self):
        self.screen_manager.transition = SlideTransition(direction="right")
        self.screen_manager.current = "start_sec"
        self.user_id = None

    def check_session(self):
        if self.user_id is None:
            self.screen_manager.current = "start_sec"
        self.show_stat_tab = self.user_id != "guest"

    def guest(self):
        self.user_id = "guest"
        self.logout_btn_text = "Išeiti"
        self.screen_manager.transition = SlideTransition(direction="left")
        self.screen_manager.current = "main"

    def account_management(self):
        self.account.account_management()

    def change_account_data(self):
        self.name, self.surname, self.email = self.account.account_data_dialog(self.user_id)

    def change_password(self):
        self.account.password_dialog()


if __name__ == "__main__":
    RecognitionApp().run()
