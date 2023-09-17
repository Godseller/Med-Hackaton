"""
Модуль, позволяющий обратиться к нейросети Claude
"""
import os
import time

from typing import Optional
from datetime import datetime
from claude_api import Client
from dotenv import load_dotenv

# from promts_dict import promts


# загрузим переменные окружения из .env файла
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
# загрузим список cookie из переменной окружения
COOKIES = os.getenv('COOKIES').split('/')
# словарь, связывающий пользователя с его личным диалогом в Claude
user_dialogs = {}
# глобальная переменная для клиента Claude
CLAUDE = None


class FailToConnect(Exception):
    """
    кастомное исключение, возникающее при неудачном подключении
    к LLM
    """
    def __init__(self, txt):
        self.txt = txt


# создадим функцию для подключения к доступному клиенту claude
def connect_to_claude() -> None:
    """
    функция, выполняющая перебор доступных ключей для установления соединения с LLM
    """
    global CLAUDE
    for cookie in COOKIES:

        try:
            # клиент для работы с claude
            # CLAUDE = Client(cookie)

            # перед началом работы очистим все диалоги
            conversations = CLAUDE.list_all_conversations()
            for conversation in conversations:
                conversation_uuid = conversation['uuid']
                deleted = CLAUDE.delete_conversation(conversation_uuid)
                if deleted:
                    print(f'удален диалог по ключу {conversation_uuid}')
                else:
                    print(f'Не удалось удалить диалог по ключу {conversation_uuid}')

            # создадим чат для тестирования
            user_dialogs[0] = CLAUDE.create_new_chat()['uuid']
            # попытаемся достучаться до клиента
            if request_without_attachment(0, 'Привет'):
                return None
        except Exception as error:
            print(f'Попытка соединиться с LLM по ключу {cookie} завершилась ошибкой {error}')

    raise FailToConnect('не далось подключиться к LLM')

# создадим декоратор для повторного обращения к клауду
def retry_on_error(max_retries=2):
    """
    функция-декоратор для повторного обращения к ClaudeAPI
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0

            while retries < max_retries:
                try:
                    result = func(*args, **kwargs)
                    # если обращение прошло успешно, выход из цикла
                    break
                except Exception as error:
                    print(f'Попытка {retries + 1} соединиться с LLM завершилась ошибкой: {error}')
                    retries += 1
                    time.sleep(1)  # Подождать некоторое время перед следующей попыткой

            if retries >= max_retries:
                print('Соединиться с Claude не удалось')

            return result
        return wrapper
    return decorator

def get_latest_reply(uuid: str) -> str:
    """
    Функция для получения последнего сообщения от бота
    """
    history = CLAUDE.chat_conversation_history(uuid)
    sorted_entries = sorted(history['chat_messages'],
                            key=lambda entry: datetime.strptime(entry['created_at'],
                                                                '%Y-%m-%dT%H:%M:%S.%f%z'))
    return sorted_entries[-1]['text'] if sorted_entries[-1]['sender'] == 'assistant' else ''

def create_new_dialog(chat_id: str) -> None:
    """
    Функция, которая создает новый чат для нового пользователя
    Сохраняет их в словарь user_dialogs в формате
    {id в Телеграмме: id в Claude}
    при вызове для ранее авторизованного пользователя удаляет старый чат
    """
    if chat_id in user_dialogs:
        conversation_id = user_dialogs[chat_id]
        deleted = CLAUDE.delete_conversation(conversation_id)
        if deleted:
            print(f'Удален старый чат для пользователя {chat_id}')
        else:
            print(f'Не удалось удалить чат {conversation_id}')
    # создание нового чата
    new_chat = CLAUDE.create_new_chat()
    conversation_id = new_chat['uuid']
    user_dialogs[chat_id] = conversation_id
    print(f'Создан новый чат для пользователя {chat_id}')
    return None

@retry_on_error()
def request_without_attachment(chat_id: str, message: str) -> Optional[str]:
    """
    Функция, которая позволяет пользователю
    отправить запрос без вложенного файла
    """
    prompt = message
    if user_dialogs.get(chat_id, False):
        conversation_id = user_dialogs[chat_id]
    else:
        create_new_dialog(chat_id)
        conversation_id = user_dialogs[chat_id]
    CLAUDE.send_message(prompt, conversation_id)
    return get_latest_reply(conversation_id)

# @retry_on_error()
# def request_with_attachment(chat_id: str, text_file_path: str, promt_lang: str) -> None:
#     """
#     Функция, которая позволяет пользователю
#     отправить запрос с вложенным файлом
#     """
#     # создаем новый диалог под новый конспект
#     create_new_dialog(chat_id)
#     promt = promts['promt']
#     conversation_id = user_dialogs[chat_id]
#     CLAUDE.send_message(promt, conversation_id, attachment=text_file_path)
#     response = get_latest_reply(conversation_id)
#     path_to_save = text_file_path.replace('.txt', '_summ.txt')
#     with open(path_to_save, 'w', encoding='utf-8') as file:
#         file.write(response)
#     return None


connect_to_claude()  # подключение к LLM

if __name__ == '__main__':
    print(request_without_attachment(0, 'Какого цвета стопкран в самолете?'))
    print()
    print(request_with_attachment(0, 'test/Never Gonna Give You Up.txt', 'en'))
