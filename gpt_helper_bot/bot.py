from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup
import dotenv
from gpt import Conversation
import db
import logging

db.init_users()
logging.basicConfig(filename='bot.log', level=logging.DEBUG)
logging.debug('Bot startup initiated...')
telegram_token = dotenv.get_key('.env', 'TELEGRAM_BOT_TOKEN')
bot = TeleBot(telegram_token)
logging.debug('Bot started')
conversations: dict[int: Conversation] = {}
subjects = ['Философия', 'Математика', 'Русский язык', 'Английский язык', 'Программирование']
levels = ['Начальный', 'Продвинутый', 'Профессиональный']

users = db.execute_query('''SELECT user_id, context FROM users''')
if users:
    for user in users:
        conversations[user['user_id']] = Conversation('http://localhost:1234/v1/chat/completions',
                                                      'Content-Type: application/json')
        logging.debug(f'Added conversation for user {user["user_id"]}')

        if user['context']:
            conversations[user['user_id']].load_context(user['context'])
            logging.debug(f'Context for user {user["user_id"]} loaded successfully')


def kb_builder(buttons):
    kb = ReplyKeyboardMarkup()
    for button in buttons:
        kb.add(button)
    return kb


@bot.message_handler(commands=['start', 'help'])
def start(message: Message):
    usr = db.get_user_data(message.from_user.id)
    if usr:
        user = usr[0]
    else:
        user = usr
    if message.text == '/start':
        text = ('Добро пожаловать в бота-помощник по физике. Выберите предмет, а после сложность ответа. Затем задайте '
                'вопрос и получите ответ не нейросети! Чтобы попросить нейросеть продолжить напишите "продолжить". '
                'регистр букв не учитывается. Пожалуйста, выберите предмет:')
        if not user:
            logging.debug(f'User {message.from_user.id} is not found in database. Creating new conversation')
            db.insert_data(message.from_user.id)
            conversations[str(message.from_user.id)] = Conversation('http://localhost:1234/v1/chat/completions',
                                                                    'Content-Type: application/json')
            logging.debug(f'Conversation for user {message.from_user.id} initiated successfully')
        else:
            if user['level']:
                bot.register_next_step_handler_by_chat_id(message.chat.id, handle_question)
                bot.send_message(message.from_user.id, 'Вы можете уже отправить запрос')
                return
            elif user['subject']:
                bot.register_next_step_handler_by_chat_id(message.from_user.id, level_handler)
                bot.send_message(message.from_user.id, 'Выберите уровень, на котором вам будет отвечать нейросеть:',
                                 reply_markup=kb_builder(subjects))
                return
        bot.send_message(message.from_user.id, text, reply_markup=kb_builder(subjects))
        bot.register_next_step_handler_by_chat_id(message.chat.id, subject_handler)
    else:
        text = '''
Чтобы задать новый вопрос без контекста можете просто его написать.
Чтобы попросить бота продолжить текущий ответ введите "Продолжить".
Чтобы сбросить предмет, сложность или и то и другое, воспользуйтесь соответствующими коммандами'''
        bot.send_message(message.from_user.id, text, reply_markup=kb_builder(subjects))
        bot.register_next_step_handler_by_chat_id(message.chat.id, subject_handler)


def subject_handler(message: Message):
    if message.text not in subjects:
        bot.send_message(message.from_user.id, 'Такого предмета нет. Пожалуйста, выберите уровень из кнопок:',
                         reply_markup=kb_builder(subjects))
        bot.register_next_step_handler_by_chat_id(message.from_user.id, subject_handler)
    else:
        user = db.get_user_data(message.from_user.id)[0]
        if user['level']:
            bot.send_message(message.from_user.id, 'Отличный выбор! Теперь можете просто задать вопрос!')
            bot.register_next_step_handler_by_chat_id(message.chat.id, handle_question)
        else:
            bot.register_next_step_handler_by_chat_id(message.chat.id, level_handler)
        bot.send_message(message.from_user.id, 'Отличный выбор! Теперь выберите уровень, на котором вам будет '
                                               'отвечать нейросеть:',
                         reply_markup=kb_builder(levels))
        db.update_subject(message.from_user.id, subject=message.text)
        if db.get_user_data(message.from_user.id)[0]['level']:
            bot.register_next_step_handler_by_chat_id(message.chat.id, handle_question)
        else:
            bot.register_next_step_handler_by_chat_id(message.from_user.id, level_handler)


def level_handler(message: Message):
    if message.text not in levels:
        bot.send_message(message.from_user.id, 'Такого уровня нет. Пожалуйста, выберите уровень из кнопок:',
                         reply_markup=kb_builder(levels))
        bot.register_next_step_handler_by_chat_id(message.from_user.id, level_handler)
        return
    db.update_level(message.from_user.id, level=message.text)
    bot.send_message(message.from_user.id, 'Готово! Теперь можете задавать вопрос', reply_markup=None)
    bot.register_next_step_handler_by_chat_id(message.from_user.id, handle_question)


@bot.message_handler(commands=['rm_level', 'rm_subject', 'rm_all'])
def handle_resets(message: Message):
    if message.text == '/rm_subject':
        db.update_level(message.from_user.id)
        bot.send_message(message.from_user.id, 'Предмет удален успешно! Выберите новый предмет из кнопок:',
                         reply_markup=kb_builder(subjects))
        bot.register_next_step_handler_by_chat_id(message.chat.id, subject_handler)
    elif message.text == '/rm_all':
        db.execute_query('DELETE FROM users WHERE user_id = ?', (message.from_user.id,))
        bot.send_message(message.from_user.id, 'Все данные успешно удалены! Выберите новый предмет из кнопок:',
                         reply_markup=kb_builder(subjects))
        bot.register_next_step_handler_by_chat_id(message.chat.id, subject_handler)
    else:
        db.update_level(message.from_user.id)
        bot.send_message(message.from_user.id, 'Уровень успешно удален! Выберите новый уровень из кнопок:',
                         reply_markup=kb_builder(levels))
        bot.register_next_step_handler_by_chat_id(message.chat.id, level_handler)


@bot.message_handler(commands=['debug'])
def handle_debug(message: Message):
    if message.text == '/debug':
        if str(message.from_user.id) not in db.execute_query('SELECT id FROM users WHERE admin = 1'):
            bot.send_message(message.from_user.id, 'У вас нет доступа к этой команде')
            return
        try:
            logging.debug('Trying to send logs')
            with open('bot.log', 'r') as logs:
                bot.send_message(message.from_user.id, logs.read())
            logging.warning(f'Logs sent to admin {db.get_user_data(message.from_user.id)["user_id"]}')
        except:
            bot.send_message(message.from_user.id,
                             'Отправить логи не удалось. Возможно, файл слишком большой, или ошибок еще не было')
            logging.error('Logs are not sent')


def handle_question(message: Message):
    if message.text[0:3] == '/rm':
        handle_resets(message)
        return
    res = db.get_user_data(message.from_user.id)[0]
    resp = conversations[message.from_user.id].conv(question=message.text,
                                                    level=res['level'],
                                                    subject=res['subject'])
    text = resp[1]
    if resp[0] == 'err':
        logging.error(resp[2])
        text = resp[1]
        bot.send_message(message.from_user.id, text)
    elif resp[0] == 'succ':
        conversations[message.from_user.id].save_context(message.from_user.id)
    else:
        text = resp[1]
    bot.send_message(message.from_user.id, text, reply_markup=kb_builder(['Продолжить']))
    bot.register_next_step_handler_by_chat_id(message.from_user.id, handle_question)


bot.polling(non_stop=True)
