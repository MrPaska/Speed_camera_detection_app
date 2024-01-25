import re
import user

name_pattern = r"^[a-žA-Ž\s]+$"
email_pattern = r"^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$"
password_pattern = r"^(?=.*[a-ž])(?=.*[A-Ž])(?=(?:.*\d){3})[a-žA-Ž\d]{8,}$"


def login_valid(email, password):
    user_id = None
    user_name = None
    email.helper_text = ""
    password.helper_text = ""
    valid = False
    email.error = password.error = False
    email.helper_text, password.helper_text = "", ""
    if email.text != "":
        if password.text != "":
            valid, user_id, user_name = user.login(email.text, password.text)
            print(f"validation.py {valid}")
        else:
            valid = None
            password.error = True
            password.helper_text = "Laukas tuščias!"
    else:
        valid = None
        email.error = True
        email.helper_text = "Laukas tuščias!"

    return valid, user_id, user_name


def signup_valid(name, surname, email, password, user_id):
    name.helper_text, surname.helper_text, email.helper_text, password.helper_text = "", "", "", ""
    name.error = surname.error = email.error = password.error = False
    if name.text == "":
        valid = None
        name.error = True
        name.helper_text = "Laukas tuščias!"
    elif not bool(re.match(name_pattern, name.text)):
        valid = None
        name.error = True
        name.helper_text = "Neatitinka įvestas vardas formato!"
    else:
        valid = True
        name_txt = name.text
    if surname.text == "":
        valid = None
        surname.error = True
        surname.helper_text = "Laukas tuščias!"
    elif not bool(re.match(name_pattern, surname.text)):
        valid = None
        surname.error = True
        surname.helper_text = "Neatitinka įvestas vardas formato!"
    else:
        valid = True
        surname_txt = surname.text
    if email.text == "":
        valid = None
        email.error = True
        email.helper_text = "Laukas tuščias!"
    elif not bool(re.match(email_pattern, email.text)):
        valid = None
        email.error = True
        email.helper_text = "Neatitinka pašto formato!"
    else:
        valid = True
        email_txt = email.text
    if password.text == "":
        valid = None
        password.error = True
        password.helper_text = "Laukas tuščias!"
    elif not bool(re.match(password_pattern, password.text)):
        valid = None
        password.error = True
        password.helper_text = "Silpnas slaptažodis!"
    else:
        valid = True
        password_txt = password.text

    if user_id is None:
        try:
            valid = user.creating_user(name_txt, surname_txt, email_txt, password_txt, email)
        except Exception as e:
            pass
    return valid







