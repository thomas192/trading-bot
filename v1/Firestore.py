import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


class Firestore:

    def __init__(self):
        cred = credentials.Certificate("./trading-bot-credentials.json")
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def create_collection(self, pair, date):
        data = {
            "pair": str(pair),
            "date": str(date),
        }
        self.db.collection(pair.replace("/", "")).document("info").set(data)

    def save_trade(self, trade_id, pair, row):
        data = {
            "date": row["date"],
            "side": row["side"],
            "price": row["price"],
            "trade_change": row["trade_change"],
            "capital": row["capital"],
        }
        self.db.collection(pair.replace("/", "")).document(str(trade_id)).set(data)

    def save_error(self, error_id, date, error, str_of_traceback, state_after_error):
        data = {
            "date": str(date),
            "error": str(error),
            "traceback": str(str_of_traceback),
            "state_after_error": str(state_after_error),
        }
        self.db.collection("error").document(str(error_id)).set(data)
