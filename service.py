from datetime import datetime

import emoji
import requests
from bs4 import BeautifulSoup as bs, BeautifulSoup
from constants import RESOURCE_URL
from telebot import types


def parse_response(page: BeautifulSoup) -> dict:
    rates = {}
    for item in page.find("tbody", {"class": "list"}).findChildren("tr", recursive=False):
        row = item.findChildren("td")[0]
        rates[row.text.strip()] = {
            "bank": row["data-title"],
            "card": row["data-card"]
        }
    return rates

# TODO: add ordering according to user setting


def get_rates(db, user_id: int, currency: str, date: str = None) -> str:
    users_settings = select_settings(db, user_id)
    is_show_card_rate = users_settings.get("show_card_rate", "No") == "Yes"
    selected_banks = users_settings.get("banks", [])
    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")
    msg = f"*Bank:\t\tCash Register(Bit/Ask)\t\t{'Card(Bit/Ask)' if is_show_card_rate else ''}*"
    rates = db.select_currency_rate(date, currency)
    for obj in rates:
        bank_name = obj['key'].split('#')[-1]
        if selected_banks and bank_name in selected_banks:
            format_card_value = " / ".join(obj["card"].split("/"))
            msg += f"\n*{obj['key'].split('#')[-1]}*: {obj['cash']}\t\t\t{format_card_value if is_show_card_rate else ''}"
    if not rates:
        res = requests.get(RESOURCE_URL + currency + "/" + date)
        page = bs(res.text, features="lxml")
        object_to_insert = []
        for bank, rate in parse_response(page).items():
            object_to_insert.append(
                {
                    "key": f"{date}#{currency}#{bank}",
                    "cash": rate["bank"],
                    "card": rate["card"]
                }
            )
            if selected_banks and bank in selected_banks:
                format_card_value = " / ".join(rate["card"].split("/"))
                msg += f"\n*{bank}*: {rate['bank']}\t\t\t{format_card_value if is_show_card_rate else ''}"
        if object_to_insert:
            db.insert_currency_rates(object_to_insert)
    return msg


def generate_keyboard_buttons(
    keyboard: types.ReplyKeyboardMarkup, currencies: dict, row_size: int
) -> types.ReplyKeyboardMarkup:
    buttons = [
        types.KeyboardButton(emoji.emojize(flag, language="alias") + " " + currency.upper())
        for currency, flag in currencies.items()
    ]
    buttons_per_row = [buttons[i:i + row_size] for i in range(0, len(buttons), row_size)]
    for row in buttons_per_row:
        keyboard.row(*row)
    return keyboard


def generate_inline_buttons(options_batch: list[tuple]) -> types.InlineKeyboardMarkup:
    buttons = types.InlineKeyboardMarkup()
    for option in options_batch:
        buttons.add(
            types.InlineKeyboardButton(
                text=option[0],
                callback_data=option[-1]
            )
        )
    return buttons

# use all Database method through service to provide additional layer of abstraction


def register_user(db, id: int):
    db.insert_user(id)


def check_user_exists(db, id: int) -> bool:
    return bool(db.select_user(id))


def update_settings(db, id: int, value: dict):
    db.update_user(id, value)


def select_users_banks(db, id: int) -> list[str]:
    return db.select_users_banks(id)


def add_users_bank(db, id: int, bank: str):
    db.add_users_bank(id, bank)


def remove_users_bank(db, id: int, bank: str):
    db.remove_users_bank(id, bank)


def select_settings(db, id: int) -> dict:
    return db.select_settings(id)
