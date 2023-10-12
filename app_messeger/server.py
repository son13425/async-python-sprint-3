from asyncio import (Task, StreamReader, StreamWriter,
                     run, sleep, start_server)
from settings import (HOST, PORT, BUFSIZE, USERS, MESSAGES,
                      NUMBER_MESSAGES_GENERAL_CHAT)
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
                f'Запущен сервер: {self.host}:{self.port}'
            )
            await aprint(f'Запущен сервер: {self.host}, {self.port}')
            await sleep(1)
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            logger_server.error('Работа сервера грубо прервана!')
        finally:
            logger_server.error('Сервер остановлен администратором!')

    async def listen(self, reader: StreamReader, writer: StreamWriter):
        """Обработка подключенных соединений"""
        user = await self.client_connected(reader, writer)
        task = Task(self.reade_message(user), name=user.name)
        await task
        Task(self.client_disconnect(task.get_name()))

    async def client_disconnect(self, task_name: str):
        """Обработка отключения клиента"""
        await self.broadcast('Bot', f'Пользователь {task_name} вышел из чата')
        logger_server.info(f'Пользователь {task_name} вышел из чата')


    async def client_connected(self, reader, writer):
        """Обработка нового подключения"""
        address = writer.get_extra_info('peername')
        logger_server.info(f'Новое подключение {address}')
        login_request = await self.create_message('Bot', 'Ваш login:')
        await self.send(writer, login_request)
        data = await reader.read(BUFSIZE)
        name = data.decode('utf-8')
        user = User(reader, writer, name)
        if name in USERS.values():
            for key, values in USERS.items():
                if name == values:
                    USERS.pop(key)
                    USERS[user] = name
                    logger_server.info(f'В чат вошел {name} {address}')
                    await self.broadcast('Bot', f'В чат вошел {name}', name)
                    return user
        USERS[user] = name
        welcome_message = await self.create_message(
            'Bot',
            f'Добро пожаловать в чат, {name}! Команда для выхода: "quit"'
        )
        await self.send(writer, welcome_message)
        await self.recent_posts(writer, name)
        logger_server.info(f'В чат вошел {name} {address}')
        await self.broadcast('Bot', f'В чат вошел новый пользователь: {name}', name)
        return user

    async def reade_message(self, user: 'User'):
        """Прослушивание и обработка сообщений от клиента"""
        while True:
            data = await user.reader.read(BUFSIZE)
            if not data:
                break
            name = user.name
            message = data.decode('utf-8')
            await self.broadcast(name, message)
            logger_server.info(f'Входящее сообщение от {name}: {message}')

    async def send(self, writer, send_message):
        """Отправка сообщения"""
        writer.write(send_message.encode('utf-8'))

    async def broadcast(self, author: str, message: str, new_user: str = ''):
        """Широковещательная рассылка"""
        message_send = await self.create_message(author, message)
        MESSAGES.append(message_send)
        for user in USERS:
            if author != USERS[user] != new_user:
                await self.send(user.writer, message_send)
        logger_server.info(f'Широковещательная рассылка: {message_send}')

    async def create_message(self, author: str, message: str) -> str:
        """Формирование тела сообщения"""
        timestamp = dt.now().strftime('%Y-%m-%d %H:%M')
        message_send = f'{timestamp} | {author} | {message}'
        return message_send

    async def recent_posts(self, writer, user_name):
        """Отправка последних N сообщений"""
        if len(MESSAGES) != 0:
            if len(MESSAGES) < NUMBER_MESSAGES_GENERAL_CHAT:
                list_messages = MESSAGES
            else:
                list_messages = list(
                    MESSAGES[-NUMBER_MESSAGES_GENERAL_CHAT:]
                )
            for message in list_messages:
                await self.send(writer, f'{message}\n')
        logger_server.info(
            f'Пользователю {user_name} отправлены последние сообщения '
            f'({len(list_messages)}) из общего чата'
        )
        return


class User:
    """Модель юзера (клиента)"""
    def __init__(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        name: str
    ) -> None:
        self.reader: StreamReader = reader
        self.writer: StreamWriter = writer
        self.name: str = name

    def reader(self):
        return self.reader

    def writer(self):
        return self.writer

    def name(self):
        return self.name


if __name__ == '__main__':
    server = Server(HOST, PORT)
    run(server.start())
