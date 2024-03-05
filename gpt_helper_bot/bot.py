from telebot import async_telebot
import telebot.types
import asyncio
import dotenv
from gpt import Conversation
import time
import db
import logging


logging.basicConfig(filename='bot.log', level=logging.DEBUG)
logging.debug('Bot startup initiated...')
telegram_token = dotenv.get_key('.env', 'TELEGRAM_BOT_TOKEN')
bot = async_telebot.AsyncTeleBot(telegram_token)
logging.debug('Bot started')
conversations: dict[str: Conversation] = {}

for user in db.select_from_users():
    conversations[user['user_id']] = Conversation('http://localhost:1234/v1/chat/completions',
                                                  'Content-Type: application/json')
    logging.debug(f'Added conversation for user {user["user_id"]}')

    if user['context']:
        conversations[user['user_id']].load_context(user['context'])
        logging.debug('Context for user {user["user_id"]} loaded successfully')


@bot.message_handler(commands=['start', 'help'])
async def start(message: telebot.types.Message):
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
        text = ('Чтобы попросить бота продолжить просто напишите "Продолжить". Регистр букв не важен. Задавайте боту '
                'ответы по физике и получайте сомнительные, вероятно, неправильные ответы')
    await bot.send_message(message.from_user.id, text)


@bot.message_handler(commands=['rm_context', 'debug'])
async def handle_complicated_bullshit(message: telebot.types):
    if message.text == '/debug':
        if str(message.from_user.id) not in db.select_from_users('user_id', ('admin', '1')):
            await bot.send_message(message.from_user.id, 'У вас нет доступа к этой команде')
            return

        try:
            logging.debug('Trying to send logs')
            with open('bot.log', 'r') as logs:
                await bot.send_message(message.from_user.id, logs.read())
            logging.warning(f'Logs sent to admin {db.get_data(str(message.from_user.id))["user_id"]}')
        except:
            await bot.send_message(message.from_user.id,
                                   'Отправить логи не удалось. Возможно, файл слишком большой, или ошибок еще не было')
            logging.error('Logs are not sent')

@bot.message_handler()
async def handle_question(message: telebot.types.Message):
    system_content = ('Ты - дружелюбный помощник для решения задач по физике. НЕ ИСПОЛЬЗУЙ ПРОГРАММИРОВАНИЕ. Когда у '
                      'тебя спрашивают какую-то величину или цифру, отвечай коротко и точно')
    resp = conversations[str(message.from_user.id)].conv(question=message.text, system_content=system_content)
    if resp[0] == 'err':
        logs[time.time()] = resp[2]
        text = resp[1]
        await bot.send_message(message.from_user.id, text)
    conversations[str(message.from_user.id)].save_context(message.from_user.id)
    text = resp[1]
    await bot.send_message(message.from_user.id, text)


asyncio.run(bot.polling(non_stop=True))
