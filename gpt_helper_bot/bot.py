from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup
import asyncio
import dotenv
from gpt import Conversation
import time
import db
import logging

logging.basicConfig(filename='bot.log', level=logging.DEBUG)
logging.debug('Bot startup initiated...')
telegram_token = dotenv.get_key('.env', 'TELEGRAM_BOT_TOKEN')
bot = TeleBot(telegram_token)
logging.debug('Bot started')
conversations: dict[str: Conversation] = {}
subjects = ['Философия', 'Математика', 'Русский язык', 'Английский язык', 'Программирование']

for user in db.select_from_users():
    conversations[user['user_id']] = Conversation('http://localhost:1234/v1/chat/completions',
                                                  'Content-Type: application/json')
    logging.debug(f'Added conversation for user {user["user_id"]}')

    if user['context']:
        conversations[user['user_id']].load_context(user['context'])
        logging.debug('Context for user {user["user_id"]} loaded successfully')


def kb_builder(buttons):
    kb = ReplyKeyboardMarkup()
    for button in buttons:
        kb.add(button)
    return kb


@bot.message_handler(commands=['start', 'help'])
def start(message: Message):
    if message.text == '/start':
        text = ('Добро пожаловать в бота-помощник по физике. Просто пишите сообщения и получайте ответ с учетом '
                'контекста!')
        if str(message.from_user.id) not in conversations:
            logging.debug('User {message.from_user.id} is not found in database. Creating new conversation')
            db.insert_data(str(message.from_user.id))
            conversations[str(message.from_user.id)] = Conversation('http://localhost:1234/v1/chat/completions',
                                                                    'Content-Type: application/json')
            logging.debug('Conversation for user {message.from_user.id} initiated successfully')
    else:
        bot.send_message(message.from_user.id, ('Чтобы попросить бота продолжить просто напишите "Продолжить". '
                                                'Регистр букв не важен. Задавайте боту'
                                                'ответы по физике и получайте сомнительные, вероятно, неправильные '
                                                'ответы'))
        return
    bot.send_message(message.from_user.id, text, reply_markup=kb_builder(subjects))
    bot.register_next_step_handler_by_chat_id(message.chat.id, subject_handler)


def subject_handler(message: Message):
    if message.text not in subjects:
        bot.send_message(message.from_user.id, 'Такого уровня нет. Пожалуйста, выберите уровень из кнопок:',
                         reply_markup=kb_builder(subjects))
        bot.register_next_step_handler_by_chat_id(message.from_user.id, handle_question)
        return
    else:
        bot.send_message(message.from_user.id, 'Отличный выбор! Теперь выберите уровень знаний, на котором будет вам '
                                               'давать ответ нейросеть',
                         reply_markup=kb_builder(subjects))
        db.update_data(str(message.from_user.id), subject=message.text)
    bot.register_next_step_handler_by_chat_id(message.from_user.id, level_handler)


def level_handler(message: Message):
    levels = ['Начальный', 'Продвинутый', 'Профессиональный']
    if message.text not in levels:
        bot.send_message(message.from_user.id, 'Такого уровня нет. Пожалуйста, выберите уровень из кнопок:',
                         reply_markup=kb_builder(levels))
        bot.register_next_step_handler_by_chat_id(message.from_user.id, level_handler)
        return
    db.update_data(str(message.from_user.id), level=message.text)
    bot.register_next_step_handler_by_chat_id(message.from_user.id, handle_question)


@bot.message_handler(commands=['debug'])
def handle_complicated_bullshit(message: Message):
    if message.text == '/debug':
        if str(message.from_user.id) not in db.select_from_users('user_id', ('admin', '1')):
            bot.send_message(message.from_user.id, 'У вас нет доступа к этой команде')
            return

        try:
            logging.debug('Trying to send logs')
            with open('bot.log', 'r') as logs:
                bot.send_message(message.from_user.id, logs.read())
            logging.warning(f'Logs sent to admin {db.get_data(str(message.from_user.id))["user_id"]}')
        except:
            bot.send_message(message.from_user.id,
                             'Отправить логи не удалось. Возможно, файл слишком большой, или ошибок еще не было')
            logging.error('Logs are not sent')


async def handle_question(message: Message):
    resp = conversations[str(message.from_user.id)].conv(question=message.text, system_content=system_content)
    if resp[0] == 'err':
        logging.error(resp[2])
        text = resp[1]
        bot.send_message(message.from_user.id, text)
    conversations[str(message.from_user.id)].save_context(message.from_user.id)
    text = resp[1]
    bot.send_message(message.from_user.id, text)


asyncio.run(bot.polling(non_stop=True))
