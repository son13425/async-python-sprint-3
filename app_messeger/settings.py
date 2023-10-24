from datetime import datetime
from pathlib import Path

from user_model import User

# настройки подключения
HOST: str = '127.0.0.1'
PORT: int = 8000
BUFSIZE: int = 1024

# базовая директория
BASE_DIR: Path = Path(__file__).parent

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
