from datetime import datetime
from pathlib import Path

from pydantic.v1 import BaseSettings, Field
from user_model import User

# базовая директория
BASE_DIR: Path = Path(__file__).parent


# настройки подключения
class ConnectionSettings(BaseSettings):
    """Настройки подключения"""
    host: str = Field(default='127.0.0.1')
    port: int = Field(default=8000)
    bufsize: int = Field(default=1024)

    class Config:
        allow_mutation = False
        secrets_dir = BASE_DIR / 'secrets'


connect = ConnectionSettings()

# количество доступных новому клиенту последних cообщений из общего чата
NUMBER_MESSAGES_GENERAL_CHAT: int = 20

# период жизни доставленных сообщений
PERIOD_LIFETIME_MESSAGES: int = 3600


# настройки общего чата
# максимальное количество сообщений за период
LIMIT_MESSAGES: int = 20
# период, секунд
PERIOD_LIMIT_MESSAGES: int = 3600

# TO DO
# лимит предупреждений перед баном
# WARNING_LIMIT: int = 3
# период бана
# BAN_PERIOD: int = 4 * 3600


# настройки логгера
# формат даты
DATETIME_FORMAT: str = '%Y-%m-%d_%H-%M-%S'
# формат сообщений логгера
FORMAT_LOGGER: str = (
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
# директория для файлов логов
DIR_LOGS: Path = BASE_DIR / 'logs'
# адрес файла вывода логов сервера
FILE_LOGGER_SERVER: Path = DIR_LOGS / 'server-application-log.log'


# зарегистрированные пользователи общего чата
# {<obj 'User'>: 'user.name'}
USERS: dict[User, str] = {}
# offline-пользователи общего чата
# {<obj 'User'>: <datetime>}
USERS_OFFLINE: dict[User, datetime] = {}
# сообщения общего чата
# [str]
MESSAGES: list[str] = []
# счетчик сообщений пользователя в чате
# {'user.name': int}
MESSAGE_COUNTER: dict[str, int] = {}
