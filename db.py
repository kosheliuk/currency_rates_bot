from pymongo import MongoClient


class Database:
    def __init__(self, conn: str, name: str):
        self._db_name = name
        self._cluster = MongoClient(conn)
        self._db = self._cluster[self._db_name]
        self._currencies_rate_collection = self._db["currencies_rate"]

    def select_currency_rate(self, date: str, currency: str):
        res = list(self._currencies_rate_collection.find({"key": {"$regex": f"^{date}#{currency}"}}))
        return res

    def insert_currency_rates(self, rates_list: list[dict[str:str]]):
        self._currencies_rate_collection.insert_many(rates_list)
