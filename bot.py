import re
from datetime import datetime

import emoji
import requests
from bs4 import BeautifulSoup as bs, BeautifulSoup
from telebot import TeleBot, types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from constants import BOT_TOKEN, CURRENCIES, DATABASE_URL, DB_NAME, FAVORITES_CURRENCIES, OTHER_CURRENCIES
from constants import RESOURCE_URL
from db import Database

bot = TeleBot(BOT_TOKEN)
database = Database(conn=DATABASE_URL, name=DB_NAME)

bot.set_my_commands(
    [
        types.BotCommand("/start", "Main Menu"),
        types.BotCommand("/bank", "Select Bank"),  # TODO: to be implemented
        types.BotCommand("/date", "Select Data"),  # TODO: to be implemented
        types.BotCommand("/help", "Print Usage"),
    ]
)


def parse_response(page: BeautifulSoup) -> dict:
    rates = {}
    for item in page.find("tbody", {"class": "list"}).findChildren("tr", recursive=False):
        row = item.findChildren("td")[0]
        rates[row.text.strip()] = {
            "bank": row["data-title"],
            "card": row["data-card"]
        }
    return rates


def get_rates(currency: str, date: str = None) -> str:
    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")
    msg = "Bank\tCash Register\tCard"
    rates = database.select_currency_rate(date, currency)
    for obj in rates:
        msg += f"\n{obj['key'].split('#')[-1]}\t{obj['cash']}\t{obj['card']}"
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
            msg += f"\n{bank}\t{rate['bank']}\t{rate['card']}"
        if object_to_insert:
            database.insert_currency_rates(object_to_insert)
    msg = "<pre>{}</pre>".format(msg)
    return msg


@bot.message_handler(commands=["help"])
def get_usage_info(msg: types.Message):
    bot.send_message(
        msg.chat.id,
        "Use this bot to check actual information about currency rates using _Ukrainian Minfin_ data.\n"
        "*Possible actions:* \n{shft}check rate of specific currency, \n{shft}check rate of specific bank,"
        " \n{shft}review rate for specific date.".format(shft="\t" * 4),
        parse_mode="Markdown"
    )


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


@bot.message_handler()
def get_currencies_list(msg: types.Message):
    msg_text = re.sub(":.*?:", "", emoji.demojize(msg.text)).strip(" ").lower()
    if msg_text in CURRENCIES.keys():
        text = get_rates(msg_text)
        bot.send_message(
            msg.chat.id,
            text,
            parse_mode="html"
        )
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if msg_text == "other":
        keyboard.add(types.KeyboardButton(emoji.emojize(":arrow_left:", language="alias") + " " + "Back"))
        keyboard = generate_keyboard_buttons(keyboard, OTHER_CURRENCIES, 5)
    else:
        keyboard = generate_keyboard_buttons(keyboard, FAVORITES_CURRENCIES, 2)
        keyboard.add(types.KeyboardButton("Other" + " " + emoji.emojize(":arrow_right:", language="alias")))
    bot.send_message(
        msg.chat.id,
        "Select Currency: ",
        reply_markup=keyboard,
    )
    return


@bot.message_handler(commands=["date"])
def get_calendar(msg: types.Message):
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(
        msg.chat.id,
        f"Select {LSTEP[step]}",
        reply_markup=calendar
    )


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c):
    result, key, step = DetailedTelegramCalendar().process(c.data)
    if not result and key:
        bot.edit_message_text(
            f"Select {LSTEP[step]}",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=key
        )
    elif result:
        bot.edit_message_text(
            f"You selected {result}",
            c.message.chat.id,
            c.message.message_id
        )
