import re
from datetime import datetime

import emoji
from telebot import TeleBot, types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from constants import (
    BOT_TOKEN,
    CURRENCIES,
    DATABASE_URL,
    DB_NAME,
    AVAILABLE_SETTINGS,
    VIEW_SETTINGS,
    ORDERING_SETTINGS,
    AVAILABLE_BANKS,
)
from db import Database
from service import (
    get_rates, register_user, check_user_exists, update_settings, generate_inline_buttons,
    generate_keyboard_buttons, select_users_banks, add_users_bank, remove_users_bank, select_settings
)


bot = TeleBot(BOT_TOKEN)
database = Database(conn=DATABASE_URL, name=DB_NAME)

bot.set_my_commands(
    [
        types.BotCommand("/start", "Main Menu"),
        types.BotCommand("/date", "Select Data"),
        types.BotCommand("/settings", "Customize Output"),
        types.BotCommand("/mysettings", "View Settings"),
        types.BotCommand("/help", "Print Usage"),
    ]
)


@bot.message_handler(commands=["help"])
def get_usage_info(msg: types.Message):
    bot.send_message(
        msg.chat.id,
        "Use this bot to check actual information about currency rates using _Ukrainian Minfin_ data.\n"
        "*Possible actions:* check rate of specific currency and review rate for specific date.",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["settings"])
def get_available_settings(msg: types.Message):
    user_id = msg.from_user.id
    if not check_user_exists(database, user_id):
        register_user(database, user_id)
    bot.send_message(
        msg.chat.id,
        text="Available Settings:",
        reply_markup=generate_inline_buttons(AVAILABLE_SETTINGS)
    )


@bot.callback_query_handler(func=lambda call: "customize" in call.data)
def customize_output(cl):
    match cl.data:
        case "customize_bank":
            selected_banks = select_users_banks(database, cl.from_user.id)
            bot.send_message(
                cl.message.chat.id,
                "Press to Add Bank",
                reply_markup=generate_inline_buttons([b for b in AVAILABLE_BANKS if b[0] not in selected_banks])

            )
        case "customize_view":
            bot.send_message(
                cl.message.chat.id,
                "Show Card Rate: ",
                reply_markup=generate_inline_buttons(VIEW_SETTINGS)
            )
        case "customize_ordering":
            bot.send_message(
                cl.message.chat.id,
                "Order By: ",
                reply_markup=generate_inline_buttons(ORDERING_SETTINGS)
            )


@bot.callback_query_handler(func=lambda call: call.data in [o[-1] for o in VIEW_SETTINGS])
def save_view_setting(cl):
    update_settings(database, cl.from_user.id, {"show_card_rate": cl.data})
    bot.send_message(
        cl.message.chat.id, f"Option *{cl.data}* was applied.",
        parse_mode="Markdown"
    )


@bot.callback_query_handler(func=lambda call: call.data in [o[-1] for o in ORDERING_SETTINGS])
def save_ordering_settings(cl):
    update_settings(database, cl.from_user.id, {"order_by": cl.data})
    bot.send_message(
        cl.message.chat.id, f"Option *{cl.data}* was applied.",
        parse_mode="Markdown"
    )


@bot.callback_query_handler(func=lambda call: call.data in [o[-1] for o in AVAILABLE_BANKS])
def update_selected_banks(cl):
    user = cl.from_user
    selected_banks = select_users_banks(database, user.id)
    if "remove" in cl.message.text.lower():
        selected_banks.remove(cl.data)
        BANKS = [b for b in AVAILABLE_BANKS if b[-1] in selected_banks]
        remove_users_bank(database, user.id, cl.data)
    else:
        selected_banks.append(cl.data)
        BANKS = [b for b in AVAILABLE_BANKS if b[-1] not in selected_banks]
        add_users_bank(database, user.id, cl.data)
    bot.edit_message_reply_markup(
        cl.message.chat.id,
        message_id=cl.message.id,
        reply_markup=generate_inline_buttons(BANKS)
    )


@bot.message_handler(commands=["mysettings"])
def view_settings(msg: types.Message):
    settings = select_settings(database, msg.from_user.id)
    res_txt = f"""
        Your setting is: 
        \nShow Card Rate: {settings.get('show_card_rate', 'Yes')}
        \nOrdering: {settings.get('order_by', 'Default')}
        \nSelected Banks: {', '.join(set(settings.get('banks', []))) if settings.get('banks') else 'All'}
        """
    button = types.InlineKeyboardMarkup()
    button.add(
        types.InlineKeyboardButton(
            text="Remove Selected Banks",
            callback_data="remove_selected_banks"
        )
    )
    bot.send_message(
        msg.chat.id,
        res_txt,
        reply_markup=button
    )


@bot.callback_query_handler(func=lambda call: call.data == "remove_selected_banks")
def manage_selected_banks(cl):
    selected_banks = select_users_banks(database, cl.from_user.id)
    bot.send_message(
        cl.message.chat.id,
        "Press to Remove Bank",
        reply_markup=generate_inline_buttons([b for b in AVAILABLE_BANKS if b[0] in selected_banks])
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


@bot.message_handler()
def get_currency_rate(msg: types.Message, **kwargs):
    msg_text = re.sub(":.*?:", "", emoji.demojize(msg.text)).strip(" ").lower()
    if msg_text in CURRENCIES.keys():
        text = get_rates(database, msg.from_user.id, msg_text, date=kwargs.get("date"))
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
