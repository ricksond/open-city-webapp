import os
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore, auth


firebaseConfig = {
  "apiKey": os.getenv("apiKey"),
  "authDomain": os.getenv("authDomain"),
  "databaseURL": os.getenv("databaseURL"),
  "projectId": os.getenv("projectId"),
  "storageBucket": os.getenv("storageBucket"),
  "messagingSenderId": os.getenv("messagingSenderId"),
  "appId": os.getenv("appId"),
  "measurementId":os.getenv("measurementId")
}

firebase = pyrebase.initialize_app(firebaseConfig)
pb_auth = firebase.auth()

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
