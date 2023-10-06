import asyncio
from asyncio import StreamReader, StreamWriter, sleep, start_server
from settings import HOST, PORT, BUFSIZE, USERS, MESSAGES
from loggings import logger_server
from aioconsole import aprint
from datetime import datetime as dt


class Server:
    """Сервер мессенджера"""
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port

    async def start(self):
        """Запуск сервера"""
        try:
            server = await start_server(self.listen, self.host, self.port)
            logger_server.info(
                f'Запущен сервер: {self.host}, {self.port}'
            )
            await aprint(f'Запущен сервер: {self.host}, {self.port}')
            await sleep(1)
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            asyncio.ensure_future(asyncio.shield(server.wait_closed()))
            server.close()
            await server.wait_closed()
            logger_server.error('Сервер остановлен администратором!')
        finally:
            asyncio.ensure_future(asyncio.shield(server.wait_closed()))
            server.close()
            await server.wait_closed()

    async def listen(self, reader: StreamReader, writer: StreamWriter):
        """Обработка подключенных соединений"""
        try:
            await self.client_connected(reader, writer)
        except KeyboardInterrupt:
            asyncio.ensure_future(asyncio.shield(server.wait_closed()))
            server.close()
            await server.wait_closed()
            logger_server.error('Клиент отвалился!')

    async def client_connected(self, reader, writer):
        """Обработка нового подключения"""
        address = writer.get_extra_info('peername')
        logger_server.info('Новое подключение %s', address)
        login_request = 'Ваш login:'
        self.send(writer, 'Bot', login_request)
        data = await reader.read(BUFSIZE)
        name = data.decode('utf-8')
        USERS[address] = name
        welcome_message = f'Добро пожаловать в чат, {name}! Команда для выхода: "quit"'
        self.send(writer, 'Bot', welcome_message)
        logger_server.info(f'В чат вошел {name} {address}')
        self.broadcast(f'В чат вошел {name}', 'Bot')
        await writer.wait_closed()

    def send(self, writer, author, message):
        """Отправка сообщения"""
        timestamp = dt.now().strftime('%Y-%m-%d %H:%M')
        message_send = f'{timestamp} | {author} | {message}'
        MESSAGES.append(message_send)
        writer.write(message_send.encode('utf-8'))
        logger_server.info(f'Исходящее сообщение: {message_send}')

    def broadcast(self, message: str, author: str):
        """Широковещательная рассылка"""
        for address in USERS:
            print()
            print(address)
            # await self.send(message_send, address)


if __name__ == '__main__':
    server = Server(HOST, PORT)
    asyncio.run(server.start())
