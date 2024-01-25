import firebase_conn
import bcrypt


def creating_user(name, surname, email, password, email_field):
    valid = None
    ref = firebase_conn.db.reference("/users")
    users = ref.get()
    email_list = []
    try:
        salt = bcrypt.gensalt()  # A salt is a random sequence added to the password before hashing to ensure that the same password will not always hash to the same value.
        hashed_pass = bcrypt.hashpw(password.encode('utf-8'), salt)
    except Exception as e:
        print(f"Bcrypt_Error: {e}")

    if users is not None:
        for key, value in users.items():
            email_list.append(value["email"])

    if email not in email_list:
        try:
            new_user = ref.push(
                {
                    "name": name,
                    "surname": surname,
                    "email": email,
                    "password": hashed_pass.decode("utf-8")
                }
            )
            valid = True
        except Exception as e:
            print(e)
    else:
        email_field.error = True
        email_field.helper_text = "Vartotojas su tokiu el. paštu jau egzistuoja!"
        print("No user added")
    print("User added")
    return valid


def login(email, password):
    valid = False
    ref = firebase_conn.db.reference("/users")
    users = ref.get()
    user_id = None
    user_name = None
    if users is not None:
        for key, value in users.items():
            if value["email"] == email:
                hashed_pass = value["password"]
                user_name = value["name"]
                user_id = key
        try:
            if user_name is not None:
                match = bcrypt.checkpw(password.encode("utf-8"), hashed_pass.encode("utf-8")) #  It internally rehashes the input password using the salt extracted from the hash
                if match:
                    valid = True
        except Exception as e:
            print(e)
    return valid, user_id, user_name





