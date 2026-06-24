# ============================================================
# bot.py - ГОТОВЫЙ РАБОЧИЙ БОТ
# ============================================================

import telebot
import re
import os
import time
import json
import logging
import random
import threading
import sqlite3
from datetime import datetime, timedelta
from telebot import types
from telebot.apihelper import ApiTelegramException
from contextlib import contextmanager

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1364254252
ADMIN_PASSWORD = "08091913"

if not BOT_TOKEN:
    raise ValueError("Нет токена BOT_TOKEN!")

# ============================================================
# НАСТРОЙКИ
# ============================================================

VERIFICATION_TIMEOUT = 120  # секунд
VERIFICATION_ATTEMPTS = 3
MESSAGE_DELETE_SECONDS = 30
MAX_WRONG_MESSAGES = 3
MAX_MESSAGES_PER_MINUTE = 20
STATS_TIME_HOUR = 23
STATS_TIME_MINUTE = 59
DB_FILE = "bot_data.db"

# ============================================================
# ТЕКСТЫ
# ============================================================

WELCOME_TEXT = """
🌟 Добро пожаловать в Вейп-Барахолку Краснодара, {user_mention}! 🎉

📋 Правила чата:
🚫 Запрещено:
• ❌ Не вейп-тематика
• ❌ Оскорбления и флуд
• ❌ Спам и реклама

⚠️ Внимание!
При скаме: @callumom 
Администрация не отвечает за сделки.

🏪 Лучшие вейп-шопы:
• 🔥 Mix Vape: https://t.me/mixvape1

💫 Приятного общения!
"""

VERIFICATION_TEXT = """
🔐 ВЕРИФИКАЦИЯ

👤 {mention}

Для подтверждения, что вы не робот, решите пример:

❓ {question} = ?

⏳ У вас {timeout} минут(ы) и {attempts} попытки.

💡 Напишите ТОЛЬКО число в чат!
"""

VERIFICATION_PASSED = "✅ Молодец! Добро пожаловать!"
VERIFICATION_FAILED = "❌ Неправильно. Осталось попыток: {remaining}"
VERIFICATION_TIMEOUT_TEXT = "⏰ Время верификации истекло"
VERIFICATION_ATTEMPTS_EXCEEDED = "❌ Попытки исчерпаны"
VERIFICATION_RESTRICTED = "⛔ Пользователь не прошел верификацию и ограничен."

FORBIDDEN_WORDS_LIST = [
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

VERIFICATION_QUESTIONS = [
    {"question": "7 + 3", "answer": 10},
    {"question": "12 - 5", "answer": 7},
    {"question": "4 * 6", "answer": 24},
    {"question": "15 + 8", "answer": 23},
    {"question": "20 - 7", "answer": 13},
    {"question": "3 * 9", "answer": 27},
    {"question": "14 + 6", "answer": 20},
    {"question": "25 - 10", "answer": 15},
    {"question": "5 * 8", "answer": 40},
    {"question": "11 + 9", "answer": 20},
    {"question": "18 - 6", "answer": 12},
    {"question": "7 * 7", "answer": 49},
    {"question": "23 + 7", "answer": 30},
    {"question": "30 - 12", "answer": 18},
    {"question": "6 * 6", "answer": 36},
    {"question": "9 + 8", "answer": 17},
    {"question": "22 - 9", "answer": 13},
    {"question": "8 * 5", "answer": 40},
    {"question": "16 + 14", "answer": 30},
    {"question": "35 - 8", "answer": 27},
    {"question": "4 * 9", "answer": 36},
    {"question": "13 + 7", "answer": 20},
    {"question": "28 - 9", "answer": 19},
    {"question": "6 * 8", "answer": 48},
    {"question": "19 + 11", "answer": 30},
]

# ============================================================
# БАЗА ДАННЫХ
# ============================================================

class Database:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Пользователи
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    verified BOOLEAN DEFAULT 0,
                    restricted BOOLEAN DEFAULT 0,
                    banned BOOLEAN DEFAULT 0,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0
                )
            ''')
            
            # Верификация
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification (
                    user_id INTEGER PRIMARY KEY,
                    chat_id INTEGER,
                    question TEXT,
                    answer INTEGER,
                    attempts INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Статистика чатов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_stats (
                    chat_id INTEGER,
                    date TEXT,
                    joins INTEGER DEFAULT 0,
                    messages INTEGER DEFAULT 0,
                    verifications INTEGER DEFAULT 0,
                    bans INTEGER DEFAULT 0,
                    PRIMARY KEY (chat_id, date)
                )
            ''')
            
            # Запрещенные слова
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forbidden_words (
                    word TEXT PRIMARY KEY
                )
            ''')
            
            # Админы
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY
                )
            ''')
            
            conn.commit()
            
            # Добавляем главного админа
            cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
            conn.commit()
            
            # Добавляем дефолтные слова
            for word in FORBIDDEN_WORDS_LIST:
                cursor.execute('INSERT OR IGNORE INTO forbidden_words (word) VALUES (?)', (word,))
            conn.commit()
    
    def get_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    
    def add_user(self, user_id, username, first_name, last_name=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
    
    def mark_verified(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET verified = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
    
    def mark_restricted(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET restricted = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
    
    def mark_banned(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET banned = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
    
    def is_verified(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT verified FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return bool(row[0]) if row else False
    
    def is_restricted(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT restricted FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return bool(row[0]) if row else False
    
    def is_banned(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return bool(row[0]) if row else False
    
    def save_verification(self, user_id, chat_id, question, answer):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO verification (user_id, chat_id, question, answer, attempts)
                VALUES (?, ?, ?, ?, 0)
            ''', (user_id, chat_id, question, answer))
            conn.commit()
    
    def get_verification(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM verification WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    
    def delete_verification(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM verification WHERE user_id = ?', (user_id,))
            conn.commit()
    
    def increment_attempts(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE verification SET attempts = attempts + 1 WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    def update_stats(self, chat_id, stat_type):
        date = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_stats (chat_id, date, joins, messages, verifications, bans)
                VALUES (?, ?, 0, 0, 0, 0)
                ON CONFLICT(chat_id, date) DO UPDATE SET
                    joins = joins + CASE WHEN ? = 'joins' THEN 1 ELSE 0 END,
                    messages = messages + CASE WHEN ? = 'messages' THEN 1 ELSE 0 END,
                    verifications = verifications + CASE WHEN ? = 'verifications' THEN 1 ELSE 0 END,
                    bans = bans + CASE WHEN ? = 'bans' THEN 1 ELSE 0 END
            ''', (chat_id, stat_type, stat_type, stat_type, stat_type))
            conn.commit()
    
    def get_forbidden_words(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT word FROM forbidden_words')
            return [row[0] for row in cursor.fetchall()]
    
    def add_forbidden_word(self, word):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO forbidden_words (word) VALUES (?)', (word.lower(),))
            conn.commit()
    
    def remove_forbidden_word(self, word):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM forbidden_words WHERE word = ?', (word.lower(),))
            conn.commit()
    
    def clear_forbidden_words(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM forbidden_words')
            conn.commit()
    
    def is_admin(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    
    def get_admins(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM admins')
            return [row[0] for row in cursor.fetchall()]
    
    def add_admin(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (user_id,))
            conn.commit()
    
    def remove_admin(self, user_id):
        if user_id == ADMIN_ID:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
    
    def get_stats(self, days=30):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT chat_id,
                       SUM(joins) as total_joins,
                       SUM(messages) as total_messages,
                       SUM(verifications) as total_verifications,
                       SUM(bans) as total_bans
                FROM chat_stats
                WHERE date >= date('now', ?)
                GROUP BY chat_id
            ''', (f'-{days} days',))
            return cursor.fetchall()

# ============================================================
# ЛОГГЕР
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
db = Database()

# ============================================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================

admin_ids = set(db.get_admins())
verification_sessions = {}
restricted_users = {}
wrong_message_count = {}
user_message_count = {}
verification_timers = {}
forbidden_words = db.get_forbidden_words()

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_question():
    return random.choice(VERIFICATION_QUESTIONS)

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
    return any(word in cleaned for word in forbidden_words)

def send_and_delete(chat_id, text, delay=MESSAGE_DELETE_SECONDS, **kwargs):
    try:
        msg = bot.send_message(chat_id, text, **kwargs)
        if msg:
            timer = threading.Timer(delay, lambda: delete_message(chat_id, msg.message_id))
            timer.daemon = True
            timer.start()
        return msg
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return None

def delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

def safe_delete(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

def get_chat_name(chat_id):
    try:
        chat = bot.get_chat(chat_id)
        return chat.title or "Чат"
    except:
        return "Чат"

def cancel_timer(user_id):
    if user_id in verification_timers:
        try:
            verification_timers[user_id].cancel()
        except:
            pass
        del verification_timers[user_id]

def check_antiflood(user_id):
    now = time.time()
    if user_id not in user_message_count:
        user_message_count[user_id] = {'count': 0, 'reset_time': now + 60}
        return True
    
    data = user_message_count[user_id]
    if now > data['reset_time']:
        data['count'] = 0
        data['reset_time'] = now + 60
        return True
    
    if data['count'] >= MAX_MESSAGES_PER_MINUTE:
        return False
    
    data['count'] += 1
    return True

def is_admin(user_id):
    return user_id in admin_ids or user_id == ADMIN_ID

# ============================================================
# ОСНОВНАЯ ЛОГИКА
# ============================================================

def send_verification(chat_id, user_id, username, first_name, is_rejoin=False):
    try:
        cancel_timer(user_id)
        
        question_data = get_question()
        mention = f"@{username}" if username else first_name
        timeout_minutes = VERIFICATION_TIMEOUT // 60
        
        text = VERIFICATION_TEXT.format(
            mention=mention,
            question=question_data['question'],
            timeout=timeout_minutes,
            attempts=VERIFICATION_ATTEMPTS
        )
        
        # Сохраняем сессию
        verification_sessions[user_id] = {
            'chat_id': chat_id,
            'question': question_data['question'],
            'answer': question_data['answer'],
            'attempts': 0,
            'timestamp': time.time(),
            'message_ids': []
        }
        
        db.save_verification(user_id, chat_id, question_data['question'], question_data['answer'])
        wrong_message_count[user_id] = 0
        
        # Отправляем сообщение
        msg = bot.send_message(chat_id, text)
        if msg:
            verification_sessions[user_id]['message_ids'].append(msg.message_id)
        
        if not is_rejoin:
            db.update_stats(chat_id, 'joins')
        
        # Уведомляем админа
        admin_text = f"""👤 Новая верификация
├ 🆔 ID: {user_id}
├ 📛 Имя: {first_name}
├ 🔗 Юзернейм: @{username if username else "отсутствует"}
├ 💬 Чат: {chat_id} ({get_chat_name(chat_id)})
├ ❓ Вопрос: {question_data['question']}
└ 🕐 Время: {datetime.now().strftime("%H:%M:%S")}"""
        bot.send_message(ADMIN_ID, admin_text)
        
        # Отправляем в ЛС
        try:
            bot.send_message(user_id, f"🔐 В группе задан вопрос для верификации:\n\n❓ {question_data['question']} = ?\n\n⏳ У вас {timeout_minutes} минут(ы)\n\n📝 Напишите ответ (только число) в чат!")
        except:
            pass
        
        # Таймер
        timer = threading.Timer(VERIFICATION_TIMEOUT, restrict_user, args=[chat_id, user_id])
        timer.daemon = True
        timer.start()
        verification_timers[user_id] = timer
        
        logger.info(f"✅ Верификация отправлена пользователю {user_id} в чат {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка верификации: {e}")

def restrict_user(chat_id, user_id):
    try:
        if db.is_verified(user_id):
            return
        
        # Удаляем сессию
        if user_id in verification_sessions:
            for msg_id in verification_sessions[user_id].get('message_ids', []):
                safe_delete(chat_id, msg_id)
            del verification_sessions[user_id]
            db.delete_verification(user_id)
        
        # Ограничиваем
        bot.ban_chat_member(chat_id, user_id)
        bot.unban_chat_member(chat_id, user_id)
        
        restricted_users[user_id] = {'chat_id': chat_id, 'timestamp': time.time()}
        db.mark_restricted(user_id)
        
        send_and_delete(chat_id, VERIFICATION_RESTRICTED, MESSAGE_DELETE_SECONDS)
        bot.send_message(ADMIN_ID, f"⛔ Пользователь {user_id} ограничен в чате {chat_id}")
        
        logger.info(f"⛔ Пользователь {user_id} ограничен в чате {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка ограничения: {e}")

def handle_verification_answer(chat_id, user_id, message_id, answer_text):
    if user_id not in verification_sessions:
        return False, "❌ Вы не на верификации"
    
    session = verification_sessions[user_id]
    
    # Проверяем время
    if time.time() - session['timestamp'] > VERIFICATION_TIMEOUT:
        del verification_sessions[user_id]
        db.delete_verification(user_id)
        return False, "⏰ Время истекло"
    
    # Проверяем попытки
    if session['attempts'] >= VERIFICATION_ATTEMPTS:
        del verification_sessions[user_id]
        db.delete_verification(user_id)
        return False, "❌ Попытки исчерпаны"
    
    # Проверяем ответ
    try:
        answer = int(answer_text.strip())
    except ValueError:
        wrong_message_count[user_id] = wrong_message_count.get(user_id, 0) + 1
        
        if wrong_message_count[user_id] >= MAX_WRONG_MESSAGES:
            bot.ban_chat_member(chat_id, user_id)
            if user_id in verification_sessions:
                del verification_sessions[user_id]
                db.delete_verification(user_id)
            bot.send_message(ADMIN_ID, f"🚫 Пользователь {user_id} забанен за спам в чате {chat_id}")
            send_and_delete(chat_id, f"🚫 Пользователь забанен за спам!", 10)
            return False, "🚫 Забанен за спам"
        
        remaining = MAX_WRONG_MESSAGES - wrong_message_count[user_id]
        send_and_delete(chat_id, f"⚠️ Введите число! Осталось: {remaining}", 5)
        return False, "⚠️ Введите число"
    
    safe_delete(chat_id, message_id)
    
    if answer == session['answer']:
        # Успех!
        cancel_timer(user_id)
        
        for msg_id in session.get('message_ids', []):
            safe_delete(chat_id, msg_id)
        
        del verification_sessions[user_id]
        db.delete_verification(user_id)
        
        if user_id in wrong_message_count:
            del wrong_message_count[user_id]
        
        # Отправляем приветствие
        send_and_delete(chat_id, VERIFICATION_PASSED, MESSAGE_DELETE_SECONDS)
        
        # Отмечаем как верифицированного
        db.mark_verified(user_id)
        db.update_stats(chat_id, 'verifications')
        
        # Отправляем приветствие
        user = db.get_user(user_id)
        if user:
            mention = f"@{user['username']}" if user['username'] else user['first_name']
            welcome = WELCOME_TEXT.format(user_mention=mention)
            send_and_delete(chat_id, welcome, MESSAGE_DELETE_SECONDS)
        
        bot.send_message(ADMIN_ID, f"✅ Пользователь {user_id} успешно верифицирован в чате {chat_id}")
        
        return True, "✅ Верификация успешна!"
    else:
        # Неправильный ответ
        session['attempts'] += 1
        db.increment_attempts(user_id)
        remaining = VERIFICATION_ATTEMPTS - session['attempts']
        
        if remaining > 0:
            msg = send_and_delete(chat_id, VERIFICATION_FAILED.format(remaining=remaining), MESSAGE_DELETE_SECONDS)
            if msg:
                session['message_ids'].append(msg.message_id)
        else:
            for msg_id in session.get('message_ids', []):
                safe_delete(chat_id, msg_id)
            del verification_sessions[user_id]
            db.delete_verification(user_id)
            restrict_user(chat_id, user_id)
        
        return False, f"❌ Осталось попыток: {remaining}"

# ============================================================
# ОБРАБОТЧИКИ СООБЩЕНИЙ
# ============================================================

@bot.message_handler(content_types=['new_chat_members'], chat_types=['group', 'supergroup'])
def new_member_handler(message):
    chat_id = message.chat.id
    
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        
        user_id = member.id
        
        # Добавляем в БД
        db.add_user(user_id, member.username, member.first_name, member.last_name)
        
        # Проверяем бан
        if db.is_banned(user_id):
            try:
                bot.ban_chat_member(chat_id, user_id)
            except:
                pass
            continue
        
        # Проверяем верификацию
        if db.is_verified(user_id):
            continue
        
        # Проверяем сессию
        if user_id in verification_sessions:
            continue
        
        # Отправляем верификацию
        send_verification(chat_id, user_id, member.username, member.first_name or "Пользователь", False)

@bot.message_handler(content_types=['text'], chat_types=['group', 'supergroup'])
def group_message_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text or ""
    
    # Команды пропускаем
    if text.startswith('/'):
        return
    
    # Анти-флуд
    if not check_antiflood(user_id):
        safe_delete(chat_id, message.message_id)
        send_and_delete(chat_id, f"⏳ {message.from_user.first_name}, слишком много сообщений! Подождите немного.", 10)
        return
    
    # Если на верификации
    if user_id in verification_sessions:
        safe_delete(chat_id, message.message_id)
        handle_verification_answer(chat_id, user_id, message.message_id, text)
        return
    
    # Если ограничен
    if user_id in restricted_users or db.is_restricted(user_id):
        safe_delete(chat_id, message.message_id)
        send_and_delete(chat_id, f"⛔ {message.from_user.first_name}, вы ограничены.", MESSAGE_DELETE_SECONDS)
        return
    
    # Если не верифицирован
    if not db.is_verified(user_id):
        safe_delete(chat_id, message.message_id)
        send_and_delete(chat_id, f"🔐 {message.from_user.first_name}, вы не верифицированы. Пройдите верификацию при входе в чат.", 15)
        return
    
    # Верифицированный пользователь
    db.update_stats(chat_id, 'messages')
    
    # Проверка на запрещенные слова
    if has_forbidden_words(text):
        safe_delete(chat_id, message.message_id)
        
        # Баним
        try:
            bot.ban_chat_member(chat_id, user_id)
            db.mark_banned(user_id)
            db.update_stats(chat_id, 'bans')
            
            link = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
            log = f"""🚫 Забанен спамер!

🆔 ID: {user_id}
📛 Имя: {message.from_user.first_name or "Без имени"}
🔗 Ссылка: {link}
💬 Чат: {chat_id} ({get_chat_name(chat_id)})
📝 Текст: {text}
🕐 Время: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}"""
            bot.send_message(ADMIN_ID, log)
            
            send_and_delete(chat_id, f"🚫 {message.from_user.first_name}, вы забанены за спам!", 10)
            
            logger.info(f"🚫 Пользователь {user_id} забанен за спам в чате {chat_id}")
            
        except Exception as e:
            logger.error(f"Ошибка бана: {e}")

# ============================================================
# КОМАНДЫ
# ============================================================

@bot.message_handler(commands=['start'], chat_types=['private'])
def start_cmd(message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        text = """🌟 Добро пожаловать в админ-панель!

👋 Привет, администратор!

📋 Доступные команды:

🔐 Верификация:
/verify - начать верификацию
/verify_manual <id> - ручная верификация
/unrestrict <id> - снять ограничение
/ban_user <id> - забанить пользователя

📊 Статистика:
/stats - статистика
/status - статус бота

👥 Админы:
/add_admin <id> - добавить админа
/remove_admin <id> - удалить админа
/list_admins - список админов

📝 Слова:
/add_word <слово> - добавить слово
/remove_word <слово> - удалить слово
/list_words - список слов
/clear_words - очистить все

⚙️ Настройки:
/set_timeout <сек> - таймаут верификации
/set_attempts <число> - попытки верификации
/set_delete_time <сек> - время удаления

💾 Бэкап:
/backup - создать бэкап"""
        bot.send_message(user_id, text, reply_markup=admin_keyboard())
    else:
        bot.send_message(user_id, "🔐 Введите пароль для доступа к админ-панели:")

@bot.message_handler(commands=['help'], chat_types=['private'])
def help_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    help_text = """📋 ПОМОЩЬ ПО КОМАНДАМ

🔐 ВЕРИФИКАЦИЯ:
/verify - начать верификацию
/verify_manual <id> - ручная верификация
/unrestrict <id> - снять ограничение
/ban_user <id> - забанить пользователя

📊 СТАТИСТИКА:
/stats - статистика
/status - статус бота

👥 УПРАВЛЕНИЕ:
/add_admin <id> - добавить админа
/remove_admin <id> - удалить админа
/list_admins - список админов

📝 ФИЛЬТР:
/add_word <слово> - добавить слово
/remove_word <слово> - удалить слово
/list_words - список слов
/clear_words - очистить все

⚙️ НАСТРОЙКИ:
/set_timeout <сек> - таймаут верификации
/set_attempts <число> - попытки верификации
/set_delete_time <сек> - время удаления

💾 БЭКАП:
/backup - создать бэкап"""
    
    bot.send_message(message.from_user.id, help_text)

@bot.message_handler(commands=['status'], chat_types=['private'])
def status_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE verified = 1')
        verified_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE restricted = 1')
        restricted_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1')
        banned_count = cursor.fetchone()[0]
    
    text = f"""ℹ️ СТАТУС БОТА

📋 ИНФОРМАЦИЯ:
├ 📝 Слов в фильтре: {len(forbidden_words)}
├ 👥 Админов: {len(admin_ids)}
├ 👤 Всего пользователей: {total_users}
├ ✅ Верифицировано: {verified_count}
├ ⏳ На верификации: {len(verification_sessions)}
├ 🚫 Ограничено: {restricted_count}
├ 🚫 Забанено: {banned_count}
├ ⏱ Таймаут: {VERIFICATION_TIMEOUT} сек
├ 🗑 Удаление: {MESSAGE_DELETE_SECONDS} сек
└ 🛡 Анти-флуд: {MAX_MESSAGES_PER_MINUTE} сообщ/мин

🟢 СТАТУС: ✅ Работает
📊 БД: SQLite
🤖 Бот: @{bot.get_me().username}"""
    
    bot.send_message(message.from_user.id, text)

@bot.message_handler(commands=['stats'], chat_types=['private'])
def stats_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    stats = db.get_stats()
    
    if not stats:
        bot.send_message(message.from_user.id, "📊 Нет статистики.")
        return
    
    total_joins = sum(row['total_joins'] or 0 for row in stats)
    total_messages = sum(row['total_messages'] or 0 for row in stats)
    total_verifications = sum(row['total_verifications'] or 0 for row in stats)
    total_bans = sum(row['total_bans'] or 0 for row in stats)
    
    text = f"""📊 СТАТИСТИКА ЗА 30 ДНЕЙ

📈 ИТОГО:
├ 👥 Новых: {total_joins}
├ 💬 Сообщений: {total_messages}
├ ✅ Верификаций: {total_verifications}
└ 🚫 Банов: {total_bans}

📋 ПО ЧАТАМ:"""
    
    for row in stats[:10]:
        chat_id = row['chat_id']
        name = get_chat_name(chat_id)
        text += f"""

📌 {name}
├ 👥 Новых: {row['total_joins'] or 0}
├ 💬 Сообщений: {row['total_messages'] or 0}
├ ✅ Верификаций: {row['total_verifications'] or 0}
└ 🚫 Банов: {row['total_bans'] or 0}"""
    
    bot.send_message(message.from_user.id, text)

@bot.message_handler(commands=['list_words'], chat_types=['private'])
def list_words_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    words = db.get_forbidden_words()
    if words:
        word_list = "\n".join([f"• {w}" for w in words])
        bot.send_message(message.from_user.id, f"📝 Список запрещенных слов ({len(words)} шт.):\n\n{word_list}")
    else:
        bot.send_message(message.from_user.id, "📝 Список запрещенных слов пуст.")

@bot.message_handler(commands=['list_admins'], chat_types=['private'])
def list_admins_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    admins = db.get_admins()
    if admins:
        admin_list = "\n".join([f"• {uid}" for uid in admins])
        bot.send_message(message.from_user.id, f"👥 Список администраторов ({len(admins)}):\n\n{admin_list}")
    else:
        bot.send_message(message.from_user.id, "👥 Нет администраторов.")

@bot.message_handler(commands=['verify'], chat_types=['group', 'supergroup'])
def verify_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if db.is_verified(user_id):
        bot.send_message(user_id, "✅ Вы уже верифицированы")
        return
    
    if user_id in verification_sessions:
        bot.send_message(user_id, "⏳ Вы уже на верификации")
        return
    
    if user_id in restricted_users or db.is_restricted(user_id):
        bot.send_message(user_id, "⛔ Вы ограничены")
        return
    
    member = bot.get_chat_member(chat_id, user_id)
    if member:
        send_verification(chat_id, user_id, member.user.username, member.user.first_name, True)
        bot.send_message(user_id, "✅ Вопрос отправлен в чат!")

@bot.message_handler(commands=['verify_manual'])
def verify_manual_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /verify_manual <id>")
        return
    
    try:
        target = int(parts[1])
        chat_id = message.chat.id if message.chat.type != 'private' else None
        
        if not chat_id:
            bot.send_message(message.from_user.id, "❌ Используйте команду в группе")
            return
        
        # Отменяем верификацию
        if target in verification_sessions:
            cancel_timer(target)
            for msg_id in verification_sessions[target].get('message_ids', []):
                safe_delete(chat_id, msg_id)
            del verification_sessions[target]
            db.delete_verification(target)
        
        # Снимаем ограничение
        if target in restricted_users:
            bot.unban_chat_member(chat_id, target)
            del restricted_users[target]
        
        # Верифицируем
        db.mark_verified(target)
        db.update_stats(chat_id, 'verifications')
        
        # Приветствие
        user = db.get_user(target)
        if user:
            mention = f"@{user['username']}" if user['username'] else user['first_name']
            welcome = WELCOME_TEXT.format(user_mention=mention)
            send_and_delete(chat_id, welcome, MESSAGE_DELETE_SECONDS)
        
        send_and_delete(chat_id, "✅ Пользователь верифицирован администратором! Добро пожаловать! 🎉", MESSAGE_DELETE_SECONDS)
        bot.send_message(message.from_user.id, f"✅ Пользователь {target} верифицирован")
        
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Неверный ID")
    except Exception as e:
        logger.error(f"Ошибка ручной верификации: {e}")
        bot.send_message(message.from_user.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['unrestrict'])
def unrestrict_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /unrestrict <id>")
        return
    
    try:
        target = int(parts[1])
        chat_id = message.chat.id if message.chat.type != 'private' else None
        
        if not chat_id:
            bot.send_message(message.from_user.id, "❌ Используйте команду в группе")
            return
        
        if target in restricted_users or db.is_restricted(target):
            bot.unban_chat_member(chat_id, target)
            if target in restricted_users:
                del restricted_users[target]
            db.mark_verified(target)
            bot.send_message(message.from_user.id, f"✅ Ограничение снято с {target}")
            send_and_delete(chat_id, "✅ Администратор снял ограничение", MESSAGE_DELETE_SECONDS)
        else:
            bot.send_message(message.from_user.id, "❌ Пользователь не ограничен")
            
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Неверный ID")

@bot.message_handler(commands=['ban_user'])
def ban_user_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /ban_user <id>")
        return
    
    try:
        target = int(parts[1])
        chat_id = message.chat.id if message.chat.type != 'private' else None
        
        if not chat_id:
            bot.send_message(message.from_user.id, "❌ Используйте команду в группе")
            return
        
        bot.ban_chat_member(chat_id, target)
        db.mark_banned(target)
        db.update_stats(chat_id, 'bans')
        bot.send_message(message.from_user.id, f"✅ Пользователь {target} забанен")
        send_and_delete(chat_id, f"🚫 Пользователь {target} забанен администратором", 10)
        
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Неверный ID")

@bot.message_handler(commands=['add_admin'])
def add_admin_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /add_admin <id>")
        return
    
    try:
        target = int(parts[1])
        db.add_admin(target)
        admin_ids.add(target)
        bot.send_message(message.from_user.id, f"✅ Админ {target} добавлен")
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Неверный ID")

@bot.message_handler(commands=['remove_admin'])
def remove_admin_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /remove_admin <id>")
        return
    
    try:
        target = int(parts[1])
        if target == ADMIN_ID:
            bot.send_message(message.from_user.id, "❌ Нельзя удалить главного администратора")
            return
        
        if db.remove_admin(target):
            admin_ids.discard(target)
            bot.send_message(message.from_user.id, f"✅ Админ {target} удален")
        else:
            bot.send_message(message.from_user.id, "❌ Админ не найден")
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Неверный ID")

@bot.message_handler(commands=['add_word'])
def add_word_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /add_word <слово>")
        return
    
    word = parts[1].lower().strip()
    if word:
        db.add_forbidden_word(word)
        forbidden_words.append(word)
        bot.send_message(message.from_user.id, f"✅ Слово '{word}' добавлено")
    else:
        bot.send_message(message.from_user.id, "❌ Слово не может быть пустым")

@bot.message_handler(commands=['remove_word'])
def remove_word_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /remove_word <слово>")
        return
    
    word = parts[1].lower().strip()
    db.remove_forbidden_word(word)
    forbidden_words[:] = db.get_forbidden_words()
    bot.send_message(message.from_user.id, f"✅ Слово '{word}' удалено")

@bot.message_handler(commands=['clear_words'])
def clear_words_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    db.clear_forbidden_words()
    forbidden_words.clear()
    bot.send_message(message.from_user.id, "✅ Все слова удалены")

@bot.message_handler(commands=['set_timeout'])
def set_timeout_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /set_timeout <сек>\n\nПример: /set_timeout 120")
        return
    
    try:
        seconds = int(parts[1])
        if seconds < 30:
            bot.send_message(message.from_user.id, "❌ Минимум 30 секунд")
            return
        if seconds > 600:
            bot.send_message(message.from_user.id, "❌ Максимум 600 секунд (10 минут)")
            return
        
        global VERIFICATION_TIMEOUT
        VERIFICATION_TIMEOUT = seconds
        bot.send_message(message.from_user.id, f"✅ Таймаут установлен: {seconds} сек")
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Введите число")

@bot.message_handler(commands=['set_attempts'])
def set_attempts_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /set_attempts <число>\n\nПример: /set_attempts 3")
        return
    
    try:
        attempts = int(parts[1])
        if attempts < 1:
            bot.send_message(message.from_user.id, "❌ Минимум 1 попытка")
            return
        if attempts > 10:
            bot.send_message(message.from_user.id, "❌ Максимум 10 попыток")
            return
        
        global VERIFICATION_ATTEMPTS
        VERIFICATION_ATTEMPTS = attempts
        bot.send_message(message.from_user.id, f"✅ Попыток установлено: {attempts}")
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Введите число")

@bot.message_handler(commands=['set_delete_time'])
def set_delete_time_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.from_user.id, "❌ /set_delete_time <сек>\n\nПример: /set_delete_time 30")
        return
    
    try:
        seconds = int(parts[1])
        if seconds < 5:
            bot.send_message(message.from_user.id, "❌ Минимум 5 секунд")
            return
        if seconds > 300:
            bot.send_message(message.from_user.id, "❌ Максимум 300 секунд (5 минут)")
            return
        
        global MESSAGE_DELETE_SECONDS
        MESSAGE_DELETE_SECONDS = seconds
        bot.send_message(message.from_user.id, f"✅ Время удаления установлено: {seconds} сек")
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Введите число")

@bot.message_handler(commands=['backup'])
def backup_cmd(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        
        import shutil
        shutil.copy2(DB_FILE, backup_file)
        
        bot.send_message(message.from_user.id, f"✅ Бэкап создан: {backup_file}")
    except Exception as e:
        bot.send_message(message.from_user.id, f"❌ Ошибка создания бэкапа: {e}")

# ============================================================
# КЛАВИАТУРА АДМИНА
# ============================================================

def admin_keyboard():
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

@bot.message_handler(func=lambda message: message.text in ["📊 Статистика", "📝 Список слов", "👥 Админы", "🔐 Верификация", "📋 Помощь", "ℹ️ Статус"])
def button_handler(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.send_message(user_id, "⛔ Доступ запрещен")
        return
    
    if message.text == "📊 Статистика":
        stats_cmd(message)
    elif message.text == "📝 Список слов":
        list_words_cmd(message)
    elif message.text == "👥 Админы":
        list_admins_cmd(message)
    elif message.text == "🔐 Верификация":
        bot.send_message(user_id, """🔐 Управление верификацией

📋 Доступные команды:
/verify - пройти верификацию
/verify_manual <id> - ручная верификация
/unrestrict <id> - снять ограничение
/ban_user <id> - забанить пользователя""")
    elif message.text == "📋 Помощь":
        help_cmd(message)
    elif message.text == "ℹ️ Статус":
        status_cmd(message)

# ============================================================
# ОБРАБОТКА ЛИЧНЫХ СООБЩЕНИЙ
# ============================================================

@bot.message_handler(content_types=['text'], chat_types=['private'])
def private_message_handler(message):
    user_id = message.from_user.id
    text = message.text or ""
    
    if text == ADMIN_PASSWORD:
        db.add_admin(user_id)
        admin_ids.add(user_id)
        bot.send_message(user_id, "✅ Доступ разрешен! Добро пожаловать в админ-панель.", reply_markup=admin_keyboard())
        start_cmd(message)
    elif text.startswith('/'):
        pass  # Команды обрабатываются другими обработчиками
    else:
        if is_admin(user_id):
            bot.send_message(user_id, "❓ Неизвестная команда. Используйте /help")
        else:
            bot.send_message(user_id, "🔐 Введите пароль для доступа к админ-панели:")

# ============================================================
# ФОНОВЫЕ ЗАДАЧИ
# ============================================================

def cleanup_loop():
    last_stats_date = None
    
    while True:
        time.sleep(60)
        try:
            current_time = time.time()
            now = datetime.now()
            
            # Проверка просроченных верификаций
            for user_id, session in list(verification_sessions.items()):
                if current_time - session['timestamp'] > VERIFICATION_TIMEOUT:
                    restrict_user(session['chat_id'], user_id)
            
            # Ежедневная статистика
            if now.hour == STATS_TIME_HOUR and now.minute == STATS_TIME_MINUTE:
                if last_stats_date != now.strftime("%Y-%m-%d"):
                    send_daily_stats()
                    last_stats_date = now.strftime("%Y-%m-%d")
                    time.sleep(60)
            
        except Exception as e:
            logger.error(f"Ошибка в cleanup_loop: {e}")

def send_daily_stats():
    try:
        stats = db.get_stats()
        if not stats:
            bot.send_message(ADMIN_ID, "📊 Нет статистики за сегодня")
            return
        
        total_joins = sum(row['total_joins'] or 0 for row in stats)
        total_messages = sum(row['total_messages'] or 0 for row in stats)
        total_verifications = sum(row['total_verifications'] or 0 for row in stats)
        total_bans = sum(row['total_bans'] or 0 for row in stats)
        
        text = f"""📊 ЕЖЕДНЕВНЫЙ ОТЧЕТ
📅 {datetime.now().strftime("%d.%m.%Y")}

📈 СТАТИСТИКА:
├ 👥 Новых: {total_joins}
├ 💬 Сообщений: {total_messages}
├ ✅ Верификаций: {total_verifications}
└ 🚫 Банов: {total_bans}

👤 ВЕРИФИКАЦИИ:
├ ⏳ Ожидают: {len(verification_sessions)}
├ 🚫 Ограничены: {len(restricted_users)}
└ ✅ Админов: {len(admin_ids)}

🕐 {datetime.now().strftime("%H:%M:%S")}"""
        
        bot.send_message(ADMIN_ID, text)
        logger.info("✅ Ежедневный отчет отправлен")
        
    except Exception as e:
        logger.error(f"Ошибка отправки статистики: {e}")

# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    try:
        bot.send_message(ADMIN_ID, f"""🚀 БОТ ЗАПУЩЕН!

✅ Все системы работают
🔐 Верификация активна (ТОЛЬКО при входе!)
📝 {len(forbidden_words)} слов в фильтре
👥 Админов: {len(admin_ids)}
🕐 Отчет в {STATS_TIME_HOUR:02d}:{STATS_TIME_MINUTE:02d}

💡 /start - админ-панель""")
    except:
        pass
    
    print("=" * 50)
    print("🚀 БОТ ЗАПУЩЕН!")
    print("=" * 50)
    print(f"✅ {len(forbidden_words)} слов в фильтре")
    print(f"👥 Админов: {len(admin_ids)}")
    print(f"🕐 Отчет в {STATS_TIME_HOUR:02d}:{STATS_TIME_MINUTE:02d}")
    print("=" * 50)
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, interval=1)
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
