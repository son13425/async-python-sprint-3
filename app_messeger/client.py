import asyncio
from asyncio import StreamReader, StreamWriter, sleep, gather, open_connection
from settings import HOST, PORT, BUFSIZE
from loggings import logger_client
from aioconsole import ainput, aprint

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
        except KeyboardInterrupt:
            logger_client.error('Подключение к серверу сброшено пользователем!')
            await aprint('Подключение к серверу сброшено пользователем!')
            await sleep(1)
        finally:
            asyncio.ensure_future(asyncio.shield(self.writer.wait_closed()))
            self.writer.close()
            await self.writer.wait_closed()
            logger_client.error(f'Сброс пользователем подключения к серверу: {self.host}, {self.port}')
            await aprint(f'\n Сброс пользователем подключения к серверу: {self.host}, {self.port}')
            await sleep(1)

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


if __name__ == '__main__':
    client = Client(HOST, PORT)
    asyncio.run(client.connection())
