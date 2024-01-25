from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.clock import Clock
from validation import signup_valid
import firebase_conn
import bcrypt
import re


class Account:
    def __init__(self, app):
        self.app = app
        self.acc_dialog = None
        self.acc_data = None
        self.acc_pass = None
        self.ref = firebase_conn.db.reference("/users")

    def account_management(self):
        if not self.acc_dialog:
            self.acc_dialog = MDDialog(
                title="Paskyros koregavimas",
                type="custom",
                content_cls=ChangeData(),
                buttons=[
                    MDFlatButton(
                        text="Uždaryti",
                        theme_text_color="Custom",
                        text_color=self.app.theme_cls.primary_color,
                        on_release=lambda *args: self.acc_dialog.dismiss()
                    ),
                ],
            )
        self.acc_dialog.open()

    def account_data_dialog(self, user_id):
        name = None
        surname = None
        email = None
        email_check = []
        if user_id is not None:
            user_data = self.ref.get()
            for key, values in user_data.items():
                if user_id == key:
                    name = values["name"]
                    surname = values["surname"]
                    email = values["email"]
                    password = values["password"]
                else:
                    email_check.append(values["email"])
        self.acc_dialog.dismiss()
        self.acc_data = MDDialog(
            title="Paskyros duomenys",
            type="custom",
            content_cls=ChangeAccData(),
            buttons=[
                MDFlatButton(
                    text="Atšaukti",
                    theme_text_color="Custom",
                    text_color=self.app.theme_cls.primary_color,
                    on_release=lambda *args: (self.acc_data.dismiss(), self.acc_dialog.open())
                ),
                MDFlatButton(
                    text="Keisti",
                    theme_text_color="Custom",
                    text_color=self.app.theme_cls.primary_color,
                    on_release=lambda *args: self.change_account_data(user_id, password, email_check)
                ),
            ],
        )
        self.acc_data.open()

        return name, surname, email

    def change_account_data(self, user_id, password, email_check):
        content = self.acc_data.content_cls
        name_f = content.ids.acc_name
        surname_f = content.ids.acc_surname
        email_f = content.ids.acc_email
        password_f = content.ids.acc_password
        alert = content.ids.update_denied
        alert.opacity = 0
        name_f.helper_text, surname_f.helper_text, email_f.helper_text, password_f.helper_text = "", "", "", ""
        name_f.error = surname_f.error = email_f.error = password_f.error = False
        valid = signup_valid(name_f, surname_f, email_f, password_f, user_id)
        if valid:
            if email_f.text not in email_check:
                if self.check_password(password_f.text, password):
                    new_data = {
                        "name": name_f.text,
                        "surname": surname_f.text,
                        "email": email_f.text
                    }
                    try:
                        self.ref.child(user_id).update(new_data)
                        print("Updated")
                        self.app.user_name = name_f.text
                        alert.text = "Duomenys sėkmingai pakeisti"
                        alert.color = (0, 0.8, 0, 1)
                        alert.opacity = 1
                    except Exception as e:
                        print(e)
                        alert.color = (1, 0, 0, 1)
                        alert.text = "Įvyko klaida!"
                        alert.opacity = 1
                else:
                    alert.color = (1, 0, 0, 1)
                    alert.text = "Netinkamas slaptažodis. Duomenys nepakeisti"
                    alert.opacity = 1
            else:
                alert.color = (1, 0, 0, 1)
                alert.text = "Toks el. paštas jau yra registruotas"
                alert.opacity = 1

    def check_password(self, password_text, hashed_pass):
        try:
            match = bcrypt.checkpw(password_text.encode("utf-8"), hashed_pass.encode("utf-8"))
            if match:
                return True
        except Exception as e:
            print(e)
            return False

    def password_dialog(self):
        self.acc_dialog.dismiss()
        self.acc_pass = MDDialog(
            title="Keisti slaptažodį",
            type="custom",
            content_cls=ChangePassword(),
            buttons=[
                MDFlatButton(
                    text="Uždaryti",
                    theme_text_color="Custom",
                    text_color=self.app.theme_cls.primary_color,
                    on_release=lambda *args: (self.acc_pass.dismiss(), self.acc_dialog.open())
                ),
                MDFlatButton(
                    text="Keisti",
                    theme_text_color="Custom",
                    text_color=self.app.theme_cls.primary_color,
                    on_release=lambda *args: self.change_password()
                )
            ],
        )
        self.acc_pass.open()

    def change_password(self):
        password_pattern = r"^(?=.*[a-ž])(?=.*[A-Ž])(?=(?:.*\d){3})[a-žA-Ž\d]{8,}$"
        current_pass = None
        content = self.acc_pass.content_cls
        old_pass = content.ids.old_password
        new_pass = content.ids.new_password
        alert = content.ids.update_denied
        old_pass.helper_text, new_pass.helper_text = "", ""
        old_pass.error = new_pass.error = False
        user_data = self.ref.get()
        alert.opacity = 0
        for key, values in user_data.items():
            if key == self.app.user_id:
                current_pass = values["password"]
        if old_pass.text != "":
            if new_pass.text != "":
                if old_pass.text != new_pass.text:
                    if self.check_password(old_pass.text, current_pass):
                        if not bool(re.match(password_pattern, new_pass.text)):
                            alert.text = "Silpnas slaptažodis!"
                            alert.color = (1, 0, 0, 1)
                            alert.opacity = 1
                        else:
                            try:
                                salt = bcrypt.gensalt()
                                hashed_pass = bcrypt.hashpw(new_pass.text.encode("utf-8"), salt)
                                self.ref.child(self.app.user_id).update({"password": hashed_pass.decode("utf-8")})
                                alert.color = (0, 0.8, 0, 1)
                                alert.text = "Slaptažodis sėkmingai pakeistas"
                                alert.opacity = 1
                                self.acc_pass.dismiss()
                                self.app.screen_manager.current = "start_sec"
                            except Exception as e:
                                print(e)
                                alert.color = (1, 0, 0, 1)
                                alert.text = "Įvyko klaida!"
                                alert.opacity = 1
                    else:
                        alert.color = (1, 0, 0, 1)
                        alert.text = "Netinkamas senasis slaptažodis"
                        alert.opacity = 1
                else:
                    new_pass.error = True
                    new_pass.helper_text = "Slaptažodžiai vienodi"
            else:
                new_pass.error = True
                new_pass.helper_text = "Laukas tuščias!"
        else:
            old_pass.error = True
            old_pass.helper_text = "Laukas tuščias!"


class ChangeData(MDBoxLayout):
    pass


class ChangeAccData(MDBoxLayout):
    pass


class ChangePassword(MDBoxLayout):
    pass
