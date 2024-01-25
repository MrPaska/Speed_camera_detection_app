import firebase_admin
import os
from firebase_admin import db, credentials

try:
    cred = credentials.Certificate("../credentials/credentials.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://recognitionapp-93eb8-default-rtdb.europe-west1.firebasedatabase.app"})
except Exception as e:
    print(e)

