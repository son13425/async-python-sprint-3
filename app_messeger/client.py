import asyncio
from asyncio import StreamReader, StreamWriter, sleep, gather, open_connection, CancelledError
from settings import HOST, PORT, BUFSIZE
from aioconsole import ainput, aprint
from contextlib import suppress
import logging
from settings import DATETIME_FORMAT, DIR_LOGS, FORMAT_LOGGER
import uuid


UID_CLIENT = str(uuid.uuid4())[-4:]
FILE_LOGGER_CLIENT = DIR_LOGS / f'{UID_CLIENT}-client-log.log'

logging.basicConfig(
    format=FORMAT_LOGGER,
    level=logging.INFO,
    datefmt=DATETIME_FORMAT,
    filename=FILE_LOGGER_CLIENT,
    filemode='a'
)
logger_client = logging.getLogger(f'Клиент {UID_CLIENT}')


class Client:
    """Клиент мессенджера"""
    def __init__(
            self,
            server_host='127.0.0.1',
            server_port=8000
    ):
        self.host = server_host
        self.port = server_port
        self.reader: StreamReader = None
        self.writer: StreamWriter = None

    async def connection(self):
        """Подключение к серверу"""
        try:
            self.reader, self.writer = await open_connection(
                self.host,
                self.port
            )
            logger_client.info(
                f'Подключились к серверу: {self.host}, {self.port}'
            )
            await aprint(f'Подключились к серверу: {self.host}, {self.port}')
            await sleep(1)
            await gather(
                self.send(),
                self.receive()
            )
        except ConnectionError as ConnectionErrore:
            logger_client.error(f'Ошибка подключения: {ConnectionErrore}')
        except TimeoutError as TimeoutErrore:
            logger_client.error(f'Время истекло: {TimeoutErrore}')
        finally:
            logger_client.error(f'Сброс пользователем подключения к серверу: {self.host}, {self.port}')

    async def send(self, message=''):
        """Отправка сообщения"""
        while message != 'quit':
            message = await ainput()
            self.writer.write(message.encode('utf-8'))
            await self.writer.drain()
            logger_client.info(f'Исходящее сообщение: {message}')

    async def receive(self):
        """Получение сообщения"""
        while True:
            data = await self.reader.read(BUFSIZE)
            if not data:
                break
            message = data.decode('utf-8')
            logger_client.info(f'Входящее сообщение: {message}')
            await aprint(f'{message}')
            await sleep(1)


async def main():
    with suppress(CancelledError):
        client = Client(HOST, PORT)
        await client.connection()


if __name__ == '__main__':
    asyncio.run(main())
