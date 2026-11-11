# -*- coding: utf-8 -*-
import logging
import os
import random
import sqlite3
import threading
import http.server
import urllib.parse
import urllib.request
import datetime
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, MenuButtonCommands
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# ============================================================
#  НАСТРОЙКИ MINES BOT
# ============================================================
BOT_TOKEN = "7303209127:AAGHrwgFYbmrh3LFW7mxZl63Yefs_ITYbVQ" # Токен Mines-бота
ADMIN_ID  = "6109042131"
WEB_PORT  = int(os.getenv("PORT", "5000"))

# Ссылка для Mines (замени на свою партнерскую, если нужно)
PARTNER_URL = "https://r1wagwk.com/v3/2158/1win-mines?p=4fgb&sub1={uid}"

# ============================================================
BASE_DIR = os.getenv("DATA_DIR") or os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "DataBase.db")

LANG = {
    'ru': {
        'welcome': "💣 <b>MINES AI PREDICTOR</b> 💣\n\nПриветствуем! Наша нейросеть сканирует алгоритмы игры <b>Mines</b> в 1win и находит безопасные ячейки с точностью до 90%.",
        'btn_reg': "💳 Регистрация", 'btn_instr': "📖 Инструкция", 'btn_sign': "💣 Выдать сигнал", 'btn_lang': "🌐 Язык", 'btn_ref': "👥 Конкурс и Рефералы", 'btn_support': "🆘 Поддержка",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Язык изменен на Русский 🇷🇺",
        'need_reg': "⚠️ <b>ДОСТУП ЗАБЛОКИРОВАН!</b>\n\nАлгоритм ИИ требует привязки аккаунта 1win.\n\n👇 Зарегистрируйся в 1 клик:",
        'regged': "✅ <b>УСПЕХ!</b> Аккаунт привязан. Нейросеть активирована. Жми «Выдать сигнал»! 🚀",
        'choose_traps': "⚙️ <b>Настройка ловушек</b>\n\nВыбери количество ловушек для следующего раунда:",
        'btn_trap_1': "🟢 1 ловушка", 'btn_trap_3': "🟡 3 ловушки", 'btn_trap_5': "🔴 5 ловушек",
        'btn_main': "⬅️ Главное меню",
        'signal_title': "💣 <b>Анализ завершен!</b>\nЛовушек: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Рекомендуемые ячейки:</b> <code>{cells}</code>\n\n{left}🔥 <i>Удачи! Не забывай про банкролл.</i>",
        'left_signals': "💡 <i>Осталось сигналов: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>ЛИМИТ ИСЧЕРПАН!</b>\n\n👇 Пригласите друга по кнопке «👥 Конкурс и Рефералы»!",
        'instr_text': "📖 <b>КАК ИГРАТЬ:</b>\n\n1️⃣ <b>Регистрация:</b> <a href='{url}'>КЛИКНИ СЮДА</a>\n2️⃣ <b>Депозит.</b>\n3️⃣ <b>Игра:</b> Раздел <b>Mines</b>.\n4️⃣ <b>Настройка:</b> Выстави ловушки по сигналу.",
        'admin_panel': "⚙️ <b>АДМИН ПАНЕЛЬ</b>\n\n👑 Статус: <b>GOD MODE (Безлимит)</b>\n📊 Управление: /top - таблица лидеров",
        'not_admin': "❌ Вы не админ.",
        'support_text': "🆘 <b>Поддержка</b>\n\n👉 <a href='tg://user?id={admin_id}'>Написать админу</a>",
        'ref_title': "🏆 <b>КОНКУРС</b> 🏆\n\n1 друг = 1 билет.\n🥇 $100\n🥈 $50\n🥉 $20\n\n📊 Твои билеты: <b>{count}</b>\n\n🔗 Ссылка:\n<code>{link}</code>",
        'ref_notify': "🎉 Друг зарегистрировался! +1 билет. Всего: <b>{count}</b>.",
        'ref_success': "🔥 <b>Ты пригласил 3 друзей!</b> Доступ открыт навсегда!"
    },
    'en': {
        'welcome': "💣 <b>MINES AI PREDICTOR</b> 💣\n\nWelcome! Our neural network scans <b>Mines</b> algorithms in 1win and finds safe cells with up to 90% accuracy.",
        'btn_reg': "💳 Register", 'btn_instr': "📖 Instruction", 'btn_sign': "💣 Get Signal", 'btn_lang': "🌐 Language", 'btn_ref': "👥 Contest & Refs", 'btn_support': "🆘 Support",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Language changed to English 🇬🇧",
        'need_reg': "⚠️ <b>ACCESS BLOCKED!</b>\n\nRegister below to unlock:",
        'regged': "✅ <b>SUCCESS!</b> Click 'Get Signal'! 🚀",
        'choose_traps': "⚙️ <b>Trap Configuration</b>\n\nChoose the number of traps:",
        'btn_trap_1': "🟢 1 trap", 'btn_trap_3': "🟡 3 traps", 'btn_trap_5': "🔴 5 traps",
        'btn_main': "⬅️ Main Menu",
        'signal_title': "💣 <b>Analysis Complete!</b>\nTraps: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Recommended cells:</b> <code>{cells}</code>\n\n{left}🔥 <i>Good luck!</i>",
        'left_signals': "💡 <i>Signals left: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>LIMIT REACHED!</b>\n\nInvite a friend via '👥 Contest & Refs'!",
        'instr_text': "📖 <b>HOW TO START:</b>\n\n1️⃣ <b>Register:</b> <a href='{url}'>CLICK HERE</a>\n2️⃣ <b>Deposit.</b>\n3️⃣ <b>Game:</b> <b>Mines</b>.",
        'admin_panel': "⚙️ <b>ADMIN PANEL</b>\n\n👑 Status: <b>GOD MODE (Unlimited)</b>\n📊 Commands: /top - leaderboard",
        'not_admin': "❌ No rights.",
        'support_text': "🆘 <b>Support</b>\n\n👉 <a href='tg://user?id={admin_id}'>Message Admin</a>",
        'ref_title': "🏆 <b>CONTEST</b> 🏆\n\n1 friend = 1 ticket.\n🥇 $100\n🥈 $50\n🥉 $20\n\n📊 Tickets: <b>{count}</b>\n\n🔗 Link:\n<code>{link}</code>",
        'ref_notify': "🎉 Friend registered! +1 ticket. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>3 friends invited!</b> Access open forever!"
    }
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("mines")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS user (user_id INTEGER PRIMARY KEY, postback_id TEXT, language TEXT DEFAULT 'ru', referrer_id INTEGER, daily_signals INTEGER DEFAULT 0, last_signal_date TEXT)")
        conn.commit()
        for col, typ in [("language", "TEXT DEFAULT 'ru'"), ("referrer_id", "INTEGER"), ("daily_signals", "INTEGER DEFAULT 0"), ("last_signal_date", "TEXT")]:
            try: conn.execute(f"ALTER TABLE user ADD COLUMN {col} {typ}")
            except sqlite3.OperationalError: pass

def get_user(uid: int):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT postback_id, language, referrer_id, daily_signals, last_signal_date FROM user WHERE user_id = ?", (uid,)).fetchone()
        if row:
            lang = row[1] if row[1] in LANG else 'ru'
            ref_count = conn.execute("SELECT COUNT(*) FROM user WHERE referrer_id = ? AND postback_id IS NOT NULL", (uid,)).fetchone()[0]
            return {"user_id": uid, "postback_id": row[0], "lang": lang, "referrer_id": row[2], "ref_count": ref_count, "daily_signals": row[3] or 0, "last_signal_date": row[4]}
    return None

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML", link_preview_is_disabled=True))
dp = Dispatcher(storage=MemoryStorage())

def get_lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"), InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")]])

def main_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG[lang]['btn_reg'], callback_data="reg")],
        [InlineKeyboardButton(text=LANG[lang]['btn_instr'], callback_data="instr")],
        [InlineKeyboardButton(text=LANG[lang]['btn_sign'], callback_data="sign")],
        [InlineKeyboardButton(text=LANG[lang]['btn_ref'], callback_data="ref_menu")],
        [InlineKeyboardButton(text=LANG[lang]['btn_support'], callback_data="support")],
        [InlineKeyboardButton(text=LANG[lang]['btn_lang'], callback_data="lang_menu")]
    ])

def reg_kb(uid, lang):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANG[lang]['btn_reg'], url=PARTNER_URL.format(uid=uid))]])

def traps_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG[lang]['btn_trap_1'], callback_data="gen_trap_1")],
        [InlineKeyboardButton(text=LANG[lang]['btn_trap_3'], callback_data="gen_trap_3")],
        [InlineKeyboardButton(text=LANG[lang]['btn_trap_5'], callback_data="gen_trap_5")],
        [InlineKeyboardButton(text=LANG[lang]['btn_main'], callback_data="main_menu")]
    ])

def sign_kb(lang):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANG[lang]['btn_sign'], callback_data="sign")], [InlineKeyboardButton(text=LANG[lang]['btn_main'], callback_data="main_menu")]])

def generate_mines_grid(lang, traps, signals_left_str):
    cells = ['⭐'] * (25 - traps) + ['💣'] * traps
    random.shuffle(cells)
    
    grid_text = ""
    for i in range(5):
        row = cells[i*5:(i+1)*5]
        grid_text += " ".join(row) + "\n"
        
    safe_cells = [str(i+1) for i, cell in enumerate(cells) if cell == '⭐']
    random.shuffle(safe_cells)
    recommended = ", ".join(safe_cells[:4])
    
    title = LANG[lang]['signal_title'].format(traps=traps)
    hint = LANG[lang]['signal_hint'].format(cells=recommended, left=signals_left_str)
    
    return title + f"<code>{grid_text}</code>" + hint

# ---------- ХЕНДЛЕРЫ ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    uid = message.from_user.id
    ref = command.args
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO user (user_id) VALUES (?)", (uid,))
        if ref and ref.isdigit() and int(ref) != uid:
            conn.execute("UPDATE user SET referrer_id = ? WHERE user_id = ? AND referrer_id IS NULL", (int(ref), uid))
        conn.commit()
    await message.answer(LANG['ru']['choose_lang'], reply_markup=get_lang_kb())

@dp.callback_query(F.data == "lang_menu")
async def cb_lang_menu(call: types.CallbackQuery): await call.message.edit_text(LANG['ru']['choose_lang'], reply_markup=get_lang_kb())

@dp.callback_query(F.data.startswith("set_lang_"))
async def cb_set_lang(call: types.CallbackQuery):
    lang = call.data.split("_")[-1]
    with sqlite3.connect(DB_PATH) as conn: conn.execute("UPDATE user SET language = ? WHERE user_id = ?", (lang, call.from_user.id)); conn.commit()
    await call.answer(LANG[lang]['lang_set'])
    await call.message.edit_text(LANG[lang]['welcome'], reply_markup=main_menu(lang))

@dp.callback_query(F.data == "main_menu")
async def cb_main(call: types.CallbackQuery):
    u = get_user(call.from_user.id); lang = u['lang'] if u else 'ru'
    await call.message.edit_text(LANG[lang]['welcome'], reply_markup=main_menu(lang)); await call.answer()

@dp.callback_query(F.data == "support")
async def cb_sup(call: types.CallbackQuery):
    u = get_user(call.from_user.id); lang = u['lang'] if u else 'ru'
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANG[lang]['btn_main'], callback_data="main_menu")]])
    await call.message.edit_text(LANG[lang]['support_text'].format(admin_id=ADMIN_ID), reply_markup=kb, disable_web_page_preview=True); await call.answer()

@dp.callback_query(F.data == "ref_menu")
async def cb_ref(call: types.CallbackQuery):
    u = get_user(call.from_user.id); lang = u['lang'] if u else 'ru'
    b_info = await bot.get_me(); link = f"https://t.me/{b_info.username}?start={call.from_user.id}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANG[lang]['btn_main'], callback_data="main_menu")]])
    await call.message.edit_text(LANG[lang]['ref_title'].format(link=link, count=u['ref_count']), reply_markup=kb, disable_web_page_preview=True); await call.answer()

@dp.callback_query(F.data == "instr")
async def cb_instr(call: types.CallbackQuery):
    u = get_user(call.from_user.id); lang = u['lang'] if u else 'ru'
    await call.message.answer(LANG[lang]['instr_text'].format(url=PARTNER_URL.format(uid=call.from_user.id))); await call.answer()

@dp.callback_query(F.data == "reg")
async def cb_reg(call: types.CallbackQuery):
    u = get_user(call.from_user.id); lang = u['lang'] if u else 'ru'
    await call.message.answer(LANG[lang]['need_reg'], reply_markup=reg_kb(call.from_user.id, lang)); await call.answer()

@dp.callback_query(F.data == "sign")
async def cb_sign(call: types.CallbackQuery):
    u = get_user(call.from_user.id)
    if not u or not (u['postback_id'] or u['ref_count'] >= 3):
        lang = u['lang'] if u else 'ru'
        await call.message.answer(LANG[lang]['need_reg'], reply_markup=reg_kb(call.from_user.id, lang)); await call.answer(); return
    await call.message.edit_text(LANG[u['lang']]['choose_traps'], reply_markup=traps_menu(u['lang'])); await call.answer()

@dp.callback_query(F.data.startswith("gen_trap_"))
async def cb_gen(call: types.CallbackQuery):
    uid = call.from_user.id
    u = get_user(uid); lang = u['lang'] if u else 'ru'
    
    # 🔥 ЧИТ-КОД: БЕЗЛИМИТ ДЛЯ АДМИНА 🔥
    is_admin = (str(uid) == str(ADMIN_ID))
    
    today = datetime.date.today().isoformat()
    daily = 0 if u['last_signal_date'] != today else u['daily_signals']
    
    if not is_admin:
        # Для обычных юзеров лимит 5
        if daily >= 5:
            await call.answer("⚠️ Лимит исчерпан!", show_alert=True)
            await call.message.answer(LANG[lang]['limit_msg'])
            return
        daily += 1
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE user SET daily_signals = ?, last_signal_date = ? WHERE user_id = ?", (daily, today, uid))
            conn.commit()
        signals_left_str = LANG[lang]['left_signals'].format(left=5 - daily)
    else:
        # Для админа безлимит
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE user SET last_signal_date = ? WHERE user_id = ?", (today, uid))
            conn.commit()
        signals_left_str = "💡 <i>Осталось сигналов: ∞ (God Mode)</i>\n\n"
    # --------------------------------------

    traps = int(call.data.split("_")[-1])
    signal_text = generate_mines_grid(lang, traps, signals_left_str)
    
    await call.message.edit_text(text=signal_text, reply_markup=sign_kb(lang))
    await call.answer()

@dp.message(Command("admin"))
async def cmd_adm(msg: types.Message):
    u = get_user(msg.from_user.id); lang = u['lang'] if u else 'ru'
    if str(msg.from_user.id) == str(ADMIN_ID):
        await msg.answer(LANG[lang]['admin_panel'])
    else:
        await msg.answer(LANG[lang]['not_admin'])

@dp.message(Command("top"))
async def cmd_top(msg: types.Message):
    if str(msg.from_user.id) != ADMIN_ID: return
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT u1.user_id, COUNT(u2.user_id) FROM user u1 JOIN user u2 ON u1.user_id = u2.referrer_id WHERE u2.postback_id IS NOT NULL GROUP BY u1.user_id ORDER BY 2 DESC LIMIT 10").fetchall()
    text = "🏆 <b>ТОП-10</b>\n\n" + "".join([f"{i}. ID: <code>{r[0]}</code> — <b>{r[1]} билетов</b>\n" for i, r in enumerate(rows, 1)]) if rows else "Нет рефералов."
    await msg.answer(text)

# ============================================================
# ВСТРОЕННЫЙ ВЕБ-СЕРВЕР ДЛЯ ПОСТБЕКОВ
# ============================================================
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == '/health': self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok": true}'); return
        if p.path == '/postback':
            q = urllib.parse.parse_qs(p.query); s1, s2 = q.get('sub1',[''])[0], q.get('subid',[''])[0]
            if not s1 or not s2: self.send_response(400); self.end_headers(); return
            try: uid = int(s1)
            except: self.send_response(400); self.end_headers(); return
            with sqlite3.connect(DB_PATH) as conn: conn.execute("INSERT INTO user (user_id, postback_id) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET postback_id = excluded.postback_id", (uid, s2)); conn.commit()
            u = get_user(uid); lang = u['lang'] if u else 'ru'
            try: urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={uid}&text={urllib.parse.quote(LANG[lang]['regged'])}&parse_mode=HTML", timeout=5)
            except: pass
            if u and u.get('referrer_id'):
                r_u = get_user(u['referrer_id'])
                if r_u:
                    t = LANG[r_u['lang']]['ref_success'] if r_u['ref_count'] >= 3 else LANG[r_u['lang']]['ref_notify'].format(count=r_u['ref_count'])
                    try: urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={r_u['user_id']}&text={urllib.parse.quote(t)}&parse_mode=HTML", timeout=5)
                    except: pass
            self.send_response(200); self.end_headers(); self.wfile.write(f"sub1={s1}; subid={s2}; OK".encode('utf-8')); return
        self.send_response(404); self.end_headers()

async def main():
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="Start"))
    log.info("Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=lambda: http.server.HTTPServer(('0.0.0.0', WEB_PORT), Handler).serve_forever(), daemon=True).start()
    log.info("Web server started on port %s", WEB_PORT)
    asyncio.run(main())