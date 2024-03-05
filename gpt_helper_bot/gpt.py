import requests
from transformers import AutoTokenizer
import db


def check_tokens(text, max_tokens=2048):
    tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
    return len(tokenizer.encode(text)) < max_tokens


class Conversation:
    def __init__(self,
                 api_link,
                 header,
                 model='whatever',
                 max_tokens: int = 2048,
                 temperature=1):
        self.api_link = api_link
        self.header = header
        self.model = model
        self.context: str = ''
        self.temperature = temperature
        self.max_tokens = max_tokens

    def save_context(self, uid):
        db.update_data(uid, context=self.context)

    def load_context(self, uid):
        self.context = db.get_data(uid)['context']

    def conv(self, question, level, subject, assistant_content='Решим задачу по шагам:'):
        system_content = (f'Ты - бот-помошник, который дает ответы по предмету: {subject}. Объясняй шаги как для '
                          f'человека с уровнем знаний: {level}')
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
