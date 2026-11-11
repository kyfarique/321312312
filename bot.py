# -*- coding: utf-8 -*-
import logging
import os
import random
import sqlite3
import threading
import http.server
import urllib.parse
import datetime

import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, MenuButtonCommands

# ============================================================
#  НАСТРОЙКИ
# ============================================================
BOT_TOKEN = "7303209127:AAGHrwgFYbmrh3LFW7mxZl63Yefs_ITYbVQ"
ADMIN_ID  = "6109042131"

DAILY_LIMIT = 5 # Сколько сигналов в день может запросить 1 человек
WEB_PORT    = int(os.getenv("PORT", "5000"))
PARTNER_URL = "https://r1wagwk.com/v3/2158/1win-mines?p=4fgb&sub1={uid}"

# ============================================================

BASE_DIR = os.getenv("DATA_DIR") or os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "DataBase.db")

# --- СЛОВАРИ ПЕРЕВОДОВ ---
LANG = {
    'ru': {
        'welcome': "🔥 <b>ДОСТУП К СЕКРЕТНОМУ АЛГОРИТМУ ПОЛУЧЕН</b> 🔥\n\nПриветствуем в <b>MINES AI PREDICTOR</b>!\n\n😤 Устал сливать депозиты на удачу? Хватит кормить казино. Пора забирать свое.\n\n🧠 Наша нейросеть сканирует паттерны игры <b>Mines</b> в 1win и вычисляет безопасные ячейки с точностью <b>до 85%</b>.\n\n🚀 <b>Начни зарабатывать прямо сейчас!</b> 👇",
        'btn_reg': "💳 Регистрация", 'btn_instr': "📖 Инструкция", 'btn_sign': "🔮 Выдать сигнал", 'btn_lang': "🌐 Язык", 'btn_ref': "👥 Конкурс и Рефералы", 'btn_support': "🆘 Поддержка",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Язык изменен на Русский 🇷🇺",
        'need_reg': "⚠️ <b>ДОСТУП ЗАБЛОКИРОВАН!</b>\n\nАлгоритм ИИ требует привязки аккаунта 1win.\n\n👇 Зарегистрируйся в 1 клик, чтобы открыть доступ:\n\n<i>Или участвуй в конкурсе по кнопке «👥 Конкурс и Рефералы»!</i>",
        'regged': "✅ <b>УСПЕХ!</b> Аккаунт привязан к системе. Нейросеть активирована. Жми «Выдать сигнал»! 🚀",
        'choose_traps': "⚙️ <b>Настройка риска</b>\n\nВыбери количество ловушек для следующего раунда:",
        'btn_trap_1': "🟢 1 ловушка", 'btn_trap_3': "🟡 3 ловушки", 'btn_trap_5': "🔴 5 ловушек",
        'btn_main': "⬅️ Главное меню",
        'signal_title': "🔮 <b>Анализ завершен!</b>\nКонфигурация: <b>{traps} ловушки</b>\n\n",
        'signal_hint': "\n🎯 <b>Рекомендуемые ячейки:</b> <code>{cells}</code>\n\n{left}🔥 <i>Удачи! Не забывай удваивать ставку при проигрыше.</i>",
        'left_signals': "💡 <i>Осталось сигналов на сегодня: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>ДНЕВНОЙ ЛИМИТ ИСЧЕРПАН!</b>\n\nВы использовали все {limit} сигналов на сегодня. Нейросети нужно время для калибровки и анализа новых паттернов.\n\n👇 <b>Хотите больше сигналов?</b> Пригласите друга по кнопке «👥 Конкурс и Рефералы», чтобы получить бонусные попытки!",
        'instr_text': "📖 <b>КАК НАЧАТЬ ЗАРАБАТЫВАТЬ:</b>\n\n1️⃣ <b>Регистрация:</b> <a href='{url}'>КЛИКНИ СЮДА</a>\n2️⃣ <b>Депозит:</b> Пополни баланс.\n3️⃣ <b>Игра:</b> Перейди в раздел <b>Mines</b>.\n4️⃣ <b>Настройка:</b> Выставь ловушки по сигналу.\n5️⃣ <b>Действие:</b> Открывай ячейки от ИИ.\n6️⃣ <b>Страховка:</b> При проигрыше удваивай ставку.\n\n💸 <i>Профит при строгом следовании алгоритму!</i>",
        'admin_panel': "⚙️ Админ панель. Команда /top - таблица лидеров.", 'not_admin': "❌ У вас нет прав администратора.",
        'support_text': "🆘 <b>Служба поддержки</b>\n\nЕсли у вас возникли вопросы по работе бота, регистрации или выплатам, напишите менеджеру:\n\n👉 <a href='tg://user?id={admin_id}'>Написать администратору</a>",
        'ref_title': "🏆 <b>КОНКУРС С ПРИЗОВЫМ ФОНДОМ</b> 🏆\n\nПриглашай друзей и зарабатывай билеты! <b>1 зарегистрированный друг = 1 билет.</b>\n\n🥇 <b>1 место:</b> $100\n🥈 <b>2 место:</b> $50\n🥉 <b>3 место:</b> $20\n\n📊 Твои билеты: <b>{count}</b>\n\n🔗 Твоя ссылка для приглашения:\n<code>{link}</code>",
        'ref_notify': "🎉 По твоей ссылке зарегистрировался друг! Ты получил +1 билет. Всего билетов: <b>{count}</b>.",
        'ref_success': "🔥 <b>Ты пригласил 3 друзей!</b> Твой доступ к сигналам открыт навсегда. Но не останавливайся, на кону денежные призы!"
    },
    'en': {
        'welcome': "🔥 <b>SECRET ALGORITHM ACCESS GRANTED</b> 🔥\n\nWelcome to <b>MINES AI PREDICTOR</b>!\n\n😤 Tired of losing deposits? Stop feeding the casino. It's time to take yours.\n\n🧠 Our neural network scans Mines patterns and calculates safe cells with <b>up to 85% accuracy</b>.\n\n🚀 <b>Start earning right now!</b> 👇",
        'btn_reg': "💳 Register", 'btn_instr': "📖 Instruction", 'btn_sign': "🔮 Get Signal", 'btn_lang': "🌐 Language", 'btn_ref': "👥 Contest & Refs", 'btn_support': "🆘 Support",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Language changed to English 🇬🇧",
        'need_reg': "⚠️ <b>ACCESS BLOCKED!</b>\n\nAI algorithm requires a 1win account link.\n\n👇 Register in 1 click below to unlock:\n\n<i>Or participate in the contest using the “👥 Contest & Refs” button!</i>",
        'regged': "✅ <b>SUCCESS!</b> Account linked. Neural network activated. Click 'Get Signal'! 🚀",
        'choose_traps': "⚙️ <b>Risk Configuration</b>\n\nChoose the number of traps:",
        'btn_trap_1': "🟢 1 trap", 'btn_trap_3': "🟡 3 traps", 'btn_trap_5': "🔴 5 traps",
        'btn_main': "⬅️ Main Menu",
        'signal_title': "🔮 <b>Analysis Complete!</b>\nConfiguration: <b>{traps} traps</b>\n\n",
        'signal_hint': "\n🎯 <b>Recommended cells:</b> <code>{cells}</code>\n\n{left}🔥 <i>Good luck! Double bet on loss.</i>",
        'left_signals': "💡 <i>Signals left today: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>DAILY LIMIT REACHED!</b>\n\nYou have used all {limit} signals for today. The neural network needs time to calibrate.\n\n👇 <b>Want more?</b> Invite a friend via '👥 Contest & Refs' to get bonus attempts!",
        'instr_text': "📖 <b>HOW TO START:</b>\n\n1️⃣ <b>Register:</b> <a href='{url}'>CLICK HERE</a>\n2️⃣ <b>Deposit:</b> Top up.\n3️⃣ <b>Game:</b> Go to <b>Mines</b>.\n4️⃣ <b>Setup:</b> Set traps by signal.\n5️⃣ <b>Action:</b> Open cells.\n6️⃣ <b>Insurance:</b> Double bet on loss.",
        'admin_panel': "⚙️ Admin panel. Command /top - leaderboard.", 'not_admin': "❌ You don't have admin rights.",
        'support_text': "🆘 <b>Support</b>\n\nContact our manager:\n\n👉 <a href='tg://user?id={admin_id}'>Message Admin</a>",
        'ref_title': "🏆 <b>PRIZE POOL CONTEST</b> 🏆\n\nInvite friends and earn tickets! <b>1 registered friend = 1 ticket.</b>\n\n🥇 <b>1st:</b> $100\n🥈 <b>2nd:</b> $50\n🥉 <b>3rd:</b> $20\n\n📊 Tickets: <b>{count}</b>\n\n🔗 Link:\n<code>{link}</code>",
        'ref_notify': "🎉 Friend registered! +1 ticket. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>3 friends invited!</b> Access is open forever. Don't stop, cash prizes await!"
    },
    'es': {
        'welcome': "🔥 <b>ACCESO AL ALGORITMO SECRETO</b> 🔥\n\n¡Bienvenido a <b>MINES AI PREDICTOR</b>!\n\n😤 ¿Cansado de perder? Deja de alimentar al casino.\n\n🧠 Nuestra red neuronal calcula celdas seguras con <b>hasta un 85% de precisión</b>.\n\n🚀 <b>¡Empieza a ganar ahora!</b> 👇",
        'btn_reg': "💳 Registrarse", 'btn_instr': "📖 Instrucción", 'btn_sign': "🔮 Obtener señal", 'btn_lang': "🌐 Idioma", 'btn_ref': "👥 Concurso y Refs", 'btn_support': "🆘 Soporte",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma cambiado a Español 🇪🇸",
        'need_reg': "⚠️ <b>¡ACCESO BLOQUEADO!</b>\n\nVincula tu cuenta de 1win.\n\n👇 Regístrate abajo:",
        'regged': "✅ <b>¡ÉXITO!</b> Cuenta vinculada. 🚀",
        'choose_traps': "⚙️ <b>Configuración de riesgo</b>\n\nElige trampas:",
        'btn_trap_1': "🟢 1 trampa", 'btn_trap_3': "🟡 3 trampas", 'btn_trap_5': "🔴 5 trampas",
        'btn_main': "⬅️ Menú Principal",
        'signal_title': "🔮 <b>¡Análisis completado!</b>\nTrampas: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Celdas recomendadas:</b> <code>{cells}</code>\n\n{left}🔥 <i>¡Buena suerte!</i>",
        'left_signals': "💡 <i>Señales restantes hoy: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>¡LÍMITE DIARIO ALCANZADO!</b>\n\nHas usado las {limit} señales de hoy. ¡Invita a un amigo para obtener intentos extra!",
        'instr_text': "📖 <b>CÓMO EMPEZAR:</b>\n\n1️⃣ <b>Registro:</b> <a href='{url}'>HAZ CLIC AQUÍ</a>\n2️⃣ <b>Depósito:</b> Recarga.\n3️⃣ <b>Juego:</b> Ve a <b>Mines</b>.\n4️⃣ <b>Configuración:</b> Pon las trampas.\n5️⃣ <b>Acción:</b> Abre las celdas.\n6️⃣ <b>Seguro:</b> Dobla al perder.",
        'admin_panel': "⚙️ Panel de admin. Comando /top.", 'not_admin': "❌ No eres admin.",
        'support_text': "🆘 <b>Soporte</b>\n\n👉 <a href='tg://user?id={admin_id}'>Mensaje al Admin</a>",
        'ref_title': "🏆 <b>CONCURSO CON PREMIOS</b> 🏆\n\n¡Invita amigos y gana boletos! <b>1 amigo = 1 boleto.</b>\n\n🥇 <b>1er lugar:</b> $100\n🥈 <b>2do:</b> $50\n🥉 <b>3er:</b> $20\n\n📊 Boletos: <b>{count}</b>\n\n🔗 Enlace:\n<code>{link}</code>",
        'ref_notify': "🎉 ¡Un amigo se registró! +1 boleto. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>¡Invitaste a 3 amigos!</b> Acceso abierto para siempre."
    },
    'pt': {
        'welcome': "🔥 <b>ACESSO AO ALGORITMO SECRETO</b> 🔥\n\nBem-vindo ao <b>MINES AI PREDICTOR</b>!\n\n😤 Cansado de perder? Pare de alimentar o cassino.\n\n🧠 Nossa rede neural calcula células seguras com <b>até 85% de precisão</b>.\n\n🚀 <b>Comece a ganhar agora!</b> 👇",
        'btn_reg': "💳 Registre-se", 'btn_instr': "📖 Instrução", 'btn_sign': "🔮 Obter sinal", 'btn_lang': "🌐 Idioma", 'btn_ref': "👥 Concurso e Refs", 'btn_support': "🆘 Suporte",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "Idioma alterado para Português 🇵🇹",
        'need_reg': "⚠️ <b>ACESSO BLOQUEADO!</b>\n\nVincule sua conta 1win.\n\n👇 Registre-se abaixo:",
        'regged': "✅ <b>SUCESSO!</b> Conta vinculada. 🚀",
        'choose_traps': "⚙️ <b>Configuração de risco</b>\n\nEscolha armadilhas:",
        'btn_trap_1': "🟢 1 armadilha", 'btn_trap_3': "🟡 3 armadilhas", 'btn_trap_5': "🔴 5 armadilhas",
        'btn_main': "⬅️ Menu Principal",
        'signal_title': "🔮 <b>Análise concluída!</b>\nArmadilhas: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>Células recomendadas:</b> <code>{cells}</code>\n\n{left}🔥 <i>Boa sorte!</i>",
        'left_signals': "💡 <i>Sinais restantes hoje: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>LIMITE DIÁRIO ATINGIDO!</b>\n\nVocê usou todos os {limit} sinais de hoje. Convide um amigo para tentativas extras!",
        'instr_text': "📖 <b>COMO COMEÇAR:</b>\n\n1️⃣ <b>Registro:</b> <a href='{url}'>CLIQUE AQUI</a>\n2️⃣ <b>Depósito:</b> Recarregue.\n3️⃣ <b>Jogo:</b> Vá para <b>Mines</b>.\n4️⃣ <b>Configuração:</b> Defina as armadilhas.\n5️⃣ <b>Ação:</b> Abra as células.\n6️⃣ <b>Seguro:</b> Dobre na perda.",
        'admin_panel': "⚙️ Painel de admin. Comando /top.", 'not_admin': "❌ Você não é admin.",
        'support_text': "🆘 <b>Suporte</b>\n\n👉 <a href='tg://user?id={admin_id}'>Mensagem para o Admin</a>",
        'ref_title': "🏆 <b>CONCURSO COM PRÊMIOS</b> 🏆\n\nConvide amigos e ganhe bilhetes! <b>1 amigo = 1 bilhete.</b>\n\n🥇 <b>1º:</b> $100\n🥈 <b>2º:</b> $50\n🥉 <b>3º:</b> $20\n\n📊 Bilhetes: <b>{count}</b>\n\n🔗 Link:\n<code>{link}</code>",
        'ref_notify': "🎉 Um amigo se registrou! +1 bilhete. Total: <b>{count}</b>.",
        'ref_success': "🔥 <b>Você convidou 3 amigos!</b> Acesso aberto para sempre."
    },
    'hi': {
        'welcome': "🔥 <b>गुप्त एल्गोरिथम तक पहुंच</b> 🔥\n\n<b>MINES AI PREDICTOR</b> में आपका स्वागत है!\n\n😤 खोने से थक गए? कैसीनो को खिलाना बंद करें।\n\n🧠 हमारा न्यूरल नेटवर्क <b>85% तक सटीकता</b> के साथ सुरक्षित सेल की गणना करता है।\n\n🚀 <b>अभी कमाना शुरू करें!</b> 👇",
        'btn_reg': "💳 पंजीकरण", 'btn_instr': "📖 निर्देश", 'btn_sign': "🔮 सिग्नल प्राप्त करें", 'btn_lang': "🌐 भाषा", 'btn_ref': "👥 प्रतियोगिता और रेफरल", 'btn_support': "🆘 सहायता",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "भाषा हिंदी में बदल गई 🇮🇳",
        'need_reg': "⚠️ <b>पहुंच अवरुद्ध!</b>\n\n1win खाता लिंक करें।\n\n👇 नीचे पंजीकरण करें:",
        'regged': "✅ <b>सफलता!</b> खाता लिंक हो गया। 🚀",
        'choose_traps': "⚙️ <b>जोखिम कॉन्फ़िगरेशन</b>\n\nजाल चुनें:",
        'btn_trap_1': "🟢 1 जाल", 'btn_trap_3': "🟡 3 जाल", 'btn_trap_5': "🔴 5 जाल",
        'btn_main': "⬅️ मुख्य मेनू",
        'signal_title': "🔮 <b>विश्लेषण पूरा!</b>\nजाल: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>अनुशंसित सेल:</b> <code>{cells}</code>\n\n{left}🔥 <i>शुभकामनाएं!</i>",
        'left_signals': "💡 <i>आज बचे सिग्नल: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>दैनिक सीमा समाप्त!</b>\n\nआपने आज के सभी {limit} सिग्नल का उपयोग कर लिया है। बोनस के लिए दोस्त को आमंत्रित करें!",
        'instr_text': "📖 <b>कैसे शुरू करें:</b>\n\n1️⃣ <b>पंजीकरण:</b> <a href='{url}'>यहाँ क्लिक करें</a>\n2️⃣ <b>जमा:</b> टॉप अप करें।\n3️⃣ <b>गेम:</b> <b>Mines</b> पर जाएं।\n4️⃣ <b>सेटअप:</b> जाल सेट करें।\n5️⃣ <b>कार्रवाई:</b> सेल खोलें।\n6️⃣ <b>बीमा:</b> हार पर दोगुना करें।",
        'admin_panel': "⚙️ एडमिन पैनल। कमांड /top।", 'not_admin': "❌ आप एडमिन नहीं हैं।",
        'support_text': "🆘 <b>सहायता</b>\n\n👉 <a href='tg://user?id={admin_id}'>एडमिन को संदेश भेजें</a>",
        'ref_title': "🏆 <b>पुरस्कार प्रतियोगिता</b> 🏆\n\nदोस्तों को आमंत्रित करें! <b>1 दोस्त = 1 टिकट।</b>\n\n🥇 <b>1st:</b> $100\n🥈 <b>2nd:</b> $50\n🥉 <b>3rd:</b> $20\n\n📊 टिकट: <b>{count}</b>\n\n🔗 लिंक:\n<code>{link}</code>",
        'ref_notify': "🎉 एक दोस्त पंजीकृत हुआ! +1 टिकट। कुल: <b>{count}</b>।",
        'ref_success': "🔥 <b>आपने 3 दोस्तों को आमंत्रित किया!</b> पहुंच हमेशा के लिए खुली है।"
    },
    'ar': {
        'welcome': "🔥 <b>تم منح الوصول إلى الخوارزمية السرية</b> 🔥\n\nمرحبًا بك في <b>MINES AI PREDICTOR</b>!\n\n😤 سئمت من الخسارة؟ توقف عن إطعام الكازينو.\n\n🧠 شبكتنا العصبية تحسب الخلايا الآمنة بدقة <b>تصل إلى 85٪</b>.\n\n🚀 <b>ابدأ الكسب الآن!</b> 👇",
        'btn_reg': "💳 التسجيل", 'btn_instr': "📖 تعليمات", 'btn_sign': "🔮 الحصول على إشارة", 'btn_lang': "🌐 اللغة", 'btn_ref': "👥 المسابقة والإحالات", 'btn_support': "🆘 الدعم",
        'choose_lang': "🌐 Выберите язык / Choose language:",
        'lang_set': "تم تغيير اللغة إلى العربية 🇸🇦",
        'need_reg': "⚠️ <b>تم حظر الوصول!</b>\n\nاربط حسابك في 1win.\n\n👇 سجل أدناه:",
        'regged': "✅ <b>نجاح!</b> تم ربط الحساب. 🚀",
        'choose_traps': "⚙️ <b>تكوين المخاطر</b>\n\nاختر الفخاخ:",
        'btn_trap_1': "🟢 فخ واحد", 'btn_trap_3': "🟡 3 فخاخ", 'btn_trap_5': "🔴 5 فخاخ",
        'btn_main': "⬅️ القائمة الرئيسية",
        'signal_title': "🔮 <b>اكتمل التحليل!</b>\nالفخاخ: <b>{traps}</b>\n\n",
        'signal_hint': "\n🎯 <b>الخلايا الموصى بها:</b> <code>{cells}</code>\n\n{left}🔥 <i>حظا سعيدا!</i>",
        'left_signals': "💡 <i>الإشارات المتبقية اليوم: {left}</i>\n\n",
        'limit_msg': "⚠️ <b>تم الوصول إلى الحد اليومي!</b>\n\nلقد استخدمت جميع الإشارات الـ {limit} لهذا اليوم. ادعو صديقًا للحصول على محاولات إضافية!",
        'instr_text': "📖 <b>كيف تبدأ:</b>\n\n1️⃣ <b>التسجيل:</b> <a href='{url}'>انقر هنا</a>\n2️⃣ <b>إيداع:</b> اشحن رصيدك.\n3️⃣ <b>اللعبة:</b> انتقل إلى <b>Mines</b>.\n4️⃣ <b>الإعداد:</b> اضبط الفخاخ.\n5️⃣ <b>الإجراء:</b> افتح الخلايا.\n6️⃣ <b>التأمين:</b> ضاعف عند الخسارة.",
        'admin_panel': "⚙️ لوحة المسؤول. الأمر /top.", 'not_admin': "❌ ليس لديك حقوق المسؤول.",
        'support_text': "🆘 <b>الدعم</b>\n\n👉 <a href='tg://user?id={admin_id}'>مراسلة المسؤول</a>",
        'ref_title': "🏆 <b>مسابقة جوائز</b> 🏆\n\nادعو الأصدقاء! <b>صديق = تذكرة.</b>\n\n🥇 <b>1:</b> $100\n🥈 <b>2:</b> $50\n🥉 <b>3:</b> $20\n\n📊 تذاكرك: <b>{count}</b>\n\n🔗 رابطك:\n<code>{link}</code>",
        'ref_notify': "🎉 سجل صديق! +1 تذكرة. الإجمالي: <b>{count}</b>.",
        'ref_success': "🔥 <b>لقد دعوت 3 أصدقاء!</b> وصولك مفتوح للأبد."
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
                referrer_id INTEGER,
                daily_signals INTEGER DEFAULT 0,
                last_signal_date TEXT
            )
        """)
        conn.commit()
        
        # Миграции для старых баз данных
        columns = [
            ("language", "TEXT DEFAULT 'ru'"),
            ("referrer_id", "INTEGER"),
            ("daily_signals", "INTEGER DEFAULT 0"),
            ("last_signal_date", "TEXT")
        ]
        for col, typ in columns:
            try:
                conn.execute(f"ALTER TABLE user ADD COLUMN {col} {typ}")
            except sqlite3.OperationalError:
                pass

def get_user(uid: int):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT postback_id, language, referrer_id, daily_signals, last_signal_date 
            FROM user WHERE user_id = ?
        """, (uid,)).fetchone()
        
        if row:
            lang = row[1] if row[1] in LANG else 'ru'
            ref_count = conn.execute(
                "SELECT COUNT(*) FROM user WHERE referrer_id = ? AND postback_id IS NOT NULL", 
                (uid,)
            ).fetchone()[0]
            return {
                "postback_id": row[0], 
                "lang": lang, 
                "referrer_id": row[2], 
                "ref_count": ref_count,
                "daily_signals": row[3] or 0,
                "last_signal_date": row[4]
            }
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

def generate_mines_grid(lang, traps=3, signals_left=0):
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
    
    if signals_left > 0:
        left_text = LANG[lang]['left_signals'].format(left=signals_left)
    else:
        left_text = ""
        
    return title + f"<code>{grid_text}</code>" + LANG[lang]['signal_hint'].format(cells=recommended, left=left_text)

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
    await bot.edit_message_text(text=text, chat_id=call.from_user.id, message_id=call.message.message_id, reply_markup=kb, disable_web_page_preview=True)
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
    await bot.edit_message_text(text=text, chat_id=uid, message_id=call.message.message_id, reply_markup=kb, disable_web_page_preview=True)
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
    
    # Проверка доступа
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
    
    # --- ПРОВЕРКА ДНЕВНОГО ЛИМИТА ---
    today = datetime.date.today().isoformat()
    daily_signals = user['daily_signals']
    
    # Если дата сменилась, сбрасываем счетчик
    if user['last_signal_date'] != today:
        daily_signals = 0
        
    if daily_signals >= DAILY_LIMIT:
        # Лимит исчерпан
        await bot.answer_callback_query(call.id, "⚠️ Лимит на сегодня исчерпан!", show_alert=True)
        await bot.send_message(uid, LANG[lang]['limit_msg'].format(limit=DAILY_LIMIT))
        return
        
    # Увеличиваем счетчик и обновляем дату
    daily_signals += 1
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE user SET daily_signals = ?, last_signal_date = ? WHERE user_id = ?", 
            (daily_signals, today, uid)
        )
        conn.commit()
    
    signals_left = DAILY_LIMIT - daily_signals
    
    # Генерация сигнала
    traps = int(call.data.split("_")[-1])
    signal_text = generate_mines_grid(lang, traps, signals_left)
    
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
async def on_startup(dp):
    # Устанавливаем красивую кнопку "Меню" слева внизу
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="Start"))

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_web, daemon=True).start()
    log.info("Bot starting...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)