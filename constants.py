from decouple import config

PORT = config("PORT", cast=int, default=5000)
BOT_TOKEN = config("BOT_TOKEN", cast=str)
PUBLIC_URL = config("PUBLIC_URL", cast=str)
RESOURCE_URL = "https://minfin.com.ua/ua/currency/banks/"

CURRENCIES = [
    "usd", "eur", "gbp", "pln", "chf", "sek",
    "pln", "nok", "jpy", "dkk", "cny", "cad",
    "aud", "byn", "huf", "czk", "ils",
]
