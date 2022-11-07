from telebot import TeleBot, types

from constants import BOT_TOKEN, CURRENCIES
from parser import get_minfin_data
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

bot = TeleBot(BOT_TOKEN)

bot.set_my_commands([
    types.BotCommand("/start", "Main Menu"),
    types.BotCommand("/bank", "Select Bank"),  # TODO: to be implemented
    types.BotCommand("/date", "Select Data"),  # TODO: to be implemented
    types.BotCommand("/help", "Print Usage"),
])

# TODO: pretty output
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
    msg_text = msg.text.lower()
    if msg_text in CURRENCIES:
        text = get_minfin_data(msg.text.lower())
        bot.send_message(
            msg.chat.id,
            text
        )
        return
    match msg_text:
        case "other":
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(types.KeyboardButton("Back"))
            [keyboard.add(types.KeyboardButton(cur.upper())) for cur in CURRENCIES[4:]]
            bot.send_message(
                msg.chat.id,
                "Select Currency: ",
                reply_markup=keyboard,
            )
        case _:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            [keyboard.add(types.KeyboardButton(cur.upper())) for cur in CURRENCIES[:4]]
            keyboard.add(types.KeyboardButton("Other"))
            bot.send_message(
                msg.chat.id,
                "Select Currency: ",
                reply_markup=keyboard,
            )
    return
