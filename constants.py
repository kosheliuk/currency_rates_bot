from decouple import config

PORT = config("PORT", cast=int, default=5000)
BOT_TOKEN = config("BOT_TOKEN", cast=str)
PUBLIC_URL = config("PUBLIC_URL", cast=str)
RESOURCE_URL = "https://minfin.com.ua/ua/currency/banks/"

FAVORITES_CURRENCIES = {
    "usd": ":us:",
    "eur": ":eu:",
    "gbp": ":uk:",
    "pln": ":poland:",
}

OTHER_CURRENCIES = {
    "chf": ":switzerland:",
    "nok": ":norway:",
    "jpy": ":jp:",
    "dkk": ":denmark:",
    "cny": ":flag_for_China:",
    "cad": ":canada:",
    "aud": ":australia:",
    "huf": ":hungary:",
    "czk": ":czech_republic:",
    "ils": ":israel:",
}

CURRENCIES = FAVORITES_CURRENCIES | OTHER_CURRENCIES
