import responses as r
from telebot import types
from bot_settings import MASS_PROBLEMS
from responses import BRANDS


def cancel_button():
    return types.KeyboardButton(r.CANCEL_MAKE_TASK)


def start_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    yes_btn = types.KeyboardButton(r.YES)
    no_btn = types.KeyboardButton(r.REBOOT_WONT_HELP)
    markup.add(yes_btn)
    markup.add(no_btn)
    return markup


def start():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton(r.INSTRUCTIONS), types.KeyboardButton(r.MAKE_TASK))
    return markup


def brands_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [types.KeyboardButton(position) for position in BRANDS]
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    markup.row(cancel_button())
    return markup


def skip_and_cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.row(types.KeyboardButton(r.SKIP_BUTTON))
    markup.row(cancel_button())
    return markup


def cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(cancel_button())
    return markup


def screenshot_ask_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(types.KeyboardButton(r.SCREENSHOT_ATTACH_YES),
               types.KeyboardButton(r.SCREENSHOT_ATTACH_NO))
    markup.row(cancel_button())
    return markup


def screenshot_wait_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    cancel_screenshot_btn = types.KeyboardButton(r.SCREENSHOT_ATTACH_CANCEL)
    markup.row(cancel_screenshot_btn)
    markup.row(cancel_button())
    return markup


def remove_keyboard():
    return types.ReplyKeyboardRemove()


def hide_keyboard():
    from json import dumps
    return dumps({"hide_keyboard": True})


def review_keyboard(task):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='Отлично', callback_data=f"Отлично,{task.id}")
    btn2 = types.InlineKeyboardButton(text='Хорошо', callback_data=f"Хорошо,{task.id}")
    btn3 = types.InlineKeyboardButton(text='Удовлетворительно', callback_data=f"Удовлетворительно,{task.id}")
    btn4 = types.InlineKeyboardButton(text='Плохо', callback_data=f"Плохо,{task.id}")
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    return markup


def mass_problems():
    markup = types.ReplyKeyboardMarkup(row_width=1)
    markup.add(*[types.KeyboardButton(x) for x in MASS_PROBLEMS])
    markup.row(cancel_button())
    return markup


def executor_choose():
    markup = types.ReplyKeyboardMarkup()
    markup.row(types.KeyboardButton(r.ANY_EXECUTOR))
    markup.row(cancel_button())
    return markup


def block_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton(text=r.ENTER_IS_BLOCK_YES),
        types.KeyboardButton(text=r.ENTER_IS_BLOCK_NO)
    )
    markup.row(cancel_button())
    return markup
