Бот разделен на несколько файлов:

1. bot.py - основная логика бота
2. utils.py - функции для работы с json и класс Conversation, который упрощает взаимодействие с API GPT
3. users.json - файл, в котором в виде словаря хранятся все юзеры и их контекст. Это нужно чтобы бот работал без повторного использования команды /start, если вдруг работа программы будет прервана(в самом начале программы я итерируюсь по списку юзеров, и добавляю их Conversation в словарь, где ключ - юзер айди, а значение - Conversation)
4. logs.json - файл, в котором хранятся логи в формате {время:код_ошибки}
5. admins.json - файл, в котором в виде списка хранятся юзер айди админов. Тут не предусмотрен никакой UI. Пусть текущие админы делают это руками)

Также есть файлы poetry вместо конфига. Не доверяйте requirements.txt, потому что их тоже сделал poetry
