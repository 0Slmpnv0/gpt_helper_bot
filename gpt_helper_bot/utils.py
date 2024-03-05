import requests
import json
from transformers import AutoTokenizer


def check_tokens(text, max_tokens=2048):
    tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
    return len(tokenizer.encode(text)) < max_tokens


def load_data(data_type: str = 'users'):
    if data_type == "debug":
        path = 'debug.json'
    elif data_type == "admin":
        path = 'admins.json'
    elif data_type == "users":
        path = 'users.json'
    else:
        raise ValueError("Wrong data type")

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        return {}


def save_data(user_data: dict, data_type: str = ''):
    if data_type == "debug":
        path = 'debug.json'
    else:
        path = 'users.json'

    with open(path, 'w', encoding='utf-8') as file:
        json.dump(user_data, file, indent=2, ensure_ascii=False)


class Conversation:
    def __init__(self, api_link, header, model='whatever', max_tokens: int = 2048, temperature=1):
        self.api_link = api_link
        self.header = header
        self.model = model
        self.context: str = ''
        self.temperature = temperature
        self.max_tokens = max_tokens

    def save_context(self, uid):
        data = load_data()
        data[str(uid)] = self.context
        save_data(data)

    def load_context(self, uid):
        data = load_data()
        self.context = data[str(uid)]

    def conv(self, question, system_content, assistant_content='Решим задачу по шагам:'):
        user_content = question
        if not check_tokens(user_content):
            return ['exc', 'Текст слишком большой. Попробуйте его сократить']

        if user_content.lower() != "продолжить":
            self.context = ''

        else:
            if not self.context:
                return ['exc', 'Вы не можете попросить нейросеть продолжить, поскольку она еще ничего не ответила']


        resp = requests.post(
            self.api_link,
            headers={"Content-Type": "application/json"},

            json={
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content + self.context},
                ],
                "temperature": 1,
                "max_tokens": 2048
            }
        )
        if resp.status_code == 200 and 'choices' in resp.json():
            result = resp.json()['choices'][0]['message']['content']
            if result == "":
                return ['succ', "Объяснение закончено"]
        else:
            return ['err', f'Не удалось получить ответ от нейросети. Код ошибки: {resp.status_code}',
                    resp.status_code]
        self.context += result
        return ['succ', result]


