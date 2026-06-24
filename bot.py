import telebot
import re
import os
import time
import json
import logging
import random
import threading
from datetime import datetime, timedelta
from telebot import types
from telebot.apihelper import ApiTelegramException

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1364254252
ADMIN_PASSWORD = "08091913"

if not BOT_TOKEN:
    raise ValueError("Нет токена")

# ============================================================
# НАСТРОЙКИ
# ============================================================
REQUEST_DELAY = 0.5
MAX_RETRIES = 5
RETRY_DELAY = 1
VERIFICATION_TIMEOUT = 120
VERIFICATION_ATTEMPTS = 3
MESSAGE_DELETE_SECONDS = 30

# ============================================================
# 25 РАЗНЫХ ПРИМЕРОВ ДЛЯ ВЕРИФИКАЦИИ
# ============================================================
VERIFICATION_QUESTIONS = [
    {"question": "Сколько будет 7 + 3?", "answer": 10},
    {"question": "Сколько будет 12 - 5?", "answer": 7},
    {"question": "Сколько будет 4 * 6?", "answer": 24},
    {"question": "Сколько будет 15 + 8?", "answer": 23},
    {"question": "Сколько будет 20 - 7?", "answer": 13},
    {"question": "Сколько будет 3 * 9?", "answer": 27},
    {"question": "Сколько будет 14 + 6?", "answer": 20},
    {"question": "Сколько будет 25 - 10?", "answer": 15},
    {"question": "Сколько будет 5 * 8?", "answer": 40},
    {"question": "Сколько будет 11 + 9?", "answer": 20},
    {"question": "Сколько будет 18 - 6?", "answer": 12},
    {"question": "Сколько будет 7 * 7?", "answer": 49},
    {"question": "Сколько будет 23 + 7?", "answer": 30},
    {"question": "Сколько будет 30 - 12?", "answer": 18},
    {"question": "Сколько будет 6 * 6?", "answer": 36},
    {"question": "Сколько будет 9 + 8?", "answer": 17},
    {"question": "Сколько будет 22 - 9?", "answer": 13},
    {"question": "Сколько будет 8 * 5?", "answer": 40},
    {"question": "Сколько будет 16 + 14?", "answer": 30},
    {"question": "Сколько будет 35 - 8?", "answer": 27},
    {"question": "Сколько будет 4 * 9?", "answer": 36},
    {"question": "Сколько будет 13 + 7?", "answer": 20},
    {"question": "Сколько будет 28 - 9?", "answer": 19},
    {"question": "Сколько будет 6 * 8?", "answer": 48},
    {"question": "Сколько будет 19 + 11?", "answer": 30},
]

# ============================================================
# ТЕКСТ ПРИВЕТСТВИЯ
# ============================================================
WELCOME_MESSAGE_TEMPLATE = """
🌟 Добро пожаловать в Вейп-Барахолку Краснодара, {user_mention}! 🎉

📋 <b>Правила чата:</b>
🚫 Запрещено:
• ❌ Не вейп-тематика
• ❌ Оскорбления и флуд
• ❌ Спам и реклама

⚠️ <b>Внимание!</b>
При скаме: @callumom 
Администрация не отвечает за сделки.

🏪 <b>Лучшие вейп-шопы:</b>
• 🔥 Mix Vape: https://t.me/mixvape1
• 💨 Vape Shop: https://t.me/vapeshop

💫 Приятного общения!
"""

WELCOME_STARS = ["✨", "🌟", "⭐", "💫", "🔥", "❤️"]

# ============================================================
# ЗАПРЕЩЁННЫЕ СЛОВА (ПОЛНЫЙ СПИСОК)
# ============================================================
FORBIDDEN_WORDS = [
    "подработка", "заработок", "заработать", "заработнаяплата",
    "удаленнаяработа", "удаленка", "работавинтернете", "работаонлайн",
    "вакансия", "дополнительныйдоход", "свободныйграфик", "легкиеденьги",
    "доходбезвложений", "пассивныйдоход", "работанадому", "заработокбезопыта",
    "ищулюдей", "ищусотрудника", "ищучеловека", "ищуработника",
    "ищукандидата", "ищудевушку", "ищупарня", "ищупомощника",
    "ищуассистента", "требуютсясотрудники", "требуетсясотрудник",
    "набираемсотрудников", "наборсотрудников", "открытавакансия",
    "приглашаювкоманду", "ищемлюдей", "ищемсотрудников", "ищемработников",
    "вакансияоткрыта", "заработнаяплатавысокая", "отдатьбесплатно",
    "отдамбесплатно", "отдатьбесплатнозарефку", "реф", "рефка", "альфа",
    "дельце", "трудоустройство", "кешвышеобычного", "обучениенаместе",
    "ищутолковыхребят", "пкклуб", "пацаныотлет", "пацаныотл",
    "оплатасразу", "работанесложная", "новичковберём", "выплатимчестно",
    "требуетсяпомощь", "естьтемазароботка", "еслиинтерестнопиши",
    "зарефкуальфы", "прибыльнаяшабашка", "можносовмещатьсучебой",
    "скупаюголду", "хорошемукурсу", "беруваренду", "дамподработку",
    "бросаюкурить", "плачуот", "вкомпьютерныйклуб", "быстрыеденьги",
    "легкийкуш", "арендасим", "куплюакк", "арендааккаунта",
    "арбитраж", "биржа", "быстрыйвыхлоп", "доходность", "крипта",
    "пассивныйзаработок", "ищемпарней", "ищемчеловека",
    "винтернетмагазин", "ищемребят", "возьмуваренду",
    "скуплюпушкинскиекарты", "баллыпушкинскойкарты"
]

# ============================================================
# ХРАНИЛИЩЕ ДАННЫХ
# ============================================================
authorized_users = {ADMIN_ID: True}
verification_data = {}
user_stats = {}
chat_stats = {}
restricted_users = {}
verified_users = {}
all_bot_messages = {}
last_request_time = 0
request_lock = threading.Lock()

# ============================================================
# ЛОГИРОВАНИЕ
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# БОТ
# ============================================================
bot = telebot.TeleBot(BOT_TOKEN)

# ============================================================
# ⚠️ ЕДИНСТВЕННАЯ ФУНКЦИЯ ДЛЯ ОТПРАВКИ - БЕЗ HTML!
# ============================================================
def send_msg(chat_id, text, **kwargs):
    """Единственная функция для отправки. БЕЗ HTML."""
    try:
        if 'parse_mode' in kwargs:
            del kwargs['parse_mode']
        return bot.send_message(chat_id, text, **kwargs)
    except ApiTelegramException as e:
        if "can't parse entities" in str(e):
            clean = text.replace('<', '').replace('>', '').replace('&', '')
            return bot.send_message(chat_id, clean, **kwargs)
        raise
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return None

def safe_api_call(func, *args, **kwargs):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            time.sleep(REQUEST_DELAY)
            return func(*args, **kwargs)
        except ApiTelegramException as e:
            error_code = getattr(e, 'error_code', 0)
            if error_code == 429:
                retry_after = 5
                if "retry after" in str(e):
                    try:
                        retry_after = int(str(e).split("retry after")[1].split()[0])
                    except:
                        pass
                time.sleep(retry_after + 1)
                retries += 1
                continue
            elif error_code == 502:
                time.sleep((retries + 1) * 5)
                retries += 1
                continue
            else:
                return None
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            if retries < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (retries + 1))
                retries += 1
            else:
                return None
    return None

def delete_msg(chat_id, message_id):
    try:
        safe_api_call(bot.delete_message, chat_id, message_id)
    except:
        pass

def send_and_delete(chat_id, text, delay=MESSAGE_DELETE_SECONDS, **kwargs):
    sent = send_msg(chat_id, text, **kwargs)
    if sent:
        timer = threading.Timer(delay, delete_msg, args=[chat_id, sent.message_id])
        timer.daemon = True
        timer.start()
    return sent

# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def admin_keyboard():
    """Клавиатура для админов"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton("📊 Статистика"),
        types.KeyboardButton("📝 Список слов"),
        types.KeyboardButton("👥 Админы"),
        types.KeyboardButton("🔐 Верификация"),
        types.KeyboardButton("📋 Помощь"),
        types.KeyboardButton("ℹ️ Статус")
    ]
    keyboard.add(*buttons)
    return keyboard

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def is_verified(user_id, chat_id):
    return user_id in verified_users and chat_id in verified_users.get(user_id, [])

def mark_verified(user_id, chat_id):
    if user_id not in verified_users:
        verified_users[user_id] = []
    if chat_id not in verified_users[user_id]:
        verified_users[user_id].append(chat_id)

def update_stats(user_id, chat_id, stat_type):
    current_date = datetime.now().strftime("%Y-%m-%d")
    if user_id not in user_stats:
        user_stats[user_id] = {'messages': 0, 'joins': 0, 'verifications': 0}
    user_stats[user_id][stat_type] = user_stats[user_id].get(stat_type, 0) + 1
    if chat_id not in chat_stats:
        chat_stats[chat_id] = {
            'messages': 0, 'joins': 0, 'verifications': 0,
            'daily': {'date': current_date, 'joins': 0, 'messages': 0}
        }
    chat_stats[chat_id][stat_type] = chat_stats[chat_id].get(stat_type, 0) + 1
    if chat_stats[chat_id]['daily']['date'] != current_date:
        chat_stats[chat_id]['daily'] = {'date': current_date, 'joins': 0, 'messages': 0}
    if stat_type == 'joins':
        chat_stats[chat_id]['daily']['joins'] += 1
    elif stat_type == 'messages':
        chat_stats[chat_id]['daily']['messages'] += 1

def get_question():
    return random.choice(VERIFICATION_QUESTIONS)

def get_stars():
    return random.choice(WELCOME_STARS)

def clean_text(text):
    if not text:
        return ""
    text = text.lower().replace(" ", "")
    replacements = {
        '@': 'а', '4': 'ч', '0': 'о', '3': 'з',
        'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р',
        'c': 'с', 'y': 'у', 'k': 'к', 'x': 'х',
        'b': 'ь', 'm': 'м', 'n': 'н', 't': 'т',
        'h': 'н', 'r': 'г'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r'[^а-яё]', '', text)

def has_forbidden_words(text):
    cleaned = clean_text(text)
    return any(word in cleaned for word in FORBIDDEN_WORDS)

# ============================================================
# ОСНОВНАЯ ЛОГИКА
# ============================================================
def send_verification(chat_id, user_id, user_name, first_name, is_rejoin=False):
    try:
        q = get_question()
        mention = f"@{user_name}" if user_name else first_name
        title = "🔄 Повторная верификация" if is_rejoin else "🔐 Верификация нового пользователя"
        
        text = f"""{title}

👤 {mention}

🧮 Для подтверждения, что вы не робот, решите пример:

<b>❓ {q['question']}</b>

⏳ У вас {VERIFICATION_TIMEOUT//60} минут(ы) и {VERIFICATION_ATTEMPTS} попытки.

💡 Напишите ответ в чат (только число)"""
        
        verification_data[user_id] = {
            'chat_id': chat_id,
            'question': q['question'],
            'answer': q['answer'],
            'attempts': 0,
            'timestamp': time.time(),
            'message_ids': []
        }
        
        sent = send_msg(chat_id, text)
        if sent:
            verification_data[user_id]['message_ids'].append(sent.message_id)
        
        if not is_rejoin:
            update_stats(user_id, chat_id, 'joins')
        
        admin_text = f"""👤 {title}
├ 🆔 ID: {user_id}
├ 📛 Имя: {first_name}
├ 🔗 Юзернейм: @{user_name if user_name else "отсутствует"}
├ 💬 Чат: {chat_id}
├ ❓ Вопрос: {q['question']}
└ 🕐 Время: {datetime.now().strftime("%H:%M:%S")}"""
        send_msg(ADMIN_ID, admin_text)
        
        try:
            send_msg(user_id, f"""🔐 В группе задан вопрос для верификации:

❓ {q['question']}

⏳ У вас {VERIFICATION_TIMEOUT//60} минут(ы)

📝 Напишите ответ в чат!""")
        except:
            pass
        
        timer = threading.Timer(VERIFICATION_TIMEOUT, restrict_user, args=[chat_id, user_id])
        timer.daemon = True
        timer.start()
        
    except Exception as e:
        logger.error(f"Ошибка верификации: {e}")

def send_welcome(chat_id, user_id, user_name, first_name):
    try:
        mention = f"@{user_name}" if user_name else first_name
        text = WELCOME_MESSAGE_TEMPLATE.format(stars=get_stars(), user_mention=mention)
        send_and_delete(chat_id, text, delay=MESSAGE_DELETE_SECONDS)
        update_stats(user_id, chat_id, 'verifications')
        mark_verified(user_id, chat_id)
        send_msg(ADMIN_ID, f"✅ Пользователь {user_id} успешно верифицирован в чате {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка приветствия: {e}")

def verify_user(chat_id, user_id, message_id, answer_text):
    if user_id not in verification_data:
        return False, "❌ Вы не на верификации"
    
    data = verification_data[user_id]
    
    if time.time() - data['timestamp'] > VERIFICATION_TIMEOUT:
        del verification_data[user_id]
        return False, "⏰ Время верификации истекло"
    
    if data['attempts'] >= VERIFICATION_ATTEMPTS:
        del verification_data[user_id]
        return False, "❌ Попытки исчерпаны"
    
    try:
        user_answer = int(answer_text.strip())
    except ValueError:
        return False, "⚠️ Пожалуйста, введите число"
    
    delete_msg(chat_id, message_id)
    
    if user_answer == data['answer']:
        for msg_id in data['message_ids']:
            delete_msg(chat_id, msg_id)
        del verification_data[user_id]
        
        send_and_delete(chat_id, "✅ Вы успешно прошли верификацию! Добро пожаловать! 🎉", delay=MESSAGE_DELETE_SECONDS)
        
        user = safe_api_call(bot.get_chat_member, chat_id, user_id)
        if user:
            send_welcome(chat_id, user_id, user.user.username, user.user.first_name)
        return True, "✅ Верификация успешна!"
    else:
        data['attempts'] += 1
        remaining = VERIFICATION_ATTEMPTS - data['attempts']
        if remaining > 0:
            err = send_and_delete(chat_id, f"❌ Неправильно. Осталось попыток: {remaining}", delay=MESSAGE_DELETE_SECONDS)
            if err:
                data['message_ids'].append(err.message_id)
        else:
            for msg_id in data['message_ids']:
                delete_msg(chat_id, msg_id)
            del verification_data[user_id]
            restrict_user(chat_id, user_id)
        return False, f"❌ Осталось попыток: {remaining}"

def restrict_user(chat_id, user_id):
    """Ограничивает пользователя (запрещает отправлять сообщения)"""
    if user_id in verification_data:
        for msg_id in verification_data[user_id]['message_ids']:
            delete_msg(chat_id, msg_id)
        del verification_data[user_id]
    
    try:
        # Используем ChatPermissions для ограничения
        permissions = types.ChatPermissions(
            can_send_messages=False,
            can_send_media=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_send_polls=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        safe_api_call(bot.restrict_chat_member, chat_id, user_id, permissions)
        
        restricted_users[user_id] = {'chat_id': chat_id, 'timestamp': time.time()}
        send_and_delete(chat_id, "⛔ Пользователь не прошел верификацию и ограничен.", delay=MESSAGE_DELETE_SECONDS)
        send_msg(ADMIN_ID, f"⛔ Пользователь {user_id} ограничен в чате {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка ограничения: {e}")

def send_ban_log(chat_id, user_id, username, first_name, text):
    link = f"@{username}" if username else f"ID: {user_id}"
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    log = f"""🚫 <b>Забанен спамер!</b>

🆔 ID: {user_id}
📛 Имя: {first_name or "Без имени"}
🔗 Ссылка: {link}
💬 Чат: {chat_id}
📝 Текст: {text}
🕐 Время: {now}"""
    send_msg(ADMIN_ID, log)

# ============================================================
# ОБРАБОТЧИКИ СООБЩЕНИЙ
# ============================================================
@bot.message_handler(content_types=['new_chat_members'], chat_types=['group', 'supergroup'])
def new_member_handler(message):
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        if not is_verified(member.id, message.chat.id):
            send_verification(
                message.chat.id, 
                member.id, 
                member.username, 
                member.first_name or "Пользователь",
                is_rejoin=False
            )

@bot.message_handler(content_types=['text'], chat_types=['group', 'supergroup'])
def group_message_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text or ""
    
    if text.startswith('/'):
        return
    
    if is_verified(user_id, chat_id) and user_id not in restricted_users:
        update_stats(user_id, chat_id, 'messages')
    
    if user_id in verification_data:
        verify_user(chat_id, user_id, message.message_id, text)
        return
    
    if user_id in restricted_users:
        delete_msg(chat_id, message.message_id)
        send_and_delete(chat_id, f"⛔ {message.from_user.first_name}, вы ограничены. Обратитесь к администратору.", delay=MESSAGE_DELETE_SECONDS)
        return
    
    if not is_verified(user_id, chat_id):
        user = safe_api_call(bot.get_chat_member, chat_id, user_id)
        if user:
            send_verification(chat_id, user_id, user.user.username, user.user.first_name, is_rejoin=True)
        delete_msg(chat_id, message.message_id)
        return
    
    if has_forbidden_words(text):
        delete_msg(chat_id, message.message_id)
        safe_api_call(bot.ban_chat_member, chat_id, user_id)
        send_ban_log(chat_id, user_id, message.from_user.username, message.from_user.first_name, text)

# ============================================================
# КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['start'], chat_types=['private'])
def start_cmd(message):
    user_id = message.from_user.id
    
    if user_id in authorized_users:
        welcome_text = """🌟 <b>Добро пожаловать в админ-панель!</b>

👋 Привет, администратор! Я готов к работе.

📋 <b>Доступные команды:</b>

🔐 <b>Верификация:</b>
/verify - начать верификацию для себя
/verify_user <id> - верификация пользователя
/verify_manual <id> - ручная верификация
/unrestrict <id> - снять ограничение

📊 <b>Статистика:</b>
/stats - статистика чата
/stats_all - статистика всех чатов
/send_stats - отправить дневную статистику
/status - статус бота

👥 <b>Управление:</b>
/add_admin <пароль> <id> - добавить админа
/remove_admin <id> - удалить админа
/list_admins - список админов

📝 <b>Фильтр слов:</b>
/add_word <слово> - добавить слово
/remove_word <слово> - удалить слово
/list_words - список слов

⚙️ <b>Настройки:</b>
/set_delete_time <сек> - время удаления сообщений

💡 <b>Совет:</b> Используйте кнопки ниже для быстрого доступа!"""
        
        send_msg(user_id, welcome_text, reply_markup=admin_keyboard())
    else:
        send_msg(user_id, """🔐 <b>Требуется авторизация</b>

Для доступа к админ-панели введите пароль.

ℹ️ Пароль был установлен при настройке бота.""")
        send_msg(user_id, "🔑 Введите пароль:")

@bot.message_handler(commands=['help'], chat_types=['private'])
def help_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    
    help_text = """📋 <b>Помощь по командам</b>

🔐 <b>Верификация:</b>
/verify - начать верификацию для себя
/verify_user <id> - верификация пользователя
/verify_manual <id> - ручная верификация
/unrestrict <id> - снять ограничение

📊 <b>Статистика:</b>
/stats - статистика чата
/stats_all - статистика всех чатов
/send_stats - отправить дневную статистику
/status - статус бота

👥 <b>Управление:</b>
/add_admin <пароль> <id> - добавить админа
/remove_admin <id> - удалить админа
/list_admins - список админов

📝 <b>Фильтр слов:</b>
/add_word <слово> - добавить слово
/remove_word <слово> - удалить слово
/list_words - список слов

⚙️ <b>Настройки:</b>
/set_delete_time <сек> - время удаления

❓ <b>Вопросы?</b> Обратитесь к главному администратору."""
    
    send_msg(message.from_user.id, help_text, reply_markup=admin_keyboard())

# ============================================================
# ОБРАБОТЧИК КНОПОК
# ============================================================
@bot.message_handler(func=lambda message: message.text in ["📊 Статистика", "📝 Список слов", "👥 Админы", "🔐 Верификация", "📋 Помощь", "ℹ️ Статус"])
def button_handler(message):
    user_id = message.from_user.id
    
    if user_id not in authorized_users:
        send_msg(user_id, "⛔ Доступ запрещен. Только для администраторов.")
        return
    
    if message.text == "📊 Статистика":
        stats_cmd(message)
    elif message.text == "📝 Список слов":
        list_words_cmd(message)
    elif message.text == "👥 Админы":
        list_admins_cmd(message)
    elif message.text == "🔐 Верификация":
        send_msg(user_id, """🔐 <b>Управление верификацией</b>

📋 Доступные команды:
/verify - пройти верификацию
/verify_user <id> - верифицировать пользователя
/verify_manual <id> - ручная верификация
/unrestrict <id> - снять ограничение""")
    elif message.text == "📋 Помощь":
        help_cmd(message)
    elif message.text == "ℹ️ Статус":
        status_cmd(message)

@bot.message_handler(content_types=['text'], chat_types=['private'])
def private_message_handler(message):
    user_id = message.from_user.id
    
    if user_id in authorized_users:
        text = message.text.strip()
        if text.startswith('/'):
            handle_admin_commands(message)
        else:
            if text not in ["📊 Статистика", "📝 Список слов", "👥 Админы", "🔐 Верификация", "📋 Помощь", "ℹ️ Статус"]:
                send_msg(user_id, "❓ Неизвестная команда. Используйте /help для списка команд.")
    else:
        if message.text.strip() == ADMIN_PASSWORD:
            authorized_users[user_id] = True
            send_msg(user_id, "✅ <b>Доступ разрешен!</b> Добро пожаловать в админ-панель.", reply_markup=admin_keyboard())
            start_cmd(message)
        else:
            send_msg(user_id, "❌ <b>Неверный пароль!</b> Попробуйте снова.")

# ============================================================
# КОМАНДЫ ДЛЯ КНОПОК
# ============================================================
def list_words_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    word_list = "\n".join([f"• {w}" for w in FORBIDDEN_WORDS])
    send_msg(message.from_user.id, f"📝 <b>Список запрещенных слов:</b>\n\n{word_list}")

def list_admins_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    admin_list = "\n".join([f"• {u}" for u in authorized_users])
    send_msg(message.from_user.id, f"👥 <b>Список администраторов:</b>\n\n{admin_list}")

@bot.message_handler(commands=['list_words'])
def list_words_command(message):
    list_words_cmd(message)

@bot.message_handler(commands=['list_admins'])
def list_admins_command(message):
    list_admins_cmd(message)

# ============================================================
# ОСТАЛЬНЫЕ КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['verify'], chat_types=['group', 'supergroup'])
def verify_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if is_verified(user_id, chat_id):
        send_msg(message.from_user.id, "✅ Вы уже верифицированы в этом чате")
        return
    if user_id in verification_data:
        send_msg(message.from_user.id, "⏳ Вы уже на верификации")
        return
    if user_id in restricted_users:
        send_msg(message.from_user.id, "⛔ Вы ограничены. Обратитесь к администратору.")
        return
    
    user = safe_api_call(bot.get_chat_member, chat_id, user_id)
    if user:
        send_verification(chat_id, user_id, user.user.username, user.user.first_name, is_rejoin=True)
        send_msg(message.from_user.id, "✅ Вопрос для верификации отправлен в чат!")

@bot.message_handler(commands=['verify_user'], chat_types=['group', 'supergroup'])
def verify_user_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    parts = message.text.split()
    if len(parts) != 2:
        send_msg(message.from_user.id, "❌ /verify_user <id>\n\nПример: /verify_user 123456789")
        return
    
    try:
        target = int(parts[1])
        chat_id = message.chat.id
        
        if is_verified(target, chat_id):
            send_msg(message.from_user.id, f"✅ Пользователь {target} уже верифицирован")
            return
        if target in verification_data:
            send_msg(message.from_user.id, f"⏳ Пользователь {target} уже на верификации")
            return
        if target in restricted_users:
            send_msg(message.from_user.id, f"⛔ Пользователь {target} ограничен")
            return
        
        user = safe_api_call(bot.get_chat_member, chat_id, target)
        if user:
            send_verification(chat_id, target, user.user.username, user.user.first_name, is_rejoin=True)
            send_msg(message.from_user.id, f"✅ Вопрос отправлен пользователю {target}")
            
    except ValueError:
        send_msg(message.from_user.id, "❌ Неверный ID")

@bot.message_handler(commands=['verify_manual'])
def verify_manual_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    parts = message.text.split()
    if len(parts) != 2:
        send_msg(message.from_user.id, "❌ /verify_manual <id>\n\nПример: /verify_manual 123456789")
        return
    
    try:
        user_id = int(parts[1])
        chat_id = message.chat.id
        
        if user_id in verification_data:
            for msg_id in verification_data[user_id]['message_ids']:
                delete_msg(chat_id, msg_id)
            del verification_data[user_id]
        
        if user_id in restricted_users:
            # Снимаем ограничение
            permissions = types.ChatPermissions(
                can_send_messages=True,
                can_send_media=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
            safe_api_call(bot.restrict_chat_member, chat_id, user_id, permissions)
            del restricted_users[user_id]
        
        mark_verified(user_id, chat_id)
        
        user = safe_api_call(bot.get_chat_member, chat_id, user_id)
        if user:
            send_welcome(chat_id, user_id, user.user.username, user.user.first_name)
        
        send_and_delete(chat_id, "✅ Пользователь верифицирован администратором! Добро пожаловать! 🎉", delay=MESSAGE_DELETE_SECONDS)
        send_msg(message.from_user.id, f"✅ Пользователь {user_id} верифицирован")
        
    except ValueError:
        send_msg(message.from_user.id, "❌ Неверный ID")

@bot.message_handler(commands=['unrestrict'])
def unrestrict_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    parts = message.text.split()
    if len(parts) != 2:
        send_msg(message.from_user.id, "❌ /unrestrict <id>\n\nПример: /unrestrict 123456789")
        return
    
    try:
        user_id = int(parts[1])
        if user_id in restricted_users:
            chat_id = restricted_users[user_id]['chat_id']
            
            # Снимаем ограничение
            permissions = types.ChatPermissions(
                can_send_messages=True,
                can_send_media=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
            
            safe_api_call(bot.restrict_chat_member, chat_id, user_id, permissions)
            del restricted_users[user_id]
            
            send_msg(message.from_user.id, f"✅ Ограничение снято с {user_id}")
            send_and_delete(chat_id, "✅ Администратор снял ограничение с пользователя", delay=MESSAGE_DELETE_SECONDS)
        else:
            send_msg(message.from_user.id, "❌ Пользователь не ограничен")
            
    except ValueError:
        send_msg(message.from_user.id, "❌ Неверный ID")

@bot.message_handler(commands=['set_delete_time'])
def set_delete_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    parts = message.text.split()
    if len(parts) != 2:
        send_msg(message.from_user.id, "❌ /set_delete_time <секунды>\n\nПример: /set_delete_time 30")
        return
    
    try:
        seconds = int(parts[1])
        if seconds < 5:
            send_msg(message.from_user.id, "❌ Минимум 5 секунд")
            return
        if seconds > 300:
            send_msg(message.from_user.id, "❌ Максимум 300 секунд (5 минут)")
            return
        
        global MESSAGE_DELETE_SECONDS
        MESSAGE_DELETE_SECONDS = seconds
        send_msg(message.from_user.id, f"✅ Время удаления установлено: {seconds} секунд")
        
    except ValueError:
        send_msg(message.from_user.id, "❌ Введите число")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    chat_id = message.chat.id
    
    if chat_id not in chat_stats:
        send_msg(message.from_user.id, "📊 Нет статистики для этого чата")
        return
    
    s = chat_stats[chat_id]
    d = s.get('daily', {})
    
    stats_text = f"""📊 <b>Статистика чата</b>

📅 <b>Сегодня:</b>
├ 👥 Новых: {d.get('joins', 0)}
├ 💬 Сообщений: {d.get('messages', 0)}
└ ✅ Верификаций: {s.get('verifications', 0)}

📈 <b>Всего:</b>
├ 👥 Участников: {s.get('joins', 0)}
├ 💬 Сообщений: {s.get('messages', 0)}
└ ✅ Верификаций: {s.get('verifications', 0)}

⏳ На верификации: {len(verification_data)}
🚫 Ограничено: {len(restricted_users)}
✅ Верифицировано: {len(verified_users)}"""
    
    send_msg(message.from_user.id, stats_text)

@bot.message_handler(commands=['stats_all'])
def stats_all_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    if not chat_stats:
        send_msg(message.from_user.id, "📊 Нет статистики")
        return
    
    total_joins = sum(s.get('joins', 0) for s in chat_stats.values())
    total_messages = sum(s.get('messages', 0) for s in chat_stats.values())
    total_verifications = sum(s.get('verifications', 0) for s in chat_stats.values())
    
    text = f"""📊 <b>Общая статистика по всем чатам</b>

📈 <b>Всего:</b>
├ 👥 Участников: {total_joins}
├ 💬 Сообщений: {total_messages}
└ ✅ Верификаций: {total_verifications}

📋 <b>По чатам:</b>"""
    
    for cid, s in chat_stats.items():
        try:
            chat = safe_api_call(bot.get_chat, cid)
            name = chat.title if chat else "Чат"
        except:
            name = "Чат"
        text += f"\n\n📌 {name}:\n  ├ 👥 {s.get('joins', 0)}\n  ├ 💬 {s.get('messages', 0)}\n  └ ✅ {s.get('verifications', 0)}"
    
    send_msg(message.from_user.id, text)

@bot.message_handler(commands=['status'])
def status_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    
    status_text = f"""ℹ️ <b>Статус бота</b>

📋 <b>Информация:</b>
├ 📝 Слов в фильтре: {len(FORBIDDEN_WORDS)}
├ 👥 Админов: {len(authorized_users)}
├ ⏳ На верификации: {len(verification_data)}
├ 🚫 Ограничено: {len(restricted_users)}
├ ✅ Верифицировано: {len(verified_users)}
├ 📊 Чатов: {len(chat_stats)}
├ ⏱ Таймаут верификации: {VERIFICATION_TIMEOUT} сек
├ 🗑 Время удаления: {MESSAGE_DELETE_SECONDS} сек
└ 📝 Вопросов в базе: {len(VERIFICATION_QUESTIONS)}

🟢 <b>Статус:</b> ✅ Работает

🤖 <b>Бот:</b> @{bot.get_me().username}"""
    
    send_msg(message.from_user.id, status_text)

@bot.message_handler(commands=['send_stats'])
def send_stats_cmd(message):
    if message.from_user.id not in authorized_users:
        return
    send_daily_stats()
    send_msg(message.from_user.id, "📊 Статистика отправлена администратору!")

# ============================================================
# АДМИН-КОМАНДЫ
# ============================================================
def handle_admin_commands(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text.startswith('/add_admin'):
        parts = text.split()
        if len(parts) == 3 and parts[1] == ADMIN_PASSWORD:
            try:
                new_id = int(parts[2])
                authorized_users[new_id] = True
                send_msg(user_id, f"✅ Админ {new_id} добавлен")
            except ValueError:
                send_msg(user_id, "❌ Неверный ID")
        else:
            send_msg(user_id, "❌ /add_admin <пароль> <id>")
    
    elif text.startswith('/remove_admin'):
        parts = text.split()
        if len(parts) == 2:
            try:
                rid = int(parts[1])
                if rid == ADMIN_ID:
                    send_msg(user_id, "❌ Нельзя удалить главного администратора")
                elif rid in authorized_users:
                    del authorized_users[rid]
                    send_msg(user_id, f"✅ Админ {rid} удален")
                else:
                    send_msg(user_id, "❌ Админ не найден")
            except ValueError:
                send_msg(user_id, "❌ Неверный ID")
        else:
            send_msg(user_id, "❌ /remove_admin <id>")
    
    elif text.startswith('/add_word'):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            word = clean_text(parts[1])
            if word and word not in FORBIDDEN_WORDS:
                FORBIDDEN_WORDS.append(word)
                send_msg(user_id, f"✅ Слово '{word}' добавлено в фильтр")
            else:
                send_msg(user_id, "❌ Слово уже есть или пусто")
        else:
            send_msg(user_id, "❌ /add_word <слово>")
    
    elif text.startswith('/remove_word'):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            word = clean_text(parts[1])
            if word in FORBIDDEN_WORDS:
                FORBIDDEN_WORDS.remove(word)
                send_msg(user_id, f"✅ Слово '{word}' удалено из фильтра")
            else:
                send_msg(user_id, "❌ Слово не найдено")
        else:
            send_msg(user_id, "❌ /remove_word <слово>")
    
    elif text.startswith('/check_text'):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            cleaned = clean_text(parts[1])
            found = [w for w in FORBIDDEN_WORDS if w in cleaned]
            if found:
                send_msg(user_id, f"🔍 Найдены запрещенные слова: {', '.join(found)}")
            else:
                send_msg(user_id, "✅ Текст чист. Запрещенных слов нет.")
        else:
            send_msg(user_id, "❌ /check_text <текст>")
    
    else:
        send_msg(user_id, "❓ Неизвестная команда. Используйте /help")

# ============================================================
# ФОНОВЫЕ ЗАДАЧИ
# ============================================================
def cleanup_loop():
    while True:
        time.sleep(60)
        try:
            for user_id, data in list(verification_data.items()):
                if time.time() - data['timestamp'] > VERIFICATION_TIMEOUT:
                    restrict_user(data['chat_id'], user_id)
            
            now = datetime.now()
            if now.hour == 23 and now.minute == 59:
                send_daily_stats()
                time.sleep(60)
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def send_daily_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    for cid, s in chat_stats.items():
        d = s.get('daily', {})
        if d.get('date') == today:
            try:
                chat = safe_api_call(bot.get_chat, cid)
                name = chat.title if chat else "Чат"
            except:
                name = "Чат"
            
            report = f"""📊 <b>Дневная статистика</b>

🏷 <b>Чат:</b> {name}
📅 <b>Дата:</b> {today}

👥 <b>Новых участников:</b> {d.get('joins', 0)}
💬 <b>Сообщений:</b> {d.get('messages', 0)}
✅ <b>Верификаций:</b> {s.get('verifications', 0)}

📈 <b>Общая статистика:</b>
├ 👥 Всего участников: {s.get('joins', 0)}
├ 💬 Всего сообщений: {s.get('messages', 0)}
└ ✅ Всего верификаций: {s.get('verifications', 0)}"""
            
            send_msg(ADMIN_ID, report)

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    try:
        send_msg(ADMIN_ID, """🚀 <b>Бот запущен!</b>

✅ Все системы работают
🔐 Верификация активна
🔄 Поддержка повторных входов
🛡 Защита от API ограничений
📊 Сбор статистики активен
📝 {len(FORBIDDEN_WORDS)} слов в фильтре

💡 Используйте /start в ЛС для управления""")
    except:
        pass
    
    print("=" * 50)
    print("🚀 БОТ ЗАПУЩЕН!")
    print("=" * 50)
    print(f"✅ {len(FORBIDDEN_WORDS)} слов в фильтре")
    print("✅ ВСЕ сообщения отправляются через send_msg()")
    print("✅ НИКАКОГО HTML и parse_mode")
    print("✅ Защита от ошибок 400, 429, 502")
    print("✅ Красивый интерфейс с эмодзи")
    print("=" * 50)
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    
    while True:
        try:
            bot.polling(
                none_stop=True,
                timeout=60,
                interval=1,
                allowed_updates=['message', 'callback_query']
            )
        except ApiTelegramException as e:
            error_code = getattr(e, 'error_code', 0)
            if error_code == 429:
                retry_after = 5
                if "retry after" in str(e):
                    try:
                        retry_after = int(str(e).split("retry after")[1].split()[0])
                    except:
                        pass
                print(f"⚠️ Rate limit. Ждем {retry_after+5} сек...")
                time.sleep(retry_after + 5)
            elif error_code == 502:
                print("⚠️ Bad Gateway. Ждем 10 сек...")
                time.sleep(10)
            else:
                print(f"❌ Ошибка polling: {e}")
                time.sleep(5)
        except Exception as e:
            print(f"❌ Неизвестная ошибка: {e}")
            time.sleep(5)
