from telebot import TeleBot, types
import emoji
import re
from constants import BOT_TOKEN, CURRENCIES, FAVORITES_CURRENCIES, OTHER_CURRENCIES
from parser import get_minfin_data
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

bot = TeleBot(BOT_TOKEN)

bot.set_my_commands([
    types.BotCommand("/start", "Main Menu"),
    types.BotCommand("/bank", "Select Bank"),  # TODO: to be implemented
    types.BotCommand("/date", "Select Data"),  # TODO: to be implemented
    types.BotCommand("/help", "Print Usage"),
])

# TODO: connect db
# TODO: translate to ukrainian and english
# TODO: customize bot for users
# TODO: implement feature with bank
# TODO: implement feature with date
# TODO: try to union filters


@bot.message_handler(commands=["help"])
def get_usage_info(msg: types.Message):
    bot.send_message(
        msg.chat.id,
        "Use this bot to check actual information about currency rates using _Ukrainian Minfin_ data.\n"
        "*Possible actions:* \n{shft}check rate of specific currency, \n{shft}check rate of specific bank,"
        " \n{shft}review rate for specific date.".format(shft="\t"*4),
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
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected {result}",
                              c.message.chat.id,
                              c.message.message_id)


@bot.message_handler()
def get_currencies_list(msg: types.Message):
    msg_text = re.sub(":.*?:", "", emoji.demojize(msg.text)).strip(" ").lower()
    if msg_text in CURRENCIES.keys():
        text = get_minfin_data(msg_text)
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
