from pathlib import Path


# настройки подключения
HOST = '127.0.0.1'
PORT = 8000
BUFSIZE = 1024

# базовая директория
BASE_DIR = Path(__file__).parent

# количество доступных новому клиенту последних cообщений из общего чата
NUMBER_MESSAGES_GENERAL_CHAT = 20

# период жизни доставленных сообщений
PERIOD_LIFETIME_MESSAGES = 3600


## настройки общего чата
# максимальное количество сообщений за период
LIMIT_MESSAGES = 20
# период
PERIOD_LIMIT_MESSAGES = 3600
# лимит предупреждений перед баном
WARNING_LIMIT = 3
# период бана
BAN_PERIOD = 4 * 3600


## настройки логгера
# формат даты
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
# формат сообщений логгера
FORMAT_LOGGER = (
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
# адрес файла вывода логов
FILE_LOGGER = BASE_DIR / 'application-log.log'

USERS = {}
MESSAGES = []
