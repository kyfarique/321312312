# -*- coding: utf-8 -*-

"""
MINES OpenA Bot — всё в одном файле.
Запуск:  python bot.py
"""

import logging
import os
import random
import sqlite3
import threading

import requests
from flask import Flask, request

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

# ============================================================
#  НАСТРОЙКИ
# ============================================================
BOT_TOKEN = "7303209127:AAGHrwgFYbmrh3LFW7mxZl63Yefs_ITYbVQ"
ADMIN_ID  = "6109042131"

WEB_HOST    = "0.0.0.0"
WEB_PORT    = int(os.getenv("PORT", "5000"))
PARTNER_URL = "https://1wymi.pro/casino/list?open=register&sub1={uid}#jwoe"

# ============================================================

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "DataBase.db")
SIGN_DIR   = os.path.join(BASE_DIR, "sign")
INSTR_FILE = os.path.join(BASE_DIR, "instr.png")

WELCOME = (
    "Добро пожаловать в MINES OpenA!\n\n"
    "Mines — гэмблинг-игра в БК 1win по мотивам «Сапёра». "
    "Открывайте безопасные ячейки и не попадайтесь в ловушки.\n\n"
    "Бот основан на нейросети от OpenAI и предугадывает расположение "
    "звёзд с вероятностью 85%."
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "bot.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("mines")


# ---------- DB ----------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user (
                user_id     INTEGER PRIMARY KEY,
                postback_id TEXT
            )
        """)
        conn.commit()


def is_registered(uid: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT postback_id FROM user WHERE user_id = ?", (uid,)
        ).fetchone()
    return bool(row and row[0])


# ---------- Bot ----------
bot = Bot(token=BOT_TOKEN, disable_web_page_preview=True, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


def is_admin(uid: int) -> bool:
    return str(uid) == str(ADMIN_ID)


def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Пройти регистрацию", callback_data="reg"),
        InlineKeyboardButton("Инструкция", callback_data="instr"),
        InlineKeyboardButton("Выдать сигнал", callback_data="sign"),
    )
    return kb


def reg_kb(uid: int):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("Зарегистрироваться", url=PARTNER_URL.format(uid=uid)))
    return kb


def sign_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Выдать сигнал", callback_data="sign"),
        InlineKeyboardButton("Инструкция", callback_data="instr"),
    )
    return kb


def signals_list():
    if not os.path.isdir(SIGN_DIR):
        return []
    return [
        f for f in os.listdir(SIGN_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO user (user_id) VALUES (?)", (uid,))
        conn.commit()
    await bot.send_message(uid, WELCOME, reply_markup=main_menu())


@dp.callback_query_handler(text="instr")
async def cb_instr(call: types.CallbackQuery):
    if os.path.isfile(INSTR_FILE):
        with open(INSTR_FILE, "rb") as f:
            await bot.send_photo(
                call.from_user.id,
                photo=InputFile(f, filename="instr.png"),
            )
    else:
        text = (
            f"1. Регистрация: {PARTNER_URL.format(uid=call.from_user.id)}\n"
            "2. Пополнить баланс\n"
            "3. Игра Mines\n"
            "4. Ловушек: 3\n"
            "5. Ставить по сигналам бота\n"
            "6. При проигрыше — удвоить ставку"
        )
        await bot.send_message(call.from_user.id, text)
    await bot.answer_callback_query(call.id)


@dp.callback_query_handler(text="reg")
async def cb_reg(call: types.CallbackQuery):
    await bot.send_message(
        call.from_user.id,
        "Пройдите регистрацию 👇",
        reply_markup=reg_kb(call.from_user.id),
    )
    await bot.answer_callback_query(call.id)


@dp.callback_query_handler(text="sign")
async def cb_sign(call: types.CallbackQuery):
    uid = call.from_user.id
    if not is_registered(uid):
        await bot.send_message(uid, "Сначала пройдите регистрацию 👇", reply_markup=reg_kb(uid))
        await bot.answer_callback_query(call.id)
        return
    items = signals_list()
    if not items:
        await bot.send_message(uid, "Сигналов пока нет, попробуйте позже.")
        await bot.answer_callback_query(call.id)
        return
    name = random.choice(items)
    with open(os.path.join(SIGN_DIR, name), "rb") as f:
        await bot.send_photo(
            uid, photo=InputFile(f, filename=name), reply_markup=sign_kb()
        )
    await bot.answer_callback_query(call.id)


# ---------- Admin ----------
class AddPhoto(StatesGroup):
    waiting = State()


@dp.message_handler(commands=["admin"])
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await bot.send_message(message.from_user.id, "Вы не админ")
        return
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("Добавить сигнал", callback_data="add_photo"))
    await bot.send_message(message.from_user.id, "Админ панель", reply_markup=kb)


@dp.callback_query_handler(text="add_photo")
async def cb_add(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await bot.answer_callback_query(call.id, "Нет доступа")
        return
    await bot.send_message(call.from_user.id, "Отправьте фото сигнала")
    await AddPhoto.waiting.set()
    await bot.answer_callback_query(call.id)


@dp.message_handler(state=AddPhoto.waiting, content_types=["photo"])
async def on_photo(message: types.Message, state: FSMContext):
    os.makedirs(SIGN_DIR, exist_ok=True)
    existing = set(os.listdir(SIGN_DIR))
    idx = 1
    while f"{idx}.png" in existing:
        idx += 1
    dest = os.path.join(SIGN_DIR, f"{idx}.png")
    await message.photo[-1].download(destination_file=dest)
    await bot.send_message(message.from_user.id, f"Сигнал добавлен ({idx}.png)")
    await state.finish()


@dp.message_handler(state=AddPhoto.waiting)
async def on_wrong(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, "Нужно отправить именно фото.")


# ---------- Flask postback ----------
flask_app = Flask(__name__)


@flask_app.route("/")
def index():
    return "OK"


@flask_app.route("/health")
def health():
    return {"ok": True}


@flask_app.route("/postback")
def postback():
    sub1 = (request.args.get("sub1") or "").strip()
    subid = (request.args.get("subid") or "").strip()
    if not sub1 or not subid:
        return "missing params", 400
    try:
        uid = int(sub1)
    except ValueError:
        return "bad sub1", 400

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO user (user_id, postback_id) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET postback_id = excluded.postback_id",
            (uid, subid),
        )
        conn.commit()

    text = "Вы прошли регистрацию, теперь можете пользоваться сигналами"
    url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        f"?chat_id={uid}&text={requests.utils.quote(text)}"
    )
    try:
        requests.get(url, timeout=10)
    except Exception as e:
        log.error("telegram send failed: %s", e)

    return f"sub1={sub1}; subid={subid}; OK"


def run_flask():
    flask_app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)


# ---------- Entry ----------
if __name__ == "__main__":
    os.makedirs(SIGN_DIR, exist_ok=True)
    init_db()

    threading.Thread(target=run_flask, daemon=True).start()
    log.info("Flask postback на порту %s", WEB_PORT)

    log.info("Bot starting...")
    executor.start_polling(dp, skip_updates=True)