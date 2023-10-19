from asyncio import (Task, StreamReader, StreamWriter,
                     run, sleep, start_server, create_task,
                     get_running_loop)
from settings import (HOST, PORT, BUFSIZE, USERS, MESSAGES,
                      NUMBER_MESSAGES_GENERAL_CHAT, USERS_OFFLINE,
                      PERIOD_LIFETIME_MESSAGES, LIMIT_MESSAGES,
                      MESSAGE_COUNTER, DATETIME_FORMAT,
                      PERIOD_LIMIT_MESSAGES)
from loggings import logger_server
from aioconsole import aprint
from datetime import datetime, timedelta


class Server:
    """Сервер мессенджера"""
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.task_done_set = set()

    async def start(self):
        """Запуск сервера"""
        try:
            server = await start_server(self.client_connected, self.host, self.port)
            logger_server.info(
                f'Запущен сервер: {self.host}:{self.port}'
            )
            await aprint(f'Запущен сервер: {self.host}:{self.port}')
            await sleep(1)
            update_counter_messages = create_task(self.updating_message_counters())
            self.task_done_set.add(update_counter_messages)
            update_counter_messages.add_done_callback(self.task_done_set.discard)
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            logger_server.error('Работа сервера грубо прервана!')
        finally:
            logger_server.error('Сервер остановлен администратором!')

    async def listen(self, user: 'User'):
        """Прослушивание подключенных соединений"""
        await self.reade_message(user)

    async def client_connected(self, reader: StreamReader, writer: StreamWriter):
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
                if user.name in USERS_OFFLINE:
                    await self.client_reconnect(user)
                else:
                    message = await self.create_message(
                        'Bot',
                        f'Пользователь "{user.name}" уже в чате'
                    )
                    await self.send(user.writer, message)
                    await self.client_connected(user.reader, user.writer)
            else:
                info_message = await self.create_message(
                    'Bot',
                    f'Пользователь {user.name} не найден, '
                    'поэтому зарегистрирован заново!'
                )
                await self.send(user.writer, info_message)
                await self.registration_new_client(user)
        elif response_input == '2':
            user_new = await self.check_login(user)
            if user_new:
                await self.registration_new_client(user_new)
            else:
                return
        elif response_input == 'quit':
            address = user.writer.get_extra_info('peername')
            logger_server.info(f'Подключение {address} сброшено')
            user.writer.close()
            await user.writer.wait_closed()
        else:
            await self.input_selection(user)

    async def client_reconnect(self, user: 'User'):
        """Обработка повторного подключения клиента"""
        for key, values in USERS.items():
            if user.name != values:
                continue
            old_user = key
        USERS.pop(old_user)
        USERS[user] = user.name
        logger_server.info(f'В чат вошел {user.name}')
        timestamp_disconnect = USERS_OFFLINE[user.name]
        USERS_OFFLINE.pop(user.name)
        for message in MESSAGES:
            time_str = message[:19]
            message_time = datetime.strptime(time_str, DATETIME_FORMAT)
            if timestamp_disconnect > message_time:
                continue
            await self.send(user.writer, f'{message}\n')
        logger_server.info(
            f'Пользователю {user.name} отправлены последние '
            'непрочитанные сообщения из общего чата'
        )
        await self.broadcast(
            'Bot',
            f'В чат вошел {user.name}', user.name
        )
        await self.listen(user)

    async def registration_new_client(self, user: 'User'):
        """Регистрация нового пользователя"""
        USERS[user] = user.name
        MESSAGE_COUNTER[user.name] = LIMIT_MESSAGES
        welcome_message = await self.create_message(
            'Bot',
            f'Добро пожаловать в чат, {user.name}! '
            'Команда для выхода: "quit"'
        )
        await self.send(user.writer, welcome_message)
        logger_server.info(f'В чат вошел новый пользователь {user.name}')
        await self.recent_posts(user.writer, user.name)
        await self.broadcast(
            'Bot',
            f'В чат вошел новый пользователь: {user.name}', user.name
        )
        await self.listen(user)

    async def client_disconnect(self, user_name: str):
        """Обработка отключения клиента"""
        logger_server.info(f'Пользователь {user_name} вышел из чата')
        await self.broadcast(
            'Bot',
            f'Пользователь {user_name} вышел из чата'
        )
        timestamp = datetime.now()
        USERS_OFFLINE[user_name] = timestamp

    async def check_login(self, user: 'User'):
        """Проверка доступности нового логина для регистрации"""
        if user.name in USERS.values():
            login_request = await self.create_message(
                'Bot',
                f'К сожалению login "{user.name}" занят'
            )
            await self.send(user.writer, login_request)
            await self.client_connected(user.reader, user.writer)
        else:
            return user

    async def reade_message(self, user: 'User'):
        """Прослушивание и обработка сообщений от клиента"""
        while True:
            data = await user.reader.read(BUFSIZE)
            if not data:
                break
            message = data.decode('utf-8')
            if message == 'quit':
                await self.client_disconnect(user.name)
                user.writer.close()
                await user.writer.wait_closed()
            else:
                name = user.name
                print(f'1= {name}={MESSAGE_COUNTER[name]}')
                if MESSAGE_COUNTER[name] > 0:
                    logger_server.info(
                        f'Входящее сообщение от {name}: {message}'
                    )
                    MESSAGE_COUNTER[name] -= 1
                    print(f'2= {name}={MESSAGE_COUNTER[name]}')
                    await self.broadcast(name, message)
                else:
                    message = await self.create_message(
                        'Bot',
                        'Ваш лимит исходящих сообщений на период '
                        f'{PERIOD_LIMIT_MESSAGES // 60}минут исчерпан!'
                    )
                    await self.send(user.writer, message)
                    logger_server.info(
                        f'Лимит сообщений пользователя {name} исчерпан'
                    )

    async def create_message(self, author: str, message: str) -> str:
        """Формирование тела сообщения"""
        timestamp = datetime.now().strftime(DATETIME_FORMAT)
        message_send = f'{timestamp} | {author} | {message}'
        return message_send

    async def send(self, writer, send_message):
        """Отправка сообщения"""
        writer.write(send_message.encode('utf-8'))

    async def broadcast(self, author: str, message: str, new_user: str = ''):
        """Широковещательная рассылка"""
        message_send = await self.create_message(author, message)
        MESSAGES.append(message_send)
        for user in USERS:
            if USERS[user] in USERS_OFFLINE.keys():
                continue
            if author != USERS[user] != new_user:
                await self.send(user.writer, message_send)
        logger_server.info(f'Широковещательная рассылка: {message_send}')
        remove_message = create_task(self.remove_message(message_send))
        self.task_done_set.add(remove_message)
        remove_message.add_done_callback(self.task_done_set.discard)

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

    async def remove_message(self, message: str):
        """Удаление доставленных сообщений через заданное время"""
        await sleep(PERIOD_LIFETIME_MESSAGES)
        MESSAGES.remove(message)

    async def updating_message_counters(self):
        """Обновление счетчиков сообщений всех юзеров"""
        print('updating_message_counters')
        while True:
            await sleep(PERIOD_LIMIT_MESSAGES)
            if not MESSAGE_COUNTER:
                continue
            print('1= MESSAGE_COUNTER=', MESSAGE_COUNTER)
            for user in MESSAGE_COUNTER:
                MESSAGE_COUNTER[user] = LIMIT_MESSAGES
            print('2= MESSAGE_COUNTER=', MESSAGE_COUNTER)
            timestamp = datetime.now().strftime(DATETIME_FORMAT)
            logger_server.info(
                'Обновление счетчика '
                'сообщений пользователей'
            )
            await self.broadcast(
                'Bot',
                'Ваш лимит исходящих сообщений обновлен: на '
                f'{PERIOD_LIMIT_MESSAGES // 60}минут вам доступно '
                f'{LIMIT_MESSAGES} сообщений'
            )


class User:
    """Модель юзера (клиента)"""
    def __init__(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        name: str,
        password: str
    ) -> None:
        self.reader: StreamReader = reader
        self.writer: StreamWriter = writer
        self.name: str = name
        self.password: str = password


    def reader(self):
        return self.reader

    def writer(self):
        return self.writer

    def name(self):
        return self.name

    def password(self):
        return self.password


if __name__ == '__main__':
    server = Server(HOST, PORT)
    run(server.start())
