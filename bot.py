# -*- coding: utf-8 -*-
import logging
import os
import random
import sqlite3
import threading
import http.server
import urllib.parse

import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============================================================
#  НАСТРОЙКИ
# ============================================================
BOT_TOKEN = "7303209127:AAGHrwgFYbmrh3LFW7mxZl63Yefs_ITYbVQ"
ADMIN_ID  = "6109042131"

WEB_PORT    = int(os.getenv("PORT", "5000"))
PARTNER_URL = "https://r1wagwk.com/v3/2158/1win-mines?p=4fgb&sub1={uid}"

# ============================================================

BASE_DIR = os.getenv("DATA_DIR") or os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "DataBase.db")

# --- СЛОВАРИ ПЕРЕВОДОВ ---
LANG = {
    'ru': {
        'welcome': "Добро пожаловать в MINES OpenA!\n\nMines — игра в БК 1win. Наш бот на основе ИИ предугадывает расположение звёзд с вероятностью 85%.",
        'btn_reg': "Пройти регистрацию", 'btn_instr': "Инструкция", 'btn_sign': "Выдать сигнал", 'btn_lang': "Сменить язык 🌐",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Язык изменен на Русский 🇷🇺",
        'need_reg': "Сначала пройдите регистрацию 👇",
        'regged': "Вы прошли регистрацию, теперь можете пользоваться сигналами",
        'signal_title': "🎰 <b>Ваш сигнал на игру (3 ловушки):</b>\n\n",
        'signal_hint': "\n👉 <b>Рекомендуемые ячейки:</b> {cells}",
        'instr_text': "1. Регистрация: {url}\n2. Пополнить баланс\n3. Игра Mines (5x5)\n4. Ловушек: 3\n5. Ставить по сигналам бота\n6. При проигрыше — удвоить ставку",
        'admin_panel': "Админ панель", 'not_admin': "Вы не админ"
    },
    'en': {
        'welcome': "Welcome to MINES OpenA!\n\nMines is a 1win casino game. Our AI predicts star locations with 85% accuracy.",
        'btn_reg': "Register", 'btn_instr': "Instruction", 'btn_sign': "Get Signal", 'btn_lang': "Change language 🌐",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Language changed to English 🇬🇧",
        'need_reg': "Please register first 👇",
        'regged': "You have registered, now you can use signals",
        'signal_title': "🎰 <b>Your game signal (3 traps):</b>\n\n",
        'signal_hint': "\n👉 <b>Recommended cells:</b> {cells}",
        'instr_text': "1. Register: {url}\n2. Deposit\n3. Play Mines (5x5)\n4. Traps: 3\n5. Bet on bot signals\n6. Double bet on loss",
        'admin_panel': "Admin panel", 'not_admin': "You are not admin"
    },
    'es': {
        'welcome': "¡Bienvenido a MINES OpenA!\n\nMines es un juego de 1win. Nuestra IA predice las estrellas con un 85% de precisión.",
        'btn_reg': "Registrarse", 'btn_instr': "Instrucción", 'btn_sign': "Obtener señal", 'btn_lang': "Cambiar idioma 🌐",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma cambiado a Español 🇪🇸",
        'need_reg': "Por favor, regístrate primero 👇",
        'regged': "Te has registrado, ahora puedes usar señales",
        'signal_title': "🎰 <b>Tu señal de juego (3 trampas):</b>\n\n",
        'signal_hint': "\n👉 <b>Celdas recomendadas:</b> {cells}",
        'instr_text': "1. Regístrate: {url}\n2. Deposita\n3. Juega Mines (5x5)\n4. Trampas: 3\n5. Apuesta en señales\n6. Dobla la apuesta al perder",
        'admin_panel': "Panel de admin", 'not_admin': "No eres admin"
    },
    'pt': {
        'welcome': "Bem-vindo ao MINES OpenA!\n\nMines é um jogo da 1win. Nossa IA prevê estrelas com 85% de precisão.",
        'btn_reg': "Registre-se", 'btn_instr': "Instrução", 'btn_sign': "Obter sinal", 'btn_lang': "Mudar idioma 🌐",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma alterado para Português 🇵🇹",
        'need_reg': "Por favor, registre-se primeiro 👇",
        'regged': "Você se registrou, agora pode usar sinais",
        'signal_title': "🎰 <b>Seu sinal de jogo (3 armadilhas):</b>\n\n",
        'signal_hint': "\n👉 <b>Células recomendadas:</b> {cells}",
        'instr_text': "1. Registre-se: {url}\n2. Deposite\n3. Jogue Mines (5x5)\n4. Armadilhas: 3\n5. Aposte nos sinais\n6. Dobre a aposta na perda",
        'admin_panel': "Painel de admin", 'not_admin': "Você não é admin"
    },
    'hi': {
        'welcome': "MINES OpenA में आपका स्वागत है!\n\nMines एक 1win गेम है। हमारा AI 85% सटीकता के साथ सितारों की भविष्यवाणी करता है।",
        'btn_reg': "पंजीकरण करें", 'btn_instr': "निर्देश", 'btn_sign': "सिग्नल प्राप्त करें", 'btn_lang': "भाषा बदलें 🌐",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "भाषा हिंदी में बदल गई 🇮🇳",
        'need_reg': "कृपया पहले पंजीकरण करें 👇",
        'regged': "आप पंजीकृत हो गए हैं, अब आप सिग्नल का उपयोग कर सकते हैं",
        'signal_title': "🎰 <b>आपका गेम सिग्नल (3 जाल):</b>\n\n",
        'signal_hint': "\n👉 <b>अनुशंसित सेल:</b> {cells}",
        'instr_text': "1. पंजीकरण करें: {url}\n2. जमा करें\n3. Mines खेलें (5x5)\n4. जाल: 3\n5. सिग्नल पर दांव लगाएं\n6. हारने पर दांव दोगुना करें",
        'admin_panel': "एडमिन पैनल", 'not_admin': "आप एडमिन नहीं हैं"
    },
    'ar': {
        'welcome': "مرحبًا بك في MINES OpenA!\n\nMines هي لعبة 1win. يتوقع الذكاء الاصطناعي لدينا مواقع النجوم بدقة 85٪.",
        'btn_reg': "التسجيل", 'btn_instr': "تعليمات", 'btn_sign': "الحصول على إشارة", 'btn_lang': "تغيير اللغة 🌐",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "تم تغيير اللغة إلى العربية 🇸🇦",
        'need_reg': "يرجى التسجيل أولاً 👇",
        'regged': "لقد قمت بالتسجيل، يمكنك الآن استخدام الإشارات",
        'signal_title': "🎰 <b>إشارتك للعبة (3 فخاخ):</b>\n\n",
        'signal_hint': "\n👉 <b>الخلايا الموصى بها:</b> {cells}",
        'instr_text': "1. التسجيل: {url}\n2. إيداع\n3. العب Mines (5x5)\n4. الفخاخ: 3\n5. راهن على الإشارات\n6. ضاعف الرهان عند الخسارة",
        'admin_panel': "لوحة المسؤول", 'not_admin': "أنت لست مسؤولاً"
    }
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("mines")

# ---------- DB ----------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user (
                user_id     INTEGER PRIMARY KEY,
                postback_id TEXT,
                language    TEXT DEFAULT 'ru'
            )
        """)
        conn.commit()
        try:
            conn.execute("ALTER TABLE user ADD COLUMN language TEXT DEFAULT 'ru'")
        except sqlite3.OperationalError:
            pass

def get_user(uid: int):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT postback_id, language FROM user WHERE user_id = ?", (uid,)).fetchone()
        if row:
            lang = row[1] if row[1] in LANG else 'ru'
            return {"postback_id": row[0], "lang": lang}
    return None

# ---------- Bot ----------
bot = Bot(token=BOT_TOKEN, disable_web_page_preview=True, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

def get_lang_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
        InlineKeyboardButton("🇪🇸 Español", callback_data="set_lang_es"),
        InlineKeyboardButton("🇵🇹 Português", callback_data="set_lang_pt"),
        InlineKeyboardButton("🇮🇳 हिंदी", callback_data="set_lang_hi"),
        InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar")
    )
    return kb

def main_menu(lang):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(LANG[lang]['btn_reg'], callback_data="reg"),
        InlineKeyboardButton(LANG[lang]['btn_instr'], callback_data="instr"),
        InlineKeyboardButton(LANG[lang]['btn_sign'], callback_data="sign"),
        InlineKeyboardButton(LANG[lang]['btn_lang'], callback_data="lang_menu")
    )
    return kb

def reg_kb(uid, lang):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(LANG[lang]['btn_reg'], url=PARTNER_URL.format(uid=uid)))
    return kb

def sign_kb(lang):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(LANG[lang]['btn_sign'], callback_data="sign"),
        InlineKeyboardButton(LANG[lang]['btn_instr'], callback_data="instr"),
    )
    return kb

def generate_mines_grid(lang):
    cells = ['⭐'] * 22 + ['💣'] * 3
    random.shuffle(cells)
    
    grid_text = ""
    for i in range(5):
        row = cells[i*5:(i+1)*5]
        grid_text += " ".join(row) + "\n"
        
    safe_cells = [str(i+1) for i, cell in enumerate(cells) if cell == '⭐']
    random.shuffle(safe_cells)
    recommended = ", ".join(safe_cells[:4])
    
    return LANG[lang]['signal_title'] + grid_text + LANG[lang]['signal_hint'].format(cells=recommended)

# ---------- Handlers ----------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO user (user_id) VALUES (?)", (uid,))
        conn.commit()
    
    # При старте всегда показываем выбор языка
    await bot.send_message(uid, LANG['ru']['choose_lang'], reply_markup=get_lang_kb())

@dp.callback_query_handler(text="lang_menu")
async def cb_lang_menu(call: types.CallbackQuery):
    await bot.edit_message_text(LANG['ru']['choose_lang'], call.from_user.id, call.message.message_id, reply_markup=get_lang_kb())

@dp.callback_query_handler(text_startswith="set_lang_")
async def cb_set_lang(call: types.CallbackQuery):
    new_lang = call.data.split("_")[-1]
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE user SET language = ? WHERE user_id = ?", (new_lang, call.from_user.id))
        conn.commit()
        
    await bot.answer_callback_query(call.id, LANG[new_lang]['lang_set'])
    
    await bot.edit_message_text(
        text=LANG[new_lang]['welcome'],
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=main_menu(new_lang)
    )

@dp.callback_query_handler(text="instr")
async def cb_instr(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    lang = user['lang'] if user else 'ru'
    text = LANG[lang]['instr_text'].format(url=PARTNER_URL.format(uid=call.from_user.id))
    await bot.send_message(call.from_user.id, text)
    await bot.answer_callback_query(call.id)

@dp.callback_query_handler(text="reg")
async def cb_reg(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    lang = user['lang'] if user else 'ru'
    await bot.send_message(call.from_user.id, LANG[lang]['need_reg'], reply_markup=reg_kb(call.from_user.id, lang))
    await bot.answer_callback_query(call.id)

@dp.callback_query_handler(text="sign")
async def cb_sign(call: types.CallbackQuery):
    uid = call.from_user.id
    user = get_user(uid)
    
    if not user or not user['postback_id']:
        lang = user['lang'] if user else 'ru'
        await bot.send_message(uid, LANG[lang]['need_reg'], reply_markup=reg_kb(uid, lang))
        await bot.answer_callback_query(call.id)
        return
    
    signal_text = generate_mines_grid(user['lang'])
    await bot.send_message(uid, signal_text, reply_markup=sign_kb(user['lang']))
    await bot.answer_callback_query(call.id)

@dp.message_handler(commands=["admin"])
async def cmd_admin(message: types.Message):
    user = get_user(message.from_user.id)
    lang = user['lang'] if user else 'ru'
    if str(message.from_user.id) != str(ADMIN_ID):
        await bot.send_message(message.from_user.id, LANG[lang]['not_admin'])
        return
    await bot.send_message(message.from_user.id, LANG[lang]['admin_panel'])

# ============================================================
# ВСТРОЕННЫЙ ВЕБ-СЕРВЕР ДЛЯ ПОСТБЕКОВ
# ============================================================
class PostbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/health' or parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return

        if parsed.path == '/postback':
            qs = urllib.parse.parse_qs(parsed.query)
            sub1 = qs.get('sub1', [''])[0].strip()
            subid = qs.get('subid', [''])[0].strip()

            if not sub1 or not subid:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"missing params")
                return
            try:
                uid = int(sub1)
            except ValueError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"bad sub1")
                return

            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO user (user_id, postback_id) VALUES (?, ?) "
                    "ON CONFLICT(user_id) DO UPDATE SET postback_id = excluded.postback_id",
                    (uid, subid),
                )
                conn.commit()

            user = get_user(uid)
            lang = user['lang'] if user else 'ru'
            
            text = LANG[lang]['regged']
            url = (
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                f"?chat_id={uid}&text={requests.utils.quote(text)}"
            )
            try:
                requests.get(url, timeout=10)
            except Exception as e:
                log.error("telegram send failed: %s", e)

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"sub1={sub1}; subid={subid}; OK".encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass

def run_web():
    server = http.server.HTTPServer(('0.0.0.0', WEB_PORT), PostbackHandler)
    log.info("Web server started on port %s", WEB_PORT)
    server.serve_forever()

# ---------- Entry ----------
if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_web, daemon=True).start()
    log.info("Bot starting...")
    executor.start_polling(dp, skip_updates=True)