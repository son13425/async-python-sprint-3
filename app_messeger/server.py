from asyncio import (Task, StreamReader, StreamWriter,
                     run, sleep, start_server)
from settings import (HOST, PORT, BUFSIZE, USERS, MESSAGES,
                      NUMBER_MESSAGES_GENERAL_CHAT, USERS_OFFLINE,
                      PERIOD_LIFETIME_MESSAGES)
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
            await aprint(f'Запущен сервер: {self.host}:{self.port}')
            await sleep(1)
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            logger_server.error('Работа сервера грубо прервана!')
        finally:
            logger_server.error('Сервер остановлен администратором!')

    async def listen(self, reader: StreamReader, writer: StreamWriter):
        """Обработка подключенных соединений"""
        task_done_set = set()
        user = await self.client_connected(reader, writer)
        task = Task(self.reade_message(user), name=user.name)
        await task
        task_done = Task(self.client_disconnect(task.get_name()))
        task_done_set.add(task_done)
        task_done.add_done_callback(task_done_set.discard)

    async def client_disconnect(self, task_name: str):
        """Обработка отключения клиента"""
        await self.broadcast(
            'Bot',
            f'Пользователь {task_name} вышел из чата'
        )
        logger_server.info(f'Пользователь {task_name} вышел из чата')
        timestamp = dt.now()
        USERS_OFFLINE[task_name] = timestamp

    async def client_reconnect(self, user: 'User'):
        """Обработка повторного подключения клиента"""
        for key, values in USERS.items():
            if user.name != values:
                continue
            old_user = key
        USERS.pop(old_user)
        USERS[user] = user.name
        logger_server.info(f'В чат вошел {user.name}')
        await self.broadcast(
            'Bot',
            f'В чат вошел {user.name}', user.name
        )
        timestamp_disconnect = USERS_OFFLINE[user.name]
        USERS_OFFLINE.pop(user.name)
        for message in MESSAGES:
            time_str = message[:16]
            message_time = dt.strptime(time_str, '%Y-%m-%d %H:%M')
            if timestamp_disconnect > message_time:
                continue
            await self.send(user.writer, f'{message}\n')
        logger_server.info(
            f'Пользователю {user.name} отправлены последние '
            'непрочитанные сообщения из общего чата'
        )

    async def client_connected(self, reader, writer):
        """Обработка подключения"""
        address = writer.get_extra_info('peername')
        logger_server.info(f'Новое подключение {address}')
        login_request = await self.create_message(
            'Bot',
            'Ваш login:'
        )
        await self.send(writer, login_request)
        data = await reader.read(BUFSIZE)
        name = data.decode('utf-8')
        user = User(reader, writer, name)
        await self.input_selection(user)
        return user

    async def input_selection(self, user: 'User'):
        """Выбор пользователем способа входа"""
        input_request = await self.create_message(
            'Bot',
            'Войти: 1; Зарегистрироваться: 2; Выйти: "quit"'
        )
        await self.send(user.writer, input_request)
        data_input = await user.reader.read(BUFSIZE)
        response_input = data_input.decode('utf-8')
        if response_input == '1':
            if user.name in USERS.values():
                await self.client_reconnect(user)
            else:
                info_message = await self.create_message(
                    'Bot',
                    f'Пользователь {user.name} не найден, '
                    'поэтому зарегистрирован заново!'
                )
                await self.send(user.writer, info_message)
                await self.registration_new_client(user)
            return
        elif response_input == '2':
            await self.registration_new_client(user)
            return
        else:
            await self.input_selection(user)

    async def registration_new_client(self, user: 'User'):
        """Регистрация нового пользователя"""
        USERS[user] = user.name
        welcome_message = await self.create_message(
            'Bot',
            f'Добро пожаловать в чат, {user.name}! '
            'Команда для выхода: "quit"'
        )
        await self.send(user.writer, welcome_message)
        await self.recent_posts(user.writer, user.name)
        logger_server.info(f'В чат вошел новый пользователь {user.name}')
        await self.broadcast(
            'Bot',
            f'В чат вошел новый пользователь: {user.name}', user.name
        )
        return

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
        remove_tasks = set()
        message_send = await self.create_message(author, message)
        MESSAGES.append(message_send)
        task = Task(await self.remove_message(message_send))
        remove_tasks.add(task)
        task.add_done_callback(remove_tasks.discard)
        for user in USERS:
            if USERS[user] in USERS_OFFLINE.keys():
                continue
            if author != USERS[user] != new_user:
                await self.send(user.writer, message_send)
        logger_server.info(f'Широковещательная рассылка: {message_send}')

    async def remove_message(self, message: str):
        """Удаление доставленных сообщений через заданное время"""
        await sleep(PERIOD_LIFETIME_MESSAGES)
        MESSAGES.remove(message)

    async def create_message(self, author: str, message: str) -> str:
        """Формирование тела сообщения"""
        timestamp = dt.now().strftime('%Y-%m-%d %H:%M')
        message_send = f'{timestamp} | {author} | {message}'
        return message_send

    async def recent_posts(self, writer, user_name):
        """Отправка последних N сообщений новому пользователю"""
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
