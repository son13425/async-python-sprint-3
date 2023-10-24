import logging
import os
from pathlib import Path

from settings import (DATETIME_FORMAT, DIR_LOGS, FILE_LOGGER_SERVER,
                      FORMAT_LOGGER)


def check_dir_logs(url_dir_logs: Path = DIR_LOGS):
    """Проверить существование директории для log-файлов"""
    if os.path.exists(url_dir_logs):
        return
    url_dir_logs.mkdir(exist_ok=True)
    return


check_dir_logs()


logging.basicConfig(
    format=FORMAT_LOGGER,
    level=logging.INFO,
    datefmt=DATETIME_FORMAT,
    filename=FILE_LOGGER_SERVER,
    filemode='a'
)

logger_server = logging.getLogger('Сервер')
