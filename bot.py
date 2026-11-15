# -*- coding: utf-8 -*-
import logging
import os
import random
import sqlite3
import threading
import http.server
import urllib.parse
import urllib.request
import urllib.error
import datetime
import asyncio
import json

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton, MenuButtonCommands
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# ============================================================
#  НАСТРОЙКИ MINES BOT
# ============================================================
# ВАЖНО: Токен лучше задавать в переменных окружения Bothost (BOT_TOKEN).
# Если токен не задан в окружении, используется тот, что ниже.
BOT_TOKEN = os.getenv("BOT_TOKEN", "7303209127:AAGHrwgFYbmrh3LFW7mxZl63Yefs_ITYbVQ") 
ADMIN_ID  = os.getenv("ADMIN_ID", "6109042131")
WEB_PORT  = int(os.getenv("PORT", "5000"))

PARTNER_URL = "https://r1wagwk.com/v3/2158/1win-mines?p=4fgb&sub1={uid}"

# ============================================================
BASE_DIR = os.getenv("DATA_DIR") or os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "DataBase.db")
CONFIG_PATH = os.path.join(BASE_DIR, "notify_config.txt")

LANG = {
    'ru': {
        'welcome': "💣 <b>MINES AI PREDICTOR</b> 💣\n\nПриветствуем! Наша нейросеть сканирует алгоритмы игры <b>Mines</b> в 1win и находит безопасные ячейки с точностью до 90%.\n\n👇 Используй кнопки внизу экрана:",
        'btn_reg': "💳 Регистрация", 'btn_instr': "📖 Инструкция", 'btn_sign': "💣 Выдать сигнал", 'btn_lang': "🌐 Язык", 'btn_ref': "👥 Конкурс", 'btn_support': "🆘 Поддержка",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Язык изменен на Русский 🇷🇺",
        'need_reg': "⚠️ <b>ДОСТУП ЗАБЛОКИРОВАН!</b>\n\nАлгоритм ИИ требует привязки аккаунта 1win.\n\n👇 Зарегистрируйся в 1 клик:",
        'regged': "✅ <b>УСПЕХ!</b> Аккаунт привязан. Нейросеть активирована. Жми «Выдать сигнал»! 🚀",
        'choose_traps': "⚙️ <b>Настройка ловушек</b>\n\nВыбери количество ловушек:",
        'btn_trap_1': "🟢 1 ловушка", 'btn_trap_3': "🟡 3 ловушки", 'btn_trap_5': "🔴 5 ловушек",
        'signal_title': "💣 <b>Анализ завершен!</b>\nЛовушек: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Рекомендуемые ячейки:</b> <code>{cells}</code>\n\n{left}🔥 <i>Удачи!</i>",
        'left_signals': "💡 <i>Осталось сигналов: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>ЛИМИТ ИСЧЕРПАН!</b>\n\n👇 Пригласите друга по кнопке «👥 Конкурс»!",
        'instr_text': "📖 <b>КАК ИГРАТЬ:</b>\n\n1️⃣ <b>Регистрация:</b> <a href='{url}'>КЛИКНИ СЮДА</a>\n2️⃣ <b>Депозит.</b>\n3️⃣ <b>Игра:</b> Раздел <b>Mines</b>.\n4️⃣ <b>Настройка:</b> Выстави ловушки по сигналу.",
        'admin_panel': "⚙️ <b>АДМИН ПАНЕЛЬ</b>\n\n👑 Статус: <b>GOD MODE</b>\nВыберите действие:",
        'not_admin': "❌ Вы не админ.",
        'support_text': "🆘 <b>Поддержка</b>\n\n👉 <a href='tg://user?id={admin_id}'>Написать админу</a>",
        'ref_title': "🏆 <b>КОНКУРС</b> 🏆\n\n1 друг = 1 билет.\n🥇 $100\n🥈 $50\n🥉 $20\n\n📊 Твои билеты: <b>{count}</b>\n\n🔗 Ссылка:\n<code>{link}</code>",
        'ref_notify': "🎉 Друг зарегистрировался! +1 билет. Всего: <b>{count}</b>.",
        'ref_success': "🔥 <b>Ты пригласил 3 друзей!</b> Доступ открыт навсегда!"
    },
    'en': {
        'welcome': "💣 <b>MINES AI PREDICTOR</b> 💣\n\nWelcome! Our AI scans <b>Mines</b> algorithms in 1win and finds safe cells with up to 90% accuracy.\n\n👇 Use the buttons below:",
        'btn_reg': "💳 Register", 'btn_instr': "📖 Instruction", 'btn_sign': "💣 Get Signal", 'btn_lang': "🌐 Language", 'btn_ref': "👥 Contest", 'btn_support': "🆘 Support",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Language changed to English 🇬🇧",
        'need_reg': "⚠️ <b>ACCESS BLOCKED!</b>\n\nRegister below to unlock:",
        'regged': "✅ <b>SUCCESS!</b> Click 'Get Signal'! 🚀",
        'choose_traps': "⚙️ <b>Trap Configuration</b>\n\nChoose the number of traps:",
        'btn_trap_1': "🟢 1 trap", 'btn_trap_3': "🟡 3 traps", 'btn_trap_5': "🔴 5 traps",
        'signal_title': "💣 <b>Analysis Complete!</b>\nTraps: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Recommended cells:</b> <code>{cells}</code>\n\n{left}🔥 <i>Good luck!</i>",
        'left_signals': "💡 <i>Signals left: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>LIMIT REACHED!</b>\n\nInvite a friend via '👥 Contest'!",
        'instr_text': "📖 <b>HOW TO START:</b>\n\n1️⃣ <b>Register:</b> <a href='{url}'>CLICK HERE</a>\n2️⃣ <b>Deposit.</b>\n3️⃣ <b>Game:</b> <b>Mines</b>.",
        'admin_panel': "⚙️ <b>ADMIN PANEL</b>\n\n👑 Status: <b>GOD MODE</b>\nChoose action:",
        'not_admin': "❌ No rights.",
        'support_text': "🆘 <b>Support</b>\n\n👉 <a href='tg://user?id={admin_id}'>Message Admin</a>",
        'ref_title': "🏆 <b>CONTEST</b> 🏆\n\n1 friend = 1 ticket.\n🥇 $100\n🥈 $50\n🥉 $20\n\n📊 Tickets: <b>{count}</b>\n\n🔗 Link:\n<code>{link}</code>",
        'ref_notify': "🎉 Friend registered! +1 ticket. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>3 friends invited!</b> Access open forever!"
    },
    'pt': {
        'welcome': "💣 <b>MINES AI PREDICTOR</b> 💣\n\nBem-vindo! Nossa IA escaneia os algoritmos do <b>Mines</b> na 1win e encontra células seguras com até 90% de precisão.\n\n👇 Use os botões abaixo:",
        'btn_reg': "💳 Registre-se", 'btn_instr': "📖 Instrução", 'btn_sign': "💣 Obter Sinal", 'btn_lang': "🌐 Idioma", 'btn_ref': "👥 Concurso", 'btn_support': "🆘 Suporte",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma alterado para Português 🇵🇹",
        'need_reg': "⚠️ <b>ACESSO BLOQUEADO!</b>\n\nRegistre-se abaixo para desbloquear:",
        'regged': "✅ <b>SUCESSO!</b> Clique em 'Obter Sinal'! 🚀",
        'choose_traps': "⚙️ <b>Configuração de Armadilhas</b>\n\nEscolha o número de armadilhas:",
        'btn_trap_1': "🟢 1 armadilha", 'btn_trap_3': "🟡 3 armadilhas", 'btn_trap_5': "🔴 5 armadilhas",
        'signal_title': "💣 <b>Análise Concluída!</b>\nArmadilhas: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Células recomendadas:</b> <code>{cells}</code>\n\n{left}🔥 <i>Boa sorte!</i>",
        'left_signals': "💡 <i>Sinais restantes: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>LIMITE ATINGIDO!</b>\n\nConvide um amigo pelo botão '👥 Concurso'!",
        'instr_text': "📖 <b>COMO COMEÇAR:</b>\n\n1️⃣ <b>Registro:</b> <a href='{url}'>CLIQUE AQUI</a>\n2️⃣ <b>Depósito.</b>\n3️⃣ <b>Jogo:</b> <b>Mines</b>.",
        'admin_panel': "⚙️ <b>PAINEL ADMIN</b>\n\n👑 Status: <b>GOD MODE</b>\nEscolha a ação:",
        'not_admin': "❌ Sem direitos.",
        'support_text': "🆘 <b>Suporte</b>\n\n👉 <a href='tg://user?id={admin_id}'>Mensagem ao Admin</a>",
        'ref_title': "🏆 <b>CONCURSO</b> 🏆\n\n1 amigo = 1 bilhete.\n🥇 $100\n🥈 $50\n🥉 $20\n\n📊 Seus bilhetes: <b>{count}</b>\n\n🔗 Link:\n<code>{link}</code>",
        'ref_notify': "🎉 Amigo registrado! +1 bilhete. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>3 amigos convidados!</b> Acesso aberto para sempre!"
    },
    'es': {
        'welcome': "💣 <b>MINES AI PREDICTOR</b> 💣\n\n¡Bienvenido! Nuestra IA escanea los algoritmos de <b>Mines</b> en 1win y encuentra celdas seguras con hasta un 90% de precisión.\n\n👇 Usa los botones de abajo:",
        'btn_reg': "💳 Registrarse", 'btn_instr': "📖 Instrucción", 'btn_sign': "💣 Obtener Señal", 'btn_lang': "🌐 Idioma", 'btn_ref': "👥 Concurso", 'btn_support': "🆘 Soporte",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma cambiado a Español 🇪🇸",
        'need_reg': "⚠️ <b>¡ACCESO BLOQUEADO!</b>\n\nRegístrate abajo para desbloquear:",
        'regged': "✅ <b>¡ÉXITO!</b> ¡Haz clic en 'Obtener Señal'! 🚀",
        'choose_traps': "⚙️ <b>Configuración de Trampas</b>\n\nElige el número de trampas:",
        'btn_trap_1': "🟢 1 trampa", 'btn_trap_3': "🟡 3 trampas", 'btn_trap_5': "🔴 5 trampas",
        'signal_title': "💣 <b>¡Análisis Completado!</b>\nTrampas: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Celdas recomendadas:</b> <code>{cells}</code>\n\n{left}🔥 <i>¡Buena suerte!</i>",
        'left_signals': "💡 <i>Señales restantes: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>¡LÍMITE ALCANZADO!</b>\n\n¡Invita a un amigo con el botón '👥 Concurso'!",
        'instr_text': "📖 <b>CÓMO EMPEZAR:</b>\n\n1️⃣ <b>Registro:</b> <a href='{url}'>HAZ CLIC AQUÍ</a>\n2️⃣ <b>Depósito.</b>\n3️⃣ <b>Juego:</b> <b>Mines</b>.",
        'admin_panel': "⚙️ <b>PANEL ADMIN</b>\n\n👑 Estado: <b>GOD MODE</b>\nElige acción:",
        'not_admin': "❌ Sin derechos.",
        'support_text': "🆘 <b>Soporte</b>\n\n👉 <a href='tg://user?id={admin_id}'>Mensaje al Admin</a>",
        'ref_title': "🏆 <b>CONCURSO</b> 🏆\n\n1 amigo = 1 boleto.\n🥇 $100\n🥈 $50\n🥉 $20\n\n📊 Tus boletos: <b>{count}</b>\n\n🔗 Enlace:\n<code>{link}</code>",
        'ref_notify': "🎉 ¡Amigo registrado! +1 boleto. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>¡3 amigos invitados!</b> ¡Acceso abierto para siempre!"
    },
    'hi': {
        'welcome': "💣 <b>MINES AI PREDICTOR</b> 💣\n\nस्वागत है! हमारा AI 1win में <b>Mines</b> एल्गोरिदम को स्कैन करता है और 90% तक सटीकता के साथ सुरक्षित सेल ढूंढता है।\n\n👇 नीचे दिए गए बटनों का उपयोग करें:",
        'btn_reg': "💳 पंजीकरण करें", 'btn_instr': "📖 निर्देश", 'btn_sign': "💣 सिग्नल प्राप्त करें", 'btn_lang': "🌐 भाषा", 'btn_ref': "👥 प्रतियोगिता", 'btn_support': "🆘 सहायता",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "भाषा हिंदी में बदल गई 🇮🇳",
        'need_reg': "⚠️ <b>पहुंच अवरुद्ध!</b>\n\nअनलॉक करने के लिए नीचे पंजीकरण करें:",
        'regged': "✅ <b>सफलता!</b> 'सिग्नल प्राप्त करें' पर क्लिक करें! 🚀",
        'choose_traps': "⚙️ <b>जाल कॉन्फ़िगरेशन</b>\n\nजाल की संख्या चुनें:",
        'btn_trap_1': "🟢 1 जाल", 'btn_trap_3': "🟡 3 जाल", 'btn_trap_5': "🔴 5 जाल",
        'signal_title': "💣 <b>विश्लेषण पूरा!</b>\nजाल: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>अनुशंसित सेल:</b> <code>{cells}</code>\n\n{left}🔥 <i>शुभकामनाएं!</i>",
        'left_signals': "💡 <i>शेष सिग्नल: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>सीमा समाप्त!</b>\n\n'👥 प्रतियोगिता' बटन के माध्यम से दोस्त को आमंत्रित करें!",
        'instr_text': "📖 <b>कैसे शुरू करें:</b>\n\n1️⃣ <b>पंजीकरण:</b> <a href='{url}'>यहाँ क्लिक करें</a>\n2️⃣ <b>जमा।</b>\n3️⃣ <b>गेम:</b> <b>Mines</b>।",
        'admin_panel': "⚙️ <b>एडमिन पैनल</b>\n\n👑 स्थिति: <b>GOD MODE</b>\nकार्रवाई चुनें:",
        'not_admin': "❌ कोई अधिकार नहीं।",
        'support_text': "🆘 <b>सहायता</b>\n\n👉 <a href='tg://user?id={admin_id}'>एडमिन को संदेश</a>",
        'ref_title': "🏆 <b>प्रतियोगिता</b> 🏆\n\n1 दोस्त = 1 टिकट।\n🥇 $100\n🥈 $50\n🥉 $20\n\n📊 आपके टिकट: <b>{count}</b>\n\n🔗 लिंक:\n<code>{link}</code>",
        'ref_notify': "🎉 दोस्त पंजीकृत! +1 टिकट। कुल: <b>{count}</b>।",
        'ref_success': "🔥 <b>3 दोस्त आमंत्रित!</b> पहुंच हमेशा के लिए खुली!"
    },
    'ar': {
        'welcome': "💣 <b>MINES AI PREDICTOR</b> 💣\n\nمرحبًا! يقوم الذكاء الاصطناعي لدينا بفحص خوارزميات <b>Mines</b> في 1win ويجد خلايا آمنة بدقة تصل إلى 90٪.\n\n👇 استخدم الأزرار أدناه:",
        'btn_reg': "💳 التسجيل", 'btn_instr': "📖 تعليمات", 'btn_sign': "💣 الحصول على إشارة", 'btn_lang': "🌐 اللغة", 'btn_ref': "👥 مسابقة", 'btn_support': "🆘 الدعم",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "تم تغيير اللغة إلى العربية 🇸🇦",
        'need_reg': "⚠️ <b>تم حظر الوصول!</b>\n\nسجل أدناه لفتح القفل:",
        'regged': "✅ <b>نجاح!</b> انقر على 'الحصول على إشارة'! 🚀",
        'choose_traps': "⚙️ <b>تكوين الفخاخ</b>\n\nاختر عدد الفخاخ:",
        'btn_trap_1': "🟢 فخ واحد", 'btn_trap_3': "🟡 3 فخاخ", 'btn_trap_5': "🔴 5 فخاخ",
        'signal_title': "💣 <b>اكتمل التحليل!</b>\nالفخاخ: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>الخلايا الموصى بها:</b> <code>{cells}</code>\n\n{left}🔥 <i>حظا سعيدا!</i>",
        'left_signals': "💡 <i>الإشارات المتبقية: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>تم الوصول إلى الحد الأقصى!</b>\n\nادعو صديقًا من خلال زر '👥 مسابقة'!",
        'instr_text': "📖 <b>كيف تبدأ:</b>\n\n1️⃣ <b>التسجيل:</b> <a href='{url}'>انقر هنا</a>\n2️⃣ <b>إيداع.</b>\n3️⃣ <b>اللعبة:</b> <b>Mines</b>.",
        'admin_panel': "⚙️ <b>لوحة المسؤول</b>\n\n👑 الحالة: <b>GOD MODE</b>\nاختر الإجراء:",
        'not_admin': "❌ لا حقوق.",
        'support_text': "🆘 <b>الدعم</b>\n\n👉 <a href='tg://user?id={admin_id}'>مراسلة المسؤول</a>",
        'ref_title': "🏆 <b>مسابقة</b> 🏆\n\n1 صديق = 1 تذكرة.\n🥇 $100\n🥈 $50\n🥉 $20\n\n📊 تذاكرك: <b>{count}</b>\n\n🔗 رابط:\n<code>{link}</code>",
        'ref_notify': "🎉 سجل صديق! +1 تذكرة. الإجمالي: <b>{count}</b>.",
        'ref_success': "🔥 <b>لقد دعوت 3 أصدقاء!</b> الوصول مفتوح للأبد!"
    }
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("mines")

class Broadcast(StatesGroup):
    waiting_msg = State()

# Функция безопасного подключения к БД (защита от блокировок)
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL;") # Режим WAL предотвращает зависания при одновременном доступе
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS user (user_id INTEGER PRIMARY KEY, postback_id TEXT, language TEXT DEFAULT 'ru', referrer_id INTEGER, daily_signals INTEGER DEFAULT 0, last_signal_date TEXT, total_deposit REAL DEFAULT 0)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        for col, typ in [("language", "TEXT DEFAULT 'ru'"), ("referrer_id", "INTEGER"), ("daily_signals", "INTEGER DEFAULT 0"), ("last_signal_date", "TEXT"), ("total_deposit", "REAL DEFAULT 0")]:
            try: conn.execute(f"ALTER TABLE user ADD COLUMN {col} {typ}")
            except sqlite3.OperationalError: pass

# ============================================================
# НАСТРОЙКИ УВЕДОМЛЕНИЙ
# ============================================================
def get_notify_enabled() -> bool:
    try:
        with open(CONFIG_PATH, "r") as f:
            return f.read().strip() == "1"
    except FileNotFoundError:
        return True

def set_notify_enabled(state: bool):
    with open(CONFIG_PATH, "w") as f:
        f.write("1" if state else "0")

def log_event(uid: int, event: str):
    try:
        with get_db() as conn:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO events (user_id, event, created_at) VALUES (?, ?, ?)", (uid, event, now))
            conn.commit()
    except Exception as e:
        log.error(f"Event log error: {e}")

async def notify_admin(text: str, uid: int = None):
    if not get_notify_enabled():
        return
    try:
        prefix = ""
        if uid:
            prefix = f"👤 <code>{uid}</code>\n"
        await bot.send_message(ADMIN_ID, f"{prefix}{text}")
    except Exception as e:
        log.error(f"Notify admin error: {e}")

def get_user(uid: int):
    with get_db() as conn:
        row = conn.execute("SELECT postback_id, language, referrer_id, daily_signals, last_signal_date, total_deposit FROM user WHERE user_id = ?", (uid,)).fetchone()
        if row:
            lang = row[1] if row[1] in LANG else 'ru'
            ref_count = conn.execute("SELECT COUNT(*) FROM user WHERE referrer_id = ? AND postback_id IS NOT NULL AND postback_id != 'null'", (uid,)).fetchone()[0]
            return {"user_id": uid, "postback_id": row[0], "lang": lang, "referrer_id": row[2], "ref_count": ref_count, "daily_signals": row[3] or 0, "last_signal_date": row[4], "total_deposit": row[5] or 0}
    return None

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML", link_preview_is_disabled=True))
dp = Dispatcher(storage=MemoryStorage())

# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def get_lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"), InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")],
        [InlineKeyboardButton(text="🇵🇹 Português", callback_data="set_lang_pt"), InlineKeyboardButton(text="🇪🇸 Español", callback_data="set_lang_es")],
        [InlineKeyboardButton(text="🇮🇳 हिंदी", callback_data="set_lang_hi"), InlineKeyboardButton(text="🇸🇦 العربية", callback_data="set_lang_ar")]
    ])

def get_reply_menu(lang):
    """Постоянные кнопки над чатом (Reply-клавиатура)."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton(text=LANG[lang]['btn_sign']))
    kb.row(KeyboardButton(text=LANG[lang]['btn_reg']), KeyboardButton(text=LANG[lang]['btn_instr']))
    kb.row(KeyboardButton(text=LANG[lang]['btn_ref']), KeyboardButton(text=LANG[lang]['btn_support']), KeyboardButton(text=LANG[lang]['btn_lang']))
    return kb

def reg_kb(uid, lang):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANG[lang]['btn_reg'], url=PARTNER_URL.format(uid=uid))]])

def traps_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG[lang]['btn_trap_1'], callback_data="gen_trap_1")],
        [InlineKeyboardButton(text=LANG[lang]['btn_trap_3'], callback_data="gen_trap_3")],
        [InlineKeyboardButton(text=LANG[lang]['btn_trap_5'], callback_data="gen_trap_5")]
    ])

# ============================================================
# ГЕНЕРАЦИЯ СИГНАЛА
# ============================================================
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

def get_fake_win(lang='ru'):
    names = ["Alex", "Max", "Ivan", "Denis", "Artem", "Vlad", "Favour", "Joyce Appiah", "Murilo Hodas"]
    name = random.choice(names)
    win = random.randint(500, 85000)
    mult = round(random.uniform(1.2, 9.5), 2)
    if lang in ['ru', 'ar']: curr = "₽"
    else: curr = "$"
    return f"🔥 <i>{name} just cashed out {curr}{win:,} in Mines (x{mult})!</i>"

# ============================================================
# ОБРАБОТЧИКИ
# ============================================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    uid = message.from_user.id
    ref = command.args
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO user (user_id) VALUES (?)", (uid,))
        if ref and ref.isdigit() and int(ref) != uid:
            conn.execute("UPDATE user SET referrer_id = ? WHERE user_id = ? AND referrer_id IS NULL", (int(ref), uid))
        conn.commit()
    log_event(uid, "start")
    
    name = message.from_user.first_name or "NoName"
    uname = f"@{message.from_user.username}" if message.from_user.username else "без юзернейма"
    await notify_admin(f"🆕 <b>НОВЫЙ ЮЗЕР!</b>\n👤 {name} ({uname})", uid)
    
    await message.answer(LANG['ru']['choose_lang'], reply_markup=get_lang_kb())

@dp.callback_query(F.data.startswith("set_lang_"))
async def cb_set_lang(call: types.CallbackQuery):
    try:
        lang = call.data.split("_")[-1]
        log_event(call.from_user.id, f"set_lang_{lang}")
        
        with get_db() as conn: 
            conn.execute("UPDATE user SET language = ? WHERE user_id = ?", (lang, call.from_user.id))
            conn.commit()
            
        # Сразу убираем "часики" загрузки на кнопке
        await call.answer(LANG[lang]['lang_set'])
        
        welcome_text = f"{LANG[lang]['welcome']}\n\n{get_fake_win(lang)}"
        
        # Отправляем новое сообщение и показываем клавиатуру
        await bot.send_message(
            chat_id=call.from_user.id, 
            text=welcome_text, 
            reply_markup=get_reply_menu(lang)
        )
        
        # Пытаемся удалить старое сообщение с выбором языка
        try:
            await call.message.delete()
        except Exception as e:
            log.warning(f"Не удалось удалить сообщение: {e}")
            
        await notify_admin(f"🌐 Выбрал язык: <b>{lang.upper()}</b>", call.from_user.id)
    except Exception as e:
        log.error(f"Ошибка в обработчике языка: {e}", exc_info=True)
        await call.answer("Произошла ошибка. Попробуйте еще раз.", show_alert=True)

@dp.callback_query(F.data == "lang_menu")
async def cb_lang_menu(call: types.CallbackQuery):
    await call.message.answer(LANG['ru']['choose_lang'], reply_markup=get_lang_kb())
    await call.answer()

# ============================================================
# ОБРАБОТЧИКИ REPLY-КНОПОК
# ============================================================
sign_texts = [LANG[l]['btn_sign'] for l in LANG]
reg_texts = [LANG[l]['btn_reg'] for l in LANG]
instr_texts = [LANG[l]['btn_instr'] for l in LANG]
ref_texts = [LANG[l]['btn_ref'] for l in LANG]
support_texts = [LANG[l]['btn_support'] for l in LANG]
lang_texts = [LANG[l]['btn_lang'] for l in LANG]

@dp.message(F.text.in_(sign_texts))
async def reply_sign(message: types.Message):
    uid = message.from_user.id
    u = get_user(uid)
    lang = u['lang'] if u else 'ru'
    is_registered = u and u['postback_id'] and u['postback_id'].lower() != "null"
    
    if not u or (not is_registered and u['ref_count'] < 3):
        log_event(uid, "sign_blocked_no_reg")
        await notify_admin("🚫 <b>Пытался получить сигнал БЕЗ регистрации</b>", uid)
        await message.answer(LANG[lang]['need_reg'], reply_markup=reg_kb(uid, lang))
        return
        
    log_event(uid, "click_sign_allowed")
    await message.answer(LANG[lang]['choose_traps'], reply_markup=traps_menu(lang))

@dp.message(F.text.in_(reg_texts))
async def reply_reg(message: types.Message):
    uid = message.from_user.id
    u = get_user(uid); lang = u['lang'] if u else 'ru'
    log_event(uid, "click_register_btn")
    await notify_admin("💳 <b>Нажал «Регистрация»!</b>", uid)
    await message.answer(LANG[lang]['need_reg'], reply_markup=reg_kb(uid, lang))

@dp.message(F.text.in_(instr_texts))
async def reply_instr(message: types.Message):
    uid = message.from_user.id
    u = get_user(uid); lang = u['lang'] if u else 'ru'
    log_event(uid, "click_instruction")
    await notify_admin("📖 <b>Открыл инструкцию</b>", uid)
    await message.answer(LANG[lang]['instr_text'].format(url=PARTNER_URL.format(uid=uid)))

@dp.message(F.text.in_(ref_texts))
async def reply_ref(message: types.Message):
    uid = message.from_user.id
    u = get_user(uid); lang = u['lang'] if u else 'ru'
    log_event(uid, "click_ref_menu")
    await notify_admin("👥 <b>Открыл меню конкурса</b>", uid)
    b_info = await bot.get_me()
    link = f"https://t.me/{b_info.username}?start={uid}"
    await message.answer(LANG[lang]['ref_title'].format(link=link, count=u['ref_count']))

@dp.message(F.text.in_(support_texts))
async def reply_support(message: types.Message):
    uid = message.from_user.id
    u = get_user(uid); lang = u['lang'] if u else 'ru'
    log_event(uid, "click_support")
    await notify_admin("🆘 <b>Нажал «Поддержка»</b>", uid)
    await message.answer(LANG[lang]['support_text'].format(admin_id=ADMIN_ID))

@dp.message(F.text.in_(lang_texts))
async def reply_lang(message: types.Message):
    log_event(message.from_user.id, "open_lang_menu")
    await message.answer(LANG['ru']['choose_lang'], reply_markup=get_lang_kb())

# ============================================================
# ВЫБОР ЛОВУШЕК (Inline)
# ============================================================
@dp.callback_query(F.data.startswith("gen_trap_"))
async def cb_gen(call: types.CallbackQuery):
    uid = call.from_user.id
    traps = int(call.data.split("_")[-1])
    log_event(uid, f"generate_signal_{traps}_traps")
    
    u = get_user(uid); lang = u['lang'] if u else 'ru'
    is_admin = (str(uid) == str(ADMIN_ID))
    today = datetime.date.today().isoformat()
    daily = 0 if u['last_signal_date'] != today else u['daily_signals']
    
    if not is_admin:
        if daily >= 5:
            log_event(uid, "limit_reached")
            await notify_admin("⚠️ <b>Упёрся в дневной лимит</b>", uid)
            await call.answer("⚠️ Limit reached!", show_alert=True)
            await call.message.answer(LANG[lang]['limit_msg']); return
        daily += 1
        with get_db() as conn:
            conn.execute("UPDATE user SET daily_signals = ?, last_signal_date = ? WHERE user_id = ?", (daily, today, uid)); conn.commit()
        signals_left_str = LANG[lang]['left_signals'].format(left=5 - daily)
    else:
        with get_db() as conn:
            conn.execute("UPDATE user SET last_signal_date = ? WHERE user_id = ?", (today, uid)); conn.commit()
        signals_left_str = "💡 <i>Signals left: ∞ (God Mode)</i>\n\n"

    await notify_admin(f"🎰 <b>Получил сигнал</b> ({traps} traps)", uid)
    
    signal_text = generate_mines_grid(lang, traps, signals_left_str)
    await call.message.edit_text(text=signal_text)
    await call.answer()

# ============================================================
# АДМИН ПАНЕЛЬ
# ============================================================
@dp.message(Command("admin"))
async def cmd_adm(msg: types.Message):
    if str(msg.from_user.id) != str(ADMIN_ID):
        u = get_user(msg.from_user.id); lang = u['lang'] if u else 'ru'
        await msg.answer(LANG[lang]['not_admin'])
        return
        
    status = "🟢 ВКЛ" if get_notify_enabled() else "🔴 ВЫКЛ"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="bc_start")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stat_start")],
        [InlineKeyboardButton(text="📈 Воронка", callback_data="funnel_start")],
        [InlineKeyboardButton(text="🔥 Действия", callback_data="events_start")],
        [InlineKeyboardButton(text=f"🔔 Уведомления: {status}", callback_data="toggle_notify")]
    ])
    await msg.answer(LANG['ru']['admin_panel'], reply_markup=kb)

@dp.callback_query(F.data == "toggle_notify")
async def cb_toggle_notify(call: types.CallbackQuery):
    if str(call.from_user.id) != str(ADMIN_ID): return
    new_state = not get_notify_enabled()
    set_notify_enabled(new_state)
    status = "🟢 ВКЛ" if new_state else "🔴 ВЫКЛ"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="bc_start")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stat_start")],
        [InlineKeyboardButton(text="📈 Воронка", callback_data="funnel_start")],
        [InlineKeyboardButton(text="🔥 Действия", callback_data="events_start")],
        [InlineKeyboardButton(text=f"🔔 Уведомления: {status}", callback_data="toggle_notify")]
    ])
    await call.message.edit_text(LANG['ru']['admin_panel'], reply_markup=kb)
    await call.answer(f"Уведомления: {status}")

@dp.callback_query(F.data == "stat_start")
async def cb_stat(call: types.CallbackQuery):
    if str(call.from_user.id) != str(ADMIN_ID): return
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
        regs = conn.execute("SELECT COUNT(*) FROM user WHERE postback_id IS NOT NULL AND postback_id != 'null'").fetchone()[0]
        deposit = conn.execute("SELECT SUM(total_deposit) FROM user").fetchone()[0] or 0
    text = f"📊 <b>Общая статистика:</b>\n\n👥 Юзеров: <b>{total}</b>\n✅ Регистраций: <b>{regs}</b>\n💰 Депозитов: <b>${deposit:.2f}</b>"
    await call.message.edit_text(text, reply_markup=call.message.reply_markup)
    await call.answer()

@dp.callback_query(F.data == "funnel_start")
async def cb_funnel(call: types.CallbackQuery):
    if str(call.from_user.id) != str(ADMIN_ID): return
    with get_db() as conn:
        starts = conn.execute("SELECT COUNT(DISTINCT user_id) FROM events WHERE event = 'start'").fetchone()[0]
        lang_selected = conn.execute("SELECT COUNT(DISTINCT user_id) FROM events WHERE event LIKE 'set_lang_%'").fetchone()[0]
        reg_clicks = conn.execute("SELECT COUNT(DISTINCT user_id) FROM events WHERE event = 'click_register_btn'").fetchone()[0]
        sign_blocked = conn.execute("SELECT COUNT(DISTINCT user_id) FROM events WHERE event = 'sign_blocked_no_reg'").fetchone()[0]
        regs = conn.execute("SELECT COUNT(*) FROM user WHERE postback_id IS NOT NULL AND postback_id != 'null'").fetchone()[0]
    
    def pct(a, b): return f" ({int(a/b*100)}%)" if b else ""
    text = (
        f"📈 <b>ВОРОНКА</b>\n\n"
        f"1️⃣ /start: <b>{starts}</b>\n"
        f"2️⃣ Язык: <b>{lang_selected}</b>{pct(lang_selected, starts)}\n"
        f"3️⃣ Клик на Рег: <b>{reg_clicks}</b>{pct(reg_clicks, starts)}\n"
        f"4️⃣ Без рег (блок): <b>{sign_blocked}</b>\n"
        f"5️⃣ Реальные реги: <b>{regs}</b>\n"
    )
    await call.message.edit_text(text, reply_markup=call.message.reply_markup)
    await call.answer()

@dp.callback_query(F.data == "events_start")
async def cb_events(call: types.CallbackQuery):
    if str(call.from_user.id) != str(ADMIN_ID): return
    with get_db() as conn:
        rows = conn.execute("SELECT event, COUNT(*) FROM events GROUP BY event ORDER BY 2 DESC LIMIT 15").fetchall()
    text = "🔥 <b>ТОП-15 ДЕЙСТВИЙ:</b>\n\n"
    for event, count in rows:
        text += f"• <code>{event}</code> — <b>{count}</b>\n"
    if not rows: text = "Пока нет событий."
    await call.message.edit_text(text, reply_markup=call.message.reply_markup)
    await call.answer()

@dp.callback_query(F.data == "bc_start")
async def cb_bc_start(call: types.CallbackQuery, state: FSMContext):
    if str(call.from_user.id) != str(ADMIN_ID): return
    await call.message.edit_text("📢 Отправьте текст (или фото/видео) для рассылки всем пользователям:")
    await state.set_state(Broadcast.waiting_msg)
    await call.answer()

@dp.message(Broadcast.waiting_msg, F.content_type.in_({'text', 'photo', 'video'}))
async def process_broadcast(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != str(ADMIN_ID): return
    await state.clear()
    with get_db() as conn:
        users = conn.execute("SELECT user_id FROM user").fetchall()
    await message.answer(f"🚀 Начинаю рассылку на {len(users)} пользователей...")
    success = 0
    for (uid,) in users:
        try:
            await message.copy_to(chat_id=uid)
            success += 1
            await asyncio.sleep(0.05)
        except Exception: pass
    await message.answer(f"✅ <b>Рассылка завершена!</b>\n\nУспешно доставлено: <b>{success}</b> из <b>{len(users)}</b>")

@dp.message(Command("top"))
async def cmd_top(msg: types.Message):
    if str(msg.from_user.id) != str(ADMIN_ID): return
    with get_db() as conn:
        rows = conn.execute("SELECT u1.user_id, COUNT(u2.user_id) FROM user u1 JOIN user u2 ON u1.user_id = u2.referrer_id WHERE u2.postback_id IS NOT NULL GROUP BY u1.user_id ORDER BY 2 DESC LIMIT 10").fetchall()
    text = "🏆 <b>ТОП-10</b>\n\n" + "".join([f"{i}. ID: <code>{r[0]}</code> — <b>{r[1]} билетов</b>\n" for i, r in enumerate(rows, 1)]) if rows else "Нет рефералов."
    await msg.answer(text)

# ============================================================
# ВСТРОЕННЫЙ ВЕБ-СЕРВЕР
# ============================================================
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == '/health': self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok": true}'); return
        
        if p.path == '/api/stats':
            with get_db() as conn:
                total = conn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
                regs = conn.execute("SELECT COUNT(*) FROM user WHERE postback_id IS NOT NULL AND postback_id != 'null'").fetchone()[0]
                total_deposit = conn.execute("SELECT SUM(total_deposit) FROM user").fetchone()[0] or 0
                recent = conn.execute("SELECT user_id, postback_id FROM user WHERE postback_id IS NOT NULL ORDER BY rowid DESC LIMIT 10").fetchall()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"total": total, "regs": regs, "deposit": total_deposit, "recent": recent}).encode())
            return

        if p.path == '/postback':
            q = urllib.parse.parse_qs(p.query)
            s1 = q.get('sub1',[''])[0]
            s2 = q.get('subid',[''])[0]
            amount_str = q.get('amount',['0'])[0]
            
            if not s1 or not s2: self.send_response(400); self.end_headers(); return
            try: 
                uid = int(s1)
                amount = float(amount_str) if amount_str else 0.0
            except: self.send_response(400); self.end_headers(); return
            
            with get_db() as conn: 
                conn.execute("INSERT INTO user (user_id, postback_id, total_deposit) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET postback_id = excluded.postback_id, total_deposit = user.total_deposit + excluded.total_deposit", (uid, s2, amount))
                conn.commit()
            
            log_event(uid, "postback_received")
            u = get_user(uid); lang = u['lang'] if u else 'ru'
            
            try:
                msg_text = LANG[lang]['regged']
                url_tg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={uid}&text={urllib.parse.quote(msg_text)}&parse_mode=HTML"
                urllib.request.urlopen(url_tg, timeout=10)
                log_event(uid, "postback_msg_sent")
            except urllib.error.HTTPError as e:
                if e.code == 400: log_event(uid, "postback_msg_failed_no_start")
            except Exception: pass
            
            self.send_response(200); self.end_headers(); self.wfile.write(f"sub1={s1}; subid={s2}; amount={amount}; OK".encode('utf-8')); return
        self.send_response(404); self.end_headers()

# ============================================================
# ЗАПУСК
# ============================================================
async def main():
    # ВАЖНО: Очищаем возможные вебхуки, чтобы кнопки работали корректно
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="Menu"))
    log.info("Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    # Запуск веб-сервера в отдельном потоке
    threading.Thread(target=lambda: http.server.HTTPServer(('0.0.0.0', WEB_PORT), Handler).serve_forever(), daemon=True).start()
    log.info("Web server started on port %s", WEB_PORT)
    asyncio.run(main())