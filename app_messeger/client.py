import asyncio
import logging
import uuid
from asyncio import (CancelledError, StreamReader, StreamWriter, gather,
                     open_connection, sleep)
from contextlib import suppress

from aioconsole import ainput, aprint
from settings import (BUFSIZE, DATETIME_FORMAT, DIR_LOGS, FORMAT_LOGGER, HOST,
                      PORT)

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
    ) -> None:
        self.host = server_host
        self.port = server_port
        self.reader: StreamReader = None
        self.writer: StreamWriter = None

    async def connection(self) -> None:
        """Подключение к серверу"""
        try:
            self.reader, self.writer = await open_connection(
                self.host,
                self.port
            )
            logger_client.info(
                f'Подключились к серверу: {self.host}:{self.port}'
            )
            await aprint(f'Подключились к серверу: {self.host}:{self.port}')
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
            logger_client.error(
                'Сброс пользователем подключения к серверу: '
                f'{self.host}:{self.port}')

    async def send(self) -> None:
        """Отправка сообщения"""
        while True:
            message = await ainput()
            self.writer.write(message.encode('utf-8'))
            await self.writer.drain()
            logger_client.info(f'Исходящее сообщение: {message}')
            if message == 'quit':
                self.writer.close()
                await self.writer.wait_closed()
                await aprint(
                    'Вышли из чата: соединение с сервером '
                    f'{self.host}:{self.port} сброшено'
                )
                await sleep(1)
                logger_client.warning(
                    'Вышли из чата: соединение с сервером '
                    f'{self.host}:{self.port} сброшено'
                )
                break

    async def receive(self) -> None:
        """Получение сообщения"""
        while True:
            data = await self.reader.read(BUFSIZE)
            if not data:
                break
            message = data.decode('utf-8')
            logger_client.info(f'Входящее сообщение: {message}')
            await aprint(f'{message}')
            await sleep(1)


async def main() -> None:
    """Обработка ошибки прерывания связи"""
    with suppress(CancelledError):
        client = Client(HOST, PORT)
        await client.connection()


if __name__ == '__main__':
    asyncio.run(main())
