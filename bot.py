import re
from datetime import datetime

import emoji
import requests
from bs4 import BeautifulSoup as bs, BeautifulSoup
from telebot import TeleBot, types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from constants import BOT_TOKEN, CURRENCIES, DATABASE_URL, DB_NAME
from constants import RESOURCE_URL
from db import Database

bot = TeleBot(BOT_TOKEN)
database = Database(conn=DATABASE_URL, name=DB_NAME)

bot.set_my_commands(
    [
        types.BotCommand("/start", "Main Menu"),
        types.BotCommand("/date", "Select Data"),
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
    msg = "*Bank:\t\tCash Register(Bit/Ask)\t\tCard(Bit/Ask)*"
    rates = database.select_currency_rate(date, currency)
    for obj in rates:
        format_card_value = " / ".join(obj["card"].split("/"))
        msg += f"\n*{obj['key'].split('#')[-1]}*: {obj['cash']}\t\t\t{format_card_value}"
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
            format_card_value = " / ".join(rate["card"].split("/"))
            msg += f"\n*{bank}*: {rate['bank']}\t\t\t{format_card_value}"
        if object_to_insert:
            database.insert_currency_rates(object_to_insert)
    return msg


@bot.message_handler(commands=["help"])
def get_usage_info(msg: types.Message):
    bot.send_message(
        msg.chat.id,
        "Use this bot to check actual information about currency rates using _Ukrainian Minfin_ data.\n"
        "*Possible actions:* check rate of specific currency and review rate for specific date.",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["date"])
def get_calendar(msg: types.Message):
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(
        msg.chat.id,
        f"Select {LSTEP[step].capitalize()}",
        reply_markup=calendar
    )


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def select_date(clb: types.CallbackQuery):
    date, key, step = DetailedTelegramCalendar().process(clb.data)
    if not date and key:
        bot.edit_message_text(
            f"Select {LSTEP[step].capitalize()}",
            clb.message.chat.id,
            clb.message.message_id,
            reply_markup=key
        )
    elif date:
        if date > datetime.today().date():
            bot.edit_message_text(
                f"Selected Date is *{date}*. "
                f"\n_Unfortunately I can't travel in time. Please select a date in the past_",
                clb.message.chat.id,
                clb.message.message_id,
                parse_mode="Markdown"
            )
        else:
            send = bot.edit_message_text(
                f"Selected Date is *{date}*. Now Select a Currency: ",
                clb.message.chat.id,
                clb.message.message_id,
                parse_mode="Markdown"
            )
            bot.register_next_step_handler(send, get_currency_rate, date=date.strftime("%Y-%m-%d"))


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
def get_currency_rate(msg: types.Message, **kwargs):
    msg_text = re.sub(":.*?:", "", emoji.demojize(msg.text)).strip(" ").lower()
    if msg_text in CURRENCIES.keys():
        text = get_rates(msg_text, date=kwargs.get("date"))
        bot.send_message(
            msg.chat.id,
            text,
            parse_mode="Markdown"
        )
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard = generate_keyboard_buttons(keyboard, CURRENCIES, 4)
        bot.send_message(
            msg.chat.id,
            "Select Currency: ",
            reply_markup=keyboard,
        )
