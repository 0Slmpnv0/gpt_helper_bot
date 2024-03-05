from telebot import async_telebot
import telebot.types
import asyncio
import dotenv
from gpt import Conversation
import time
from db import init_users, insert_data, update_data, reset_data, get_data


telegram_token = dotenv.get_key('.env', 'TELEGRAM_BOT_TOKEN')
bot = async_telebot.AsyncTeleBot(telegram_token)
conversations: dict[str: Conversation] = {}


for uid in data:
    conversations[str(uid)] = Conversation('http://localhost:1234/v1/chat/completions',
                                           'Content-Type: application/json')
    conversations[str(uid)].load_context(uid)


@bot.message_handler(commands=['start', 'help'])
async def start(message: telebot.types.Message):
    if message.text == '/start':
        text = ('Добро пожаловать в бота-помощник по физике. Просто пишите сообщения и получайте ответ с учетом '
                'контекста!')
        conversations[str(message.from_user.id)] = Conversation('http://localhost:1234/v1/chat/completions',
                                                                'Content-Type: application/json')
        data[str(message.from_user.id)] = ''
        save_data(data)
    else:
        text = ('Чтобы попросить бота продолжить просто напишите "Продолжить". Регистр букв не важен. Задавайте боту '
                'ответы по физике и получайте сомнительные, вероятно, неправильные ответы')
    await bot.send_message(message.from_user.id, text)


@bot.message_handler(commands=['rm_context', 'debug'])
async def handle_complicated_bullshit(message: telebot.types):
    if message.text == '/debug':
        if str(message.from_user.id) not in admins:
            await bot.send_message(message.from_user.id, 'У вас нет доступа к этой команде')
            return

        try:
            await bot.send_message(message.from_user.id, '\n'.join([f'{time}: {err}' for time, err in logs.items()]))
        except:
            await bot.send_message(message.from_user.id,
                                   'Отправить логи не удалось. Возможно, файл слишком большой, или ошибок еще не было')


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
