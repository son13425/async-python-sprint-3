import logging

from settings import DATETIME_FORMAT, FILE_LOGGER, FORMAT_LOGGER


logging.basicConfig(
    format=FORMAT_LOGGER,
    level=logging.INFO,
    datefmt=DATETIME_FORMAT,
    filename=FILE_LOGGER,
    filemode='a'
)
logger_client = logging.getLogger('Клиент')
logger_server = logging.getLogger('Сервер')
