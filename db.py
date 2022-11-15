from pymongo import MongoClient


class Database:
    def __init__(self, conn: str, name: str):
        self._db_name = name
        self._cluster = MongoClient(conn)
        self._db = self._cluster[self._db_name]
        self._currencies_rate_collection = self._db["currencies_rate"]
        self._users_collection = self._db["users"]

    def select_user(self, telegram_id: int):
        return self._users_collection.find_one({"telegram_id": telegram_id})

    def insert_user(self, telegram_id: int):
        self._users_collection.insert_one({"telegram_id": telegram_id})

    def update_user(self, telegram_id: int, value: dict):
        self._users_collection.find_one_and_update({"telegram_id": telegram_id}, {"$set":  value}, upsert=True)

    def add_users_bank(self, telegram_id: int, name: str):
        self._users_collection.find_one_and_update({"telegram_id": telegram_id}, {"$push": {"banks": name}})

    def remove_users_bank(self, telegram_id: int, name: str):
        self._users_collection.update_one({"telegram_id": telegram_id}, {"$pull": {"banks": {"$in": [name]}}})

    def select_users_banks(self, telegram_id: int) -> list[str]:
        res = self._users_collection.find_one({"telegram_id": telegram_id}, {"banks": 1, "_id": 0})
        if res and isinstance(res, dict):
            return res.get("banks", [])
        return []

    def select_settings(self, telegram_id: int) -> dict:
        return self._users_collection.find_one(
            {"telegram_id": telegram_id}, {"banks": 1, "show_card_rate": 1, "order_by": 1, "_id": 0}
        )

    def select_currency_rate(self, date: str, currency: str):
        res = list(self._currencies_rate_collection.find({"key": {"$regex": f"^{date}#{currency}"}}))
        return res

    def insert_currency_rates(self, rates_list: list[dict[str:str]]):
        self._currencies_rate_collection.insert_many(rates_list)
