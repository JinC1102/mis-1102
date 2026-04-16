import firebase_admin

from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {

"name":"賴期騰",

"mail": "chiteng20060213@gmail.com",

"lab": 676

}

doc_ref = db.collection("PU").document("ChiT")

doc_ref.set(doc)