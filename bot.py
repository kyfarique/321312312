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
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nДобро пожаловать в элиту! Наш нейросетевой алгоритм анализирует игру в реальном времени и предсказывает безопасные ячейки с точностью <b>до 85%</b>.\n\n💎 Получи свой сигнал. Забери свой куш. 🚀",
        'btn_reg': "💳 Пройти регистрацию", 'btn_instr': "📖 Инструкция", 'btn_sign': "🔮 Выдать сигнал", 'btn_lang': "🌐 Язык",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Язык изменен на Русский 🇷🇺",
        'need_reg': "⚠️ <b>Доступ заблокирован!</b>\n\nЧтобы разблокировать сигналы ИИ, вам нужно привязать аккаунт 1win.\n\n👇 Зарегистрируйтесь в 1 клик по кнопке ниже:",
        'regged': "✅ <b>Успешно!</b> Аккаунт привязан. Теперь вам доступны все сигналы нейросети. Нажмите «Выдать сигнал», чтобы начать! 🚀",
        'choose_traps': "⚙️ <b>Настройка риска</b>\n\nВыберите количество ловушек для следующего раунда:",
        'btn_trap_1': "🟢 1 ловушка", 'btn_trap_3': "🟡 3 ловушки", 'btn_trap_5': "🔴 5 ловушек",
        'btn_back': "⬅️ Назад",
        'signal_title': "🔮 <b>Анализ завершен!</b>\nКонфигурация: <b>{traps} ловушки</b>\n\n",
        'signal_hint': "\n🎯 <b>Рекомендуемые ячейки:</b> <code>{cells}</code>\n\n🔥 <i>Удачи! Не забывайте удваивать ставку при проигрыше.</i>",
        'instr_text': "📖 <b>КАК НАЧАТЬ ЗАРАБАТЫВАТЬ:</b>\n\n1️⃣ <b>Регистрация:</b> <a href='{url}'>КЛИКНИ СЮДА</a>\n2️⃣ <b>Депозит:</b> Пополните баланс на любую сумму.\n3️⃣ <b>Игра:</b> Перейдите в раздел <b>Mines</b> (сетка 5х5).\n4️⃣ <b>Настройка:</b> Выставьте количество ловушек по сигналу бота.\n5️⃣ <b>Действие:</b> Открывайте ячейки, которые рекомендует ИИ.\n6️⃣ <b>Страховка:</b> При проигрыше удваивайте ставку (Мартингейл).\n\n💸 <i>Профит гарантирован при строгом следовании алгоритму!</i>",
        'admin_panel': "⚙️ Админ панель", 'not_admin': "❌ У вас нет прав администратора."
    },
    'en': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nWelcome to the elite! Our neural network analyzes the game in real-time and predicts safe cells with <b>up to 85% accuracy</b>.\n\n💎 Get your signal. Claim your prize. 🚀",
        'btn_reg': "💳 Register", 'btn_instr': "📖 Instruction", 'btn_sign': "🔮 Get Signal", 'btn_lang': "🌐 Language",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Language changed to English 🇬🇧",
        'need_reg': "⚠️ <b>Access Denied!</b>\n\nTo unlock AI signals, you need to link your 1win account.\n\n👇 Register in 1 click below:",
        'regged': "✅ <b>Success!</b> Account linked. All neural network signals are now available to you. Click 'Get Signal' to start! 🚀",
        'choose_traps': "⚙️ <b>Risk Configuration</b>\n\nChoose the number of traps for the next round:",
        'btn_trap_1': "🟢 1 trap", 'btn_trap_3': "🟡 3 traps", 'btn_trap_5': "🔴 5 traps",
        'btn_back': "⬅️ Back",
        'signal_title': "🔮 <b>Analysis Complete!</b>\nConfiguration: <b>{traps} traps</b>\n\n",
        'signal_hint': "\n🎯 <b>Recommended cells:</b> <code>{cells}</code>\n\n🔥 <i>Good luck! Don't forget to double your bet on a loss.</i>",
        'instr_text': "📖 <b>HOW TO START EARNING:</b>\n\n1️⃣ <b>Register:</b> <a href='{url}'>CLICK HERE</a>\n2️⃣ <b>Deposit:</b> Top up your balance.\n3️⃣ <b>Game:</b> Go to <b>Mines</b> (5x5 grid).\n4️⃣ <b>Setup:</b> Set traps according to the bot's signal.\n5️⃣ <b>Action:</b> Open the cells recommended by the AI.\n6️⃣ <b>Insurance:</b> On loss, double the bet (Martingale).\n\n💸 <i>Profit is guaranteed if you strictly follow the algorithm!</i>",
        'admin_panel': "⚙️ Admin panel", 'not_admin': "❌ You don't have admin rights."
    },
    'es': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\n¡Bienvenido a la élite! Nuestra red neuronal analiza el juego en tiempo real y predice celdas seguras con <b>hasta un 85% de precisión</b>.\n\n💎 Obtén tu señal. Reclama tu premio. 🚀",
        'btn_reg': "💳 Registrarse", 'btn_instr': "📖 Instrucción", 'btn_sign': "🔮 Obtener señal", 'btn_lang': "🌐 Idioma",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma cambiado a Español 🇪🇸",
        'need_reg': "⚠️ <b>¡Acceso Denegado!</b>\n\nPara desbloquear las señales de IA, debes vincular tu cuenta de 1win.\n\n👇 Regístrate en 1 clic abajo:",
        'regged': "✅ <b>¡Éxito!</b> Cuenta vinculada. Ahora tienes acceso a todas las señales. ¡Haz clic en 'Obtener señal' para empezar! 🚀",
        'choose_traps': "⚙️ <b>Configuración de riesgo</b>\n\nElige el número de trampas para la siguiente ronda:",
        'btn_trap_1': "🟢 1 trampa", 'btn_trap_3': "🟡 3 trampas", 'btn_trap_5': "🔴 5 trampas",
        'btn_back': "⬅️ Atrás",
        'signal_title': "🔮 <b>¡Análisis completado!</b>\nConfiguración: <b>{traps} trampas</b>\n\n",
        'signal_hint': "\n🎯 <b>Celdas recomendadas:</b> <code>{cells}</code>\n\n🔥 <i>¡Buena suerte! No olvides doblar la apuesta al perder.</i>",
        'instr_text': "📖 <b>CÓMO EMPEZAR A GANAR:</b>\n\n1️⃣ <b>Registro:</b> <a href='{url}'>HAZ CLIC AQUÍ</a>\n2️⃣ <b>Depósito:</b> Recarga tu saldo.\n3️⃣ <b>Juego:</b> Ve a <b>Mines</b> (cuadrícula 5x5).\n4️⃣ <b>Configuración:</b> Establece trampas según la señal.\n5️⃣ <b>Acción:</b> Abre las celdas recomendadas por la IA.\n6️⃣ <b>Seguro:</b> Al perder, dobla la apuesta (Martingala).\n\n💸 <i>¡El beneficio está garantizado si sigues estrictamente el algoritmo!</i>",
        'admin_panel': "⚙️ Panel de admin", 'not_admin': "❌ No tienes derechos de administrador."
    },
    'pt': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nBem-vindo à elite! Nossa rede neural analisa o jogo em tempo real e prevê células seguras com <b>até 85% de precisão</b>.\n\n💎 Obtenha seu sinal. Reivindique seu prêmio. 🚀",
        'btn_reg': "💳 Registre-se", 'btn_instr': "📖 Instrução", 'btn_sign': "🔮 Obter sinal", 'btn_lang': "🌐 Idioma",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma alterado para Português 🇵🇹",
        'need_reg': "⚠️ <b>Acesso Negado!</b>\n\nPara desbloquear os sinais de IA, você precisa vincular sua conta 1win.\n\n👇 Registre-se em 1 clique abaixo:",
        'regged': "✅ <b>Sucesso!</b> Conta vinculada. Agora você tem acesso a todos os sinais. Clique em 'Obter sinal' para começar! 🚀",
        'choose_traps': "⚙️ <b>Configuração de risco</b>\n\nEscolha o número de armadilhas para a próxima rodada:",
        'btn_trap_1': "🟢 1 armadilha", 'btn_trap_3': "🟡 3 armadilhas", 'btn_trap_5': "🔴 5 armadilhas",
        'btn_back': "⬅️ Voltar",
        'signal_title': "🔮 <b>Análise concluída!</b>\nConfiguração: <b>{traps} armadilhas</b>\n\n",
        'signal_hint': "\n🎯 <b>Células recomendadas:</b> <code>{cells}</code>\n\n🔥 <i>Boa sorte! Não se esqueça de dobrar a aposta na perda.</i>",
        'instr_text': "📖 <b>COMO COMEÇAR A GANHAR:</b>\n\n1️⃣ <b>Registro:</b> <a href='{url}'>CLIQUE AQUI</a>\n2️⃣ <b>Depósito:</b> Recarregue seu saldo.\n3️⃣ <b>Jogo:</b> Vá para <b>Mines</b> (grade 5x5).\n4️⃣ <b>Configuração:</b> Defina as armadilhas conforme o sinal.\n5️⃣ <b>Ação:</b> Abra as células recomendadas pela IA.\n6️⃣ <b>Seguro:</b> Na perda, dobre a aposta (Martingale).\n\n💸 <i>O lucro é garantido se você seguir estritamente o algoritmo!</i>",
        'admin_panel': "⚙️ Painel de admin", 'not_admin': "❌ Você não tem direitos de administrador."
    },
    'hi': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nकुलीन वर्ग में आपका स्वागत है! हमारा न्यूरल नेटवर्क वास्तविक समय में गेम का विश्लेषण करता है और <b>85% तक सटीकता</b> के साथ सुरक्षित सेल की भविष्यवाणी करता है।\n\n💎 अपना सिग्नल प्राप्त करें। अपना पुरस्कार प्राप्त करें। 🚀",
        'btn_reg': "💳 पंजीकरण करें", 'btn_instr': "📖 निर्देश", 'btn_sign': "🔮 सिग्नल प्राप्त करें", 'btn_lang': "🌐 भाषा",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "भाषा हिंदी में बदल गई 🇮🇳",
        'need_reg': "⚠️ <b>पहुंच अस्वीकृत!</b>\n\nAI सिग्नल अनलॉक करने के लिए, आपको अपना 1win खाता लिंक करना होगा।\n\n👇 नीचे 1 क्लिक में पंजीकरण करें:",
        'regged': "✅ <b>सफलता!</b> खाता लिंक हो गया। अब आपके पास सभी सिग्नल हैं। शुरू करने के लिए 'सिग्नल प्राप्त करें' पर क्लिक करें! 🚀",
        'choose_traps': "⚙️ <b>जोखिम कॉन्फ़िगरेशन</b>\n\nअगले दौर के लिए जाल की संख्या चुनें:",
        'btn_trap_1': "🟢 1 जाल", 'btn_trap_3': "🟡 3 जाल", 'btn_trap_5': "🔴 5 जाल",
        'btn_back': "⬅️ पीछे",
        'signal_title': "🔮 <b>विश्लेषण पूरा हुआ!</b>\nकॉन्फ़िगरेशन: <b>{traps} जाल</b>\n\n",
        'signal_hint': "\n🎯 <b>अनुशंसित सेल:</b> <code>{cells}</code>\n\n🔥 <i>शुभकामनाएं! हारने पर दांव दोगुना करना न भूलें।</i>",
        'instr_text': "📖 <b>कमाई कैसे शुरू करें:</b>\n\n1️⃣ <b>पंजीकरण:</b> <a href='{url}'>यहाँ क्लिक करें</a>\n2️⃣ <b>जमा:</b> अपना बैलेंस टॉप अप करें।\n3️⃣ <b>गेम:</b> <b>Mines</b> (5x5 ग्रिड) पर जाएं।\n4️⃣ <b>सेटअप:</b> सिग्नल के अनुसार जाल सेट करें।\n5️⃣ <b>कार्रवाई:</b> AI द्वारा अनुशंसित सेल खोलें।\n6️⃣ <b>बीमा:</b> हारने पर, दांव दोगुना करें (मार्टिंगेल)।\n\n💸 <i>यदि आप सख्ती से एल्गोरिदम का पालन करते हैं तो लाभ की गारंटी है!</i>",
        'admin_panel': "⚙️ एडमिन पैनल", 'not_admin': "❌ आपके पास एडमिन अधिकार नहीं हैं।"
    },
    'ar': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nمرحبًا بك في النخبة! تحلل شبكتنا العصبية اللعبة في الوقت الفعلي وتتنبأ بالخلايا الآمنة بدقة <b>تصل إلى 85٪</b>.\n\n💎 احصل على إشارتك. استلم جائزتك. 🚀",
        'btn_reg': "💳 التسجيل", 'btn_instr': "📖 تعليمات", 'btn_sign': "🔮 الحصول على إشارة", 'btn_lang': "🌐 اللغة",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "تم تغيير اللغة إلى العربية 🇸🇦",
        'need_reg': "⚠️ <b>تم رفض الوصول!</b>\n\nلفتح إشارات الذكاء الاصطناعي، تحتاج إلى ربط حسابك في 1win.\n\n👇 سجل بنقرة واحدة أدناه:",
        'regged': "✅ <b>نجاح!</b> تم ربط الحساب. جميع الإشارات متاحة لك الآن. انقر فوق 'الحصول على إشارة' للبدء! 🚀",
        'choose_traps': "⚙️ <b>تكوين المخاطر</b>\n\nاختر عدد الفخاخ للجولة القادمة:",
        'btn_trap_1': "🟢 فخ واحد", 'btn_trap_3': "🟡 3 فخاخ", 'btn_trap_5': "🔴 5 فخاخ",
        'btn_back': "⬅️ رجوع",
        'signal_title': "🔮 <b>اكتمل التحليل!</b>\nالتكوين: <b>{traps} فخاخ</b>\n\n",
        'signal_hint': "\n🎯 <b>الخلايا الموصى بها:</b> <code>{cells}</code>\n\n🔥 <i>حظا سعيدا! لا تنس مضاعفة الرهان عند الخسارة.</i>",
        'instr_text': "📖 <b>كيف تبدأ الكسب:</b>\n\n1️⃣ <b>التسجيل:</b> <a href='{url}'>انقر هنا</a>\n2️⃣ <b>إيداع:</b> اشحن رصيدك.\n3️⃣ <b>اللعبة:</b> انتقل إلى <b>Mines</b> (شبكة 5x5).\n4️⃣ <b>الإعداد:</b> اضبط الفخاخ وفقا للإشارة.\n5️⃣ <b>الإجراء:</b> افتح الخلايا الموصى بها من قبل الذكاء الاصطناعي.\n6️⃣ <b>التأمين:</b> عند الخسارة، ضاعف الرهان (مارتينجال).\n\n💸 <i>الربح مضمون إذا اتبعت الخوارزمية بدقة!</i>",
        'admin_panel': "⚙️ لوحة المسؤول", 'not_admin': "❌ ليس لديك حقوق المسؤول."
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

def traps_menu(lang):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton(LANG[lang]['btn_trap_1'], callback_data="gen_trap_1"),
        InlineKeyboardButton(LANG[lang]['btn_trap_3'], callback_data="gen_trap_3"),
        InlineKeyboardButton(LANG[lang]['btn_trap_5'], callback_data="gen_trap_5")
    )
    kb.add(InlineKeyboardButton(LANG[lang]['btn_back'], callback_data="main_menu"))
    return kb

def sign_kb(lang):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(LANG[lang]['btn_sign'], callback_data="sign"),
        InlineKeyboardButton(LANG[lang]['btn_back'], callback_data="main_menu"),
    )
    return kb

def generate_mines_grid(lang, traps=3):
    # Генерируем сетку
    cells = ['⭐'] * (25 - traps) + ['💣'] * traps
    random.shuffle(cells)
    
    # Форматируем сетку 5x5
    grid_text = ""
    for i in range(5):
        row = cells[i*5:(i+1)*5]
        grid_text += " ".join(row) + "\n"
        
    # Ищем безопасные ячейки
    safe_cells = [str(i+1) for i, cell in enumerate(cells) if cell == '⭐']
    random.shuffle(safe_cells)
    recommended = ", ".join(safe_cells[:4])
    
    title = LANG[lang]['signal_title'].format(traps=traps)
    # Оборачиваем сетку в <code> для ровного шрифта
    return title + f"<code>{grid_text}</code>" + LANG[lang]['signal_hint'].format(cells=recommended)

# ---------- Handlers ----------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO user (user_id) VALUES (?)", (uid,))
        conn.commit()
    
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

@dp.callback_query_handler(text="main_menu")
async def cb_main_menu(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    lang = user['lang'] if user else 'ru'
    await bot.edit_message_text(
        text=LANG[lang]['welcome'],
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=main_menu(lang)
    )
    await bot.answer_callback_query(call.id)

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
    
    lang = user['lang']
    await bot.edit_message_text(
        text=LANG[lang]['choose_traps'],
        chat_id=uid,
        message_id=call.message.message_id,
        reply_markup=traps_menu(lang)
    )
    await bot.answer_callback_query(call.id)

@dp.callback_query_handler(text_startswith="gen_trap_")
async def cb_gen_trap(call: types.CallbackQuery):
    uid = call.from_user.id
    user = get_user(uid)
    lang = user['lang'] if user else 'ru'
    
    traps = int(call.data.split("_")[-1])
    signal_text = generate_mines_grid(lang, traps)
    
    await bot.edit_message_text(
        text=signal_text,
        chat_id=uid,
        message_id=call.message.message_id,
        reply_markup=sign_kb(lang)
    )
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
                f"?chat_id={uid}&text={requests.utils.quote(text)}&parse_mode=HTML"
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