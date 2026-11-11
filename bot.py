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
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nДобро пожаловать в элиту! Наш нейросетевой алгоритм анализирует игру и предсказывает безопасные ячейки с точностью <b>до 85%</b>.\n\n💎 Получи свой сигнал. Забери свой куш. 🚀",
        'btn_reg': "💳 Регистрация", 'btn_instr': "📖 Инструкция", 'btn_sign': "🔮 Выдать сигнал", 'btn_lang': "🌐 Язык", 'btn_ref': "👥 Конкурс и Рефералы", 'btn_support': "🆘 Поддержка",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Язык изменен на Русский 🇷🇺",
        'need_reg': "⚠️ <b>Доступ заблокирован!</b>\n\nЧтобы разблокировать сигналы ИИ, вам нужно привязать аккаунт 1win.\n\n👇 Зарегистрируйтесь в 1 клик по кнопке ниже:\n\n<i>Или участвуйте в конкурсе по кнопке «👥 Конкурс и Рефералы»!</i>",
        'regged': "✅ <b>Успешно!</b> Аккаунт привязан. Теперь вам доступны все сигналы нейросети. Нажмите «Выдать сигнал», чтобы начать! 🚀",
        'choose_traps': "⚙️ <b>Настройка риска</b>\n\nВыберите количество ловушек для следующего раунда:",
        'btn_trap_1': "🟢 1 ловушка", 'btn_trap_3': "🟡 3 ловушки", 'btn_trap_5': "🔴 5 ловушек",
        'btn_main': "⬅️ Главное меню",
        'signal_title': "🔮 <b>Анализ завершен!</b>\nКонфигурация: <b>{traps} ловушки</b>\n\n",
        'signal_hint': "\n🎯 <b>Рекомендуемые ячейки:</b> <code>{cells}</code>\n\n🔥 <i>Удачи! Не забывайте удваивать ставку при проигрыше.</i>",
        'instr_text': "📖 <b>КАК НАЧАТЬ ЗАРАБАТЫВАТЬ:</b>\n\n1️⃣ <b>Регистрация:</b> <a href='{url}'>КЛИКНИ СЮДА</a>\n2️⃣ <b>Депозит:</b> Пополните баланс.\n3️⃣ <b>Игра:</b> Перейдите в раздел <b>Mines</b>.\n4️⃣ <b>Настройка:</b> Выставьте ловушки по сигналу.\n5️⃣ <b>Действие:</b> Открывайте ячейки от ИИ.\n6️⃣ <b>Страховка:</b> При проигрыше удваивайте ставку.\n\n💸 <i>Профит гарантирован при строгом следовании!</i>",
        'admin_panel': "⚙️ Админ панель. Команда /top - таблица лидеров.", 'not_admin': "❌ У вас нет прав администратора.",
        'support_text': "🆘 <b>Служба поддержки</b>\n\nЕсли у вас возникли вопросы по работе бота, регистрации или выплатам, напишите нашему менеджеру:\n\n👉 <a href='tg://user?id={admin_id}'>Написать администратору</a>",
        'ref_title': "🏆 <b>КОНКУРС С ПРИЗОВЫМ ФОНДОМ</b> 🏆\n\nПриглашай друзей и зарабатывай билеты! <b>1 зарегистрированный друг = 1 билет.</b>\n\n🥇 <b>1 место:</b> $100\n🥈 <b>2 место:</b> $50\n🥉 <b>3 место:</b> $20\n\n📊 Твои билеты: <b>{count}</b>\n\n🔗 Твоя ссылка для приглашения:\n<code>{link}</code>",
        'ref_notify': "🎉 По твоей ссылке зарегистрировался друг! Ты получил +1 билет. Всего билетов: <b>{count}</b>. Продолжай в том же духе!",
        'ref_success': "🔥 <b>Ты пригласил 3 друзей!</b> Твой доступ к сигналам открыт навсегда. Но не останавливайся, ведь на кону денежные призы!"
    },
    'en': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nWelcome to the elite! Our neural network predicts safe cells with <b>up to 85% accuracy</b>.\n\n💎 Get your signal. Claim your prize. 🚀",
        'btn_reg': "💳 Register", 'btn_instr': "📖 Instruction", 'btn_sign': "🔮 Get Signal", 'btn_lang': "🌐 Language", 'btn_ref': "👥 Contest & Refs", 'btn_support': "🆘 Support",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Language changed to English 🇬🇧",
        'need_reg': "⚠️ <b>Access Denied!</b>\n\nTo unlock AI signals, link your 1win account.\n\n👇 Register below:\n\n<i>Or participate in the contest using the “👥 Contest & Refs” button!</i>",
        'regged': "✅ <b>Success!</b> Account linked. Click 'Get Signal' to start! 🚀",
        'choose_traps': "⚙️ <b>Risk Configuration</b>\n\nChoose the number of traps:",
        'btn_trap_1': "🟢 1 trap", 'btn_trap_3': "🟡 3 traps", 'btn_trap_5': "🔴 5 traps",
        'btn_main': "⬅️ Main Menu",
        'signal_title': "🔮 <b>Analysis Complete!</b>\nConfiguration: <b>{traps} traps</b>\n\n",
        'signal_hint': "\n🎯 <b>Recommended cells:</b> <code>{cells}</code>\n\n🔥 <i>Good luck!</i>",
        'instr_text': "📖 <b>HOW TO START EARNING:</b>\n\n1️⃣ <b>Register:</b> <a href='{url}'>CLICK HERE</a>\n2️⃣ <b>Deposit:</b> Top up your balance.\n3️⃣ <b>Game:</b> Go to <b>Mines</b>.\n4️⃣ <b>Setup:</b> Set traps by signal.\n5️⃣ <b>Action:</b> Open cells from AI.\n6️⃣ <b>Insurance:</b> Double bet on loss.",
        'admin_panel': "⚙️ Admin panel. Command /top - leaderboard.", 'not_admin': "❌ You don't have admin rights.",
        'support_text': "🆘 <b>Support</b>\n\nIf you have questions about the bot, registration, or payouts, contact our manager:\n\n👉 <a href='tg://user?id={admin_id}'>Message Admin</a>",
        'ref_title': "🏆 <b>PRIZE POOL CONTEST</b> 🏆\n\nInvite friends and earn tickets! <b>1 registered friend = 1 ticket.</b>\n\n🥇 <b>1st place:</b> $100\n🥈 <b>2nd place:</b> $50\n🥉 <b>3rd place:</b> $20\n\n📊 Your tickets: <b>{count}</b>\n\n🔗 Your invite link:\n<code>{link}</code>",
        'ref_notify': "🎉 A friend registered via your link! You got +1 ticket. Total tickets: <b>{count}</b>. Keep it up!",
        'ref_success': "🔥 <b>You invited 3 friends!</b> Your access is now open forever. But don't stop, cash prizes are at stake!"
    },
    'es': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\n¡Bienvenido! Predice celdas seguras con <b>hasta un 85% de precisión</b>.\n\n💎 Obtén tu señal. Reclama tu premio. 🚀",
        'btn_reg': "💳 Registrarse", 'btn_instr': "📖 Instrucción", 'btn_sign': "🔮 Obtener señal", 'btn_lang': "🌐 Idioma", 'btn_ref': "👥 Concurso y Refs", 'btn_support': "🆘 Soporte",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma cambiado a Español 🇪🇸",
        'need_reg': "⚠️ <b>¡Acceso Denegado!</b>\n\nVincula tu cuenta de 1win.\n\n👇 Regístrate abajo:\n\n<i>¡O participa en el concurso usando el botón “👥 Concurso y Refs”!</i>",
        'regged': "✅ <b>¡Éxito!</b> Cuenta vinculada. 🚀",
        'choose_traps': "⚙️ <b>Configuración de riesgo</b>\n\nElige el número de trampas:",
        'btn_trap_1': "🟢 1 trampa", 'btn_trap_3': "🟡 3 trampas", 'btn_trap_5': "🔴 5 trampas",
        'btn_main': "⬅️ Menú Principal",
        'signal_title': "🔮 <b>¡Análisis completado!</b>\nTrampas: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Celdas recomendadas:</b> <code>{cells}</code>\n\n🔥 <i>¡Buena suerte!</i>",
        'instr_text': "📖 <b>CÓMO EMPEZAR:</b>\n\n1️⃣ <b>Registro:</b> <a href='{url}'>HAZ CLIC AQUÍ</a>\n2️⃣ <b>Depósito:</b> Recarga.\n3️⃣ <b>Juego:</b> Ve a <b>Mines</b>.\n4️⃣ <b>Configuración:</b> Pon las trampas.\n5️⃣ <b>Acción:</b> Abre las celdas.\n6️⃣ <b>Seguro:</b> Dobla al perder.",
        'admin_panel': "⚙️ Panel de admin. Comando /top.", 'not_admin': "❌ No eres admin.",
        'support_text': "🆘 <b>Soporte</b>\n\nSi tienes preguntas, contacta a nuestro gerente:\n\n👉 <a href='tg://user?id={admin_id}'>Mensaje al Admin</a>",
        'ref_title': "🏆 <b>CONCURSO CON PREMIOS</b> 🏆\n\n¡Invita amigos y gana boletos! <b>1 amigo = 1 boleto.</b>\n\n🥇 <b>1er lugar:</b> $100\n🥈 <b>2do lugar:</b> $50\n🥉 <b>3er lugar:</b> $20\n\n📊 Tus boletos: <b>{count}</b>\n\n🔗 Tu enlace:\n<code>{link}</code>",
        'ref_notify': "🎉 ¡Un amigo se registró! +1 boleto. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>¡Invitaste a 3 amigos!</b> Tu acceso está abierto para siempre. ¡Pero no te detengas, hay premios en efectivo!"
    },
    'pt': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nBem-vindo! Preveja células seguras com <b>até 85% de precisão</b>.\n\n💎 Obtenha seu sinal. Reivindique seu prêmio. 🚀",
        'btn_reg': "💳 Registre-se", 'btn_instr': "📖 Instrução", 'btn_sign': "🔮 Obter sinal", 'btn_lang': "🌐 Idioma", 'btn_ref': "👥 Concurso e Refs", 'btn_support': "🆘 Suporte",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma alterado para Português 🇵🇹",
        'need_reg': "⚠️ <b>Acesso Negado!</b>\n\nVincule sua conta 1win.\n\n👇 Registre-se abaixo:\n\n<i>Ou participe do concurso usando o botão “👥 Concurso e Refs”!</i>",
        'regged': "✅ <b>Sucesso!</b> Conta vinculada. 🚀",
        'choose_traps': "⚙️ <b>Configuração de risco</b>\n\nEscolha o número de armadilhas:",
        'btn_trap_1': "🟢 1 armadilha", 'btn_trap_3': "🟡 3 armadilhas", 'btn_trap_5': "🔴 5 armadilhas",
        'btn_main': "⬅️ Menu Principal",
        'signal_title': "🔮 <b>Análise concluída!</b>\nArmadilhas: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Células recomendadas:</b> <code>{cells}</code>\n\n🔥 <i>Boa sorte!</i>",
        'instr_text': "📖 <b>COMO COMEÇAR:</b>\n\n1️⃣ <b>Registro:</b> <a href='{url}'>CLIQUE AQUI</a>\n2️⃣ <b>Depósito:</b> Recarregue.\n3️⃣ <b>Jogo:</b> Vá para <b>Mines</b>.\n4️⃣ <b>Configuração:</b> Defina as armadilhas.\n5️⃣ <b>Ação:</b> Abra as células.\n6️⃣ <b>Seguro:</b> Dobre na perda.",
        'admin_panel': "⚙️ Painel de admin. Comando /top.", 'not_admin': "❌ Você não é admin.",
        'support_text': "🆘 <b>Suporte</b>\n\nSe tiver dúvidas, entre em contato:\n\n👉 <a href='tg://user?id={admin_id}'>Mensagem para o Admin</a>",
        'ref_title': "🏆 <b>CONCURSO COM PRÊMIOS</b> 🏆\n\nConvide amigos e ganhe bilhetes! <b>1 amigo = 1 bilhete.</b>\n\n🥇 <b>1º lugar:</b> $100\n🥈 <b>2º lugar:</b> $50\n🥉 <b>3º lugar:</b> $20\n\n📊 Seus bilhetes: <b>{count}</b>\n\n🔗 Seu link:\n<code>{link}</code>",
        'ref_notify': "🎉 Um amigo se registrou! +1 bilhete. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>Você convidou 3 amigos!</b> Seu acesso está aberto para sempre. Mas não pare, há prêmios em dinheiro!"
    },
    'hi': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nस्वागत है! <b>85% तक सटीकता</b> के साथ सुरक्षित सेल।\n\n💎 अपना सिग्नल प्राप्त करें। 🚀",
        'btn_reg': "💳 पंजीकरण करें", 'btn_instr': "📖 निर्देश", 'btn_sign': "🔮 सिग्नल प्राप्त करें", 'btn_lang': "🌐 भाषा", 'btn_ref': "👥 प्रतियोगिता और रेफरल", 'btn_support': "🆘 सहायता",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "भाषा हिंदी में बदल गई 🇮🇳",
        'need_reg': "⚠️ <b>पहुंच अस्वीकृत!</b>\n\n1win खाता लिंक करें।\n\n👇 नीचे पंजीकरण करें:\n\n<i>या “👥 प्रतियोगिता और रेफरल” बटन का उपयोग करके प्रतियोगिता में भाग लें!</i>",
        'regged': "✅ <b>सफलता!</b> खाता लिंक हो गया। 🚀",
        'choose_traps': "⚙️ <b>जोखिम कॉन्फ़िगरेशन</b>\n\nजाल की संख्या चुनें:",
        'btn_trap_1': "🟢 1 जाल", 'btn_trap_3': "🟡 3 जाल", 'btn_trap_5': "🔴 5 जाल",
        'btn_main': "⬅️ मुख्य मेनू",
        'signal_title': "🔮 <b>विश्लेषण पूरा!</b>\nजाल: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>अनुशंसित सेल:</b> <code>{cells}</code>\n\n🔥 <i>शुभकामनाएं!</i>",
        'instr_text': "📖 <b>कैसे शुरू करें:</b>\n\n1️⃣ <b>पंजीकरण:</b> <a href='{url}'>यहाँ क्लिक करें</a>\n2️⃣ <b>जमा:</b> टॉप अप करें।\n3️⃣ <b>गेम:</b> <b>Mines</b> पर जाएं।\n4️⃣ <b>सेटअप:</b> जाल सेट करें।\n5️⃣ <b>कार्रवाई:</b> सेल खोलें।\n6️⃣ <b>बीमा:</b> हार पर दोगुना करें।",
        'admin_panel': "⚙️ एडमिन पैनल। कमांड /top।", 'not_admin': "❌ आप एडमिन नहीं हैं।",
        'support_text': "🆘 <b>सहायता</b>\n\nयदि कोई प्रश्न है, तो हमारे प्रबंधक से संपर्क करें:\n\n👉 <a href='tg://user?id={admin_id}'>एडमिन को संदेश भेजें</a>",
        'ref_title': "🏆 <b>पुरस्कार प्रतियोगिता</b> 🏆\n\nदोस्तों को आमंत्रित करें और टिकट कमाएं! <b>1 दोस्त = 1 टिकट।</b>\n\n🥇 <b>प्रथम स्थान:</b> $100\n🥈 <b>द्वितीय स्थान:</b> $50\n🥉 <b>तृतीय स्थान:</b> $20\n\n📊 आपके टिकट: <b>{count}</b>\n\n🔗 आपका लिंक:\n<code>{link}</code>",
        'ref_notify': "🎉 एक दोस्त पंजीकृत हुआ! +1 टिकट। कुल: <b>{count}</b>।",
        'ref_success': "🔥 <b>आपने 3 दोस्तों को आमंत्रित किया!</b> पहुंच हमेशा के लिए खुली है। लेकिन रुकें नहीं, नकद पुरस्कार दांव पर हैं!"
    },
    'ar': {
        'welcome': "🤖 <b>MINES AI PREDICTOR</b> 🤖\n\nمرحبًا! توقع الخلايا الآمنة بدقة <b>تصل إلى 85٪</b>.\n\n💎 احصل على إشارتك. 🚀",
        'btn_reg': "💳 التسجيل", 'btn_instr': "📖 تعليمات", 'btn_sign': "🔮 الحصول على إشارة", 'btn_lang': "🌐 اللغة", 'btn_ref': "👥 المسابقة والإحالات", 'btn_support': "🆘 الدعم",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "تم تغيير اللغة إلى العربية 🇸🇦",
        'need_reg': "⚠️ <b>تم رفض الوصول!</b>\n\nاربط حسابك في 1win.\n\n👇 سجل أدناه:\n\n<i>أو شارك في المسابقة باستخدام زر “👥 المسابقة والإحالات”!</i>",
        'regged': "✅ <b>نجاح!</b> تم ربط الحساب. 🚀",
        'choose_traps': "⚙️ <b>تكوين المخاطر</b>\n\nاختر عدد الفخاخ:",
        'btn_trap_1': "🟢 فخ واحد", 'btn_trap_3': "🟡 3 فخاخ", 'btn_trap_5': "🔴 5 فخاخ",
        'btn_main': "⬅️ القائمة الرئيسية",
        'signal_title': "🔮 <b>اكتمل التحليل!</b>\nالفخاخ: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>الخلايا الموصى بها:</b> <code>{cells}</code>\n\n🔥 <i>حظا سعيدا!</i>",
        'instr_text': "📖 <b>كيف تبدأ:</b>\n\n1️⃣ <b>التسجيل:</b> <a href='{url}'>انقر هنا</a>\n2️⃣ <b>إيداع:</b> اشحن رصيدك.\n3️⃣ <b>اللعبة:</b> انتقل إلى <b>Mines</b>.\n4️⃣ <b>الإعداد:</b> اضبط الفخاخ.\n5️⃣ <b>الإجراء:</b> افتح الخلايا.\n6️⃣ <b>التأمين:</b> ضاعف عند الخسارة.",
        'admin_panel': "⚙️ لوحة المسؤول. الأمر /top.", 'not_admin': "❌ ليس لديك حقوق المسؤول.",
        'support_text': "🆘 <b>الدعم</b>\n\nإذا كان لديك أي أسئلة، اتصل بمديرنا:\n\n👉 <a href='tg://user?id={admin_id}'>مراسلة المسؤول</a>",
        'ref_title': "🏆 <b>مسابقة جوائز</b> 🏆\n\nادعو الأصدقاء واكسب تذاكر! <b>صديق واحد = تذكرة واحدة.</b>\n\n🥇 <b>المركز الأول:</b> $100\n🥈 <b>المركز الثاني:</b> $50\n🥉 <b>المركز الثالث:</b> $20\n\n📊 تذاكرك: <b>{count}</b>\n\n🔗 رابطك:\n<code>{link}</code>",
        'ref_notify': "🎉 سجل صديق عبر رابطك! +1 تذكرة. الإجمالي: <b>{count}</b>.",
        'ref_success': "🔥 <b>لقد دعوت 3 أصدقاء!</b> وصولك مفتوح للأبد. لكن لا تتوقف، الجوائز النقدية على المحك!"
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
                language    TEXT DEFAULT 'ru',
                referrer_id INTEGER
            )
        """)
        conn.commit()
        try:
            conn.execute("ALTER TABLE user ADD COLUMN language TEXT DEFAULT 'ru'")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE user ADD COLUMN referrer_id INTEGER")
        except sqlite3.OperationalError:
            pass

def get_user(uid: int):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT postback_id, language, referrer_id FROM user WHERE user_id = ?", (uid,)).fetchone()
        if row:
            lang = row[1] if row[1] in LANG else 'ru'
            ref_count = conn.execute(
                "SELECT COUNT(*) FROM user WHERE referrer_id = ? AND postback_id IS NOT NULL", 
                (uid,)
            ).fetchone()[0]
            return {"postback_id": row[0], "lang": lang, "referrer_id": row[2], "ref_count": ref_count}
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
        InlineKeyboardButton(LANG[lang]['btn_ref'], callback_data="ref_menu"),
        InlineKeyboardButton(LANG[lang]['btn_support'], callback_data="support"),
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
    kb.add(InlineKeyboardButton(LANG[lang]['btn_main'], callback_data="main_menu"))
    return kb

def sign_kb(lang):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(LANG[lang]['btn_sign'], callback_data="sign"),
        InlineKeyboardButton(LANG[lang]['btn_main'], callback_data="main_menu"),
    )
    return kb

def generate_mines_grid(lang, traps=3):
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
    return title + f"<code>{grid_text}</code>" + LANG[lang]['signal_hint'].format(cells=recommended)

# ---------- Handlers ----------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    
    args = message.get_args()
    referrer_id = None
    if args and args.isdigit():
        referrer_id = int(args)
        if referrer_id == uid:
            referrer_id = None 
            
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO user (user_id) VALUES (?)", (uid,))
        if referrer_id:
            conn.execute("UPDATE user SET referrer_id = ? WHERE user_id = ? AND referrer_id IS NULL", (referrer_id, uid))
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

@dp.callback_query_handler(text="support")
async def cb_support(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    lang = user['lang'] if user else 'ru'
    text = LANG[lang]['support_text'].format(admin_id=ADMIN_ID)
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(LANG[lang]['btn_main'], callback_data="main_menu"))
    
    await bot.edit_message_text(
        text=text,
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        reply_markup=kb,
        disable_web_page_preview=True
    )
    await bot.answer_callback_query(call.id)

@dp.callback_query_handler(text="ref_menu")
async def cb_ref_menu(call: types.CallbackQuery):
    uid = call.from_user.id
    user = get_user(uid)
    lang = user['lang'] if user else 'ru'
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    
    text = LANG[lang]['ref_title'].format(link=ref_link, count=user['ref_count'])
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(LANG[lang]['btn_main'], callback_data="main_menu"))
    
    await bot.edit_message_text(
        text=text,
        chat_id=uid,
        message_id=call.message.message_id,
        reply_markup=kb,
        disable_web_page_preview=True
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
    
    has_access = user and (user['postback_id'] or user['ref_count'] >= 3)
    
    if not has_access:
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

@dp.message_handler(commands=["top"])
async def cmd_top(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return
        
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT u1.user_id, COUNT(u2.user_id) as ref_count
            FROM user u1
            JOIN user u2 ON u1.user_id = u2.referrer_id
            WHERE u2.postback_id IS NOT NULL
            GROUP BY u1.user_id
            ORDER BY ref_count DESC
            LIMIT 10
        """).fetchall()

    if not rows:
        await message.answer("Пока нет рефералов с регистрациями.")
        return

    text = "🏆 <b>ТОП-10 УЧАСТНИКОВ КОНКУРСА</b> 🏆\n\n"
    for i, (uid, count) in enumerate(rows, 1):
        text += f"{i}. ID: <code>{uid}</code> — <b>{count} билетов</b>\n"

    await message.answer(text)

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

            if user and user.get('referrer_id'):
                ref_id = user['referrer_id']
                ref_user = get_user(ref_id)
                if ref_user:
                    ref_lang = ref_user['lang']
                    ref_count = ref_user['ref_count']
                    
                    if ref_count == 3:
                        ref_text = LANG[ref_lang]['ref_success']
                    else:
                        ref_text = LANG[ref_lang]['ref_notify'].format(count=ref_count)
                        
                    ref_url = (
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        f"?chat_id={ref_id}&text={requests.utils.quote(ref_text)}&parse_mode=HTML"
                    )
                    try:
                        requests.get(ref_url, timeout=10)
                    except Exception as e:
                        log.error("ref notify failed: %s", e)

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