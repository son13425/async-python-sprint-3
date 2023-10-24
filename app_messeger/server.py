from asyncio import (StreamReader, StreamWriter, create_task, run, sleep,
                     start_server)
from datetime import datetime
from typing import Any

from aioconsole import ainput, aprint

from loggings import logger_server
from settings import (BUFSIZE, DATETIME_FORMAT, HOST, LIMIT_MESSAGES,
                      MESSAGE_COUNTER, MESSAGES, NUMBER_MESSAGES_GENERAL_CHAT,
                      PERIOD_LIFETIME_MESSAGES, PERIOD_LIMIT_MESSAGES, PORT,
                      USERS, USERS_OFFLINE)
from user_model import User


class Server:
    """Сервер мессенджера"""
    def __init__(self, host="127.0.0.1", port=8000) -> None:
        self.host: str = host
        self.port: int = port
        self.task_done_set: set = set()

    async def start(
        self
    ) -> None:
        """Запуск сервера"""
        try:
            server = await start_server(
                self.client_connected,
                self.host, self.port
            )
            logger_server.info(
                f'Запущен сервер: {self.host}:{self.port}'
            )
            await aprint(f'Запущен сервер: {self.host}:{self.port}')
            await sleep(1)
            update_counter_messages = create_task(
                self.updating_message_counters()
            )
            self.task_done_set.add(update_counter_messages)
            update_counter_messages.add_done_callback(
                self.task_done_set.discard
            )
            while True:
                message = await ainput()
                if message != 'quit':
                    continue
                for user in USERS:
                    if user in USERS_OFFLINE:
                        continue
                    await self.send(user.writer, 'quit')
                server.close()
                await server.wait_closed()
                await aprint('Сервер остановлен администратором!')
                await sleep(1)
                logger_server.warning(
                    'Сервер остановлен администратором!'
                )
                break
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            logger_server.error('Работа сервера грубо прервана!')
        finally:
            logger_server.error('Сервер остановлен администратором!')

    async def listen(
        self,
        user: 'User'
    ) -> None:
        """Прослушивание подключенных соединений"""
        await self.reade_message(user)

    async def client_connected(
        self,
        reader: StreamReader,
        writer: StreamWriter
    ) -> None:
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
        password_request = await self.create_message(
            'Bot',
            'пароль: '
        )
        await self.send(writer, password_request)
        data_password = await reader.read(BUFSIZE)
        password = data_password.decode('utf-8')
        user = User(reader, writer, name, password)
        await self.input_selection(user)

    async def input_selection(
        self,
        user: 'User'
    ) -> None:
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
                reg_user_devices = self.get_keys(USERS, str(user.name))
                reg_user_password = reg_user_devices[0].password
                if user.password == reg_user_password:
                    user_devices = len(reg_user_devices)
                    off_user_devices = self.get_users_devices_off(
                        reg_user_devices
                    )
                    user_devices_off = len(off_user_devices)
                    if user_devices == user_devices_off:
                        await self.client_reconnect(
                            user,
                            reg_user_devices,
                            off_user_devices
                        )
                    else:
                        time_reg_user_devices = []
                        for reg_device in reg_user_devices:
                            time_reg_user_devices.append(
                                reg_device.time_start
                            )
                        timestamp = min(time_reg_user_devices)
                        await self.add_client_connect(
                            user,
                            timestamp
                        )
                else:
                    warning_message = await self.create_message(
                        'Bot',
                        'Неверный пароль!'
                    )
                    await self.send(user.writer, warning_message)
                    await self.client_connected(
                        user.reader, user.writer
                    )
            else:
                info_message = await self.create_message(
                    'Bot',
                    f'Пользователь {user.name} не найден, '
                    'поэтому зарегистрирован заново!\n'
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

    async def add_client_connect(
        self,
        user: 'User',
        timestamp: datetime
    ) -> None:
        """
        Обработка подключения ранее зарегистрированного
        пользователя на новом клиенте (на момент подключения
        юзер online на других устройствах)
        """
        name = str(user.name)
        USERS[user] = name
        for message in MESSAGES:
            message_time = self.get_message_time(message)
            if timestamp > message_time:
                continue
            await self.send(user.writer, f'{message}\n')
        logger_server.info(
            f'Аккаунты пользователя {name} синхронизированы'
        )
        await self.listen(user)

    async def client_reconnect(
        self,
        user: 'User',
        reg_user_devices: list['User'],
        off_user_devices: list['User']
    ) -> None:
        """
        Обработка повторного подключения
        ранее зарегистрированного клиента
        (на момент подключения юзер офлайн
        на всех устройствах)
        """
        for reg_user in reg_user_devices:
            USERS.pop(reg_user)
        name = str(user.name)
        USERS[user] = name
        logger_server.info(f'В чат вошел {name}')
        timestamp_disconnect = USERS_OFFLINE[off_user_devices[-1]]
        for off_user in off_user_devices:
            USERS_OFFLINE.pop(off_user)
        for message in MESSAGES:
            message_time = self.get_message_time(message)
            if timestamp_disconnect > message_time:
                continue
            await self.send(user.writer, f'{message}\n')
        logger_server.info(
            f'Пользователю {name} отправлены последние '
            'непрочитанные сообщения из общего чата'
        )
        await self.broadcast(
            'Bot',
            f'В чат вошел {name}',
            new_user=name
        )
        await self.listen(user)

    async def registration_new_client(
        self,
        user: 'User'
    ) -> None:
        """Регистрация нового пользователя"""
        name = str(user.name)
        USERS[user] = name
        MESSAGE_COUNTER[name] = LIMIT_MESSAGES
        welcome_message = await self.create_message(
            'Bot',
            f'Добро пожаловать в чат, {user.name}! '
            f'На {PERIOD_LIMIT_MESSAGES // 60}минут вам доступно '
            f'{LIMIT_MESSAGES} исходящих сообщений. '
            'Команда для выхода: "quit"'
        )
        await self.send(user.writer, welcome_message)
        logger_server.info(
            f'В чат вошел новый пользователь {name}'
        )
        await self.recent_posts(user.writer, name)
        await self.broadcast(
            'Bot',
            f'В чат вошел новый пользователь: {name}',
            name
        )
        await self.listen(user)

    async def client_disconnect(
        self,
        user_name: str
    ) -> None:
        """Обработка выхода клиента из чата"""
        logger_server.info(f'Пользователь {user_name} вышел из чата')
        await self.broadcast(
            'Bot',
            f'Пользователь {user_name} вышел из чата'
        )

    async def check_login(
        self,
        user: 'User'
    ) -> Any:
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

    async def reade_message(
        self,
        user: 'User'
    ) -> None:
        """Прослушивание и обработка сообщений от клиента"""
        while True:
            name = str(user.name)
            data = await user.reader.read(BUFSIZE)
            if not data:
                break
            message = data.decode('utf-8')
            if message == 'quit':
                self.add_user_offline_dict(user)
                reg_user_devices = self.get_keys(USERS, name)
                user_devices = len(reg_user_devices)
                off_user_devices = self.get_users_devices_off(
                    reg_user_devices
                )
                user_devices_off = len(off_user_devices)
                if user_devices == user_devices_off:
                    await self.client_disconnect(name)
                    user.writer.close()
                    await user.writer.wait_closed()
                else:
                    user.writer.close()
                    await user.writer.wait_closed()
            else:
                reg_user_devices = self.get_keys(USERS, name)
                if MESSAGE_COUNTER[name] > 0:
                    logger_server.info(
                        f'Входящее сообщение от {name}: {message}'
                    )
                    MESSAGE_COUNTER[name] -= 1
                    await self.broadcast_user_account(
                        user,
                        reg_user_devices,
                        message
                    )
                    await self.broadcast(name, message)
                else:
                    message_warning = await self.create_message(
                        'Bot',
                        'Ваш лимит исходящих сообщений на период '
                        f'{PERIOD_LIMIT_MESSAGES // 60}минут исчерпан!'
                    )
                    await self.broadcast_user_account(
                        user,
                        reg_user_devices,
                        message
                    )
                    for reg_user_device in reg_user_devices:
                        await self.send(
                            reg_user_device.writer,
                            message_warning
                        )
                    logger_server.info(
                        f'Лимит сообщений пользователя {name} исчерпан'
                    )

    async def create_message(
        self,
        author: str,
        message: str
    ) -> str:
        """Формирование тела сообщения"""
        timestamp = datetime.now().strftime(DATETIME_FORMAT)
        message_send = f'{timestamp} | {author} | {message}'
        return message_send

    async def send(
        self,
        writer,
        send_message
    ) -> None:
        """Отправка сообщения"""
        writer.write(send_message.encode('utf-8'))

    async def broadcast(
        self,
        author: str,
        message: str,
        new_user: str = ''
    ) -> None:
        """Широковещательная рассылка"""
        message_send = await self.create_message(author, message)
        MESSAGES.append(message_send)
        for user in USERS:
            if user in USERS_OFFLINE:
                continue
            if author != USERS[user] != new_user:
                await self.send(user.writer, message_send)
        logger_server.info(
            f'Широковещательная рассылка: {message_send}'
        )
        remove_message = create_task(self.remove_message(message_send))
        self.task_done_set.add(remove_message)
        remove_message.add_done_callback(self.task_done_set.discard)

    async def recent_posts(
        self,
        writer: StreamWriter,
        user_name: str
    ) -> None:
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
                f'Пользователю {user_name} отправлены последние '
                f'сообщения ({len(list_messages)}) из общего чата'
            )
            return
        return

    async def remove_message(
        self,
        message: str
    ) -> None:
        """Удаление доставленных сообщений через заданное время"""
        await sleep(PERIOD_LIFETIME_MESSAGES)
        MESSAGES.remove(message)

    async def updating_message_counters(
        self
    ) -> None:
        """Обновление счетчиков сообщений всех юзеров"""
        while True:
            await sleep(PERIOD_LIMIT_MESSAGES)
            if not MESSAGE_COUNTER:
                continue
            for user in MESSAGE_COUNTER:
                MESSAGE_COUNTER[user] = LIMIT_MESSAGES
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

    async def broadcast_user_account(
        self,
        user: 'User',
        reg_user_devices: list['User'],
        message: str
    ) -> None:
        """
        Рассылает исходящее сообщение с одного устройства
        на все зарегистрированные устройства пользователя
        """
        for user_devices in reg_user_devices:
            if user_devices in USERS_OFFLINE:
                continue
            elif user_devices == user:
                continue
            await self.send(user_devices.writer, message)

    def get_keys(
        self,
        dict: dict,
        value_req: str
    ) -> Any:
        """Возвращает из словаря ключи по значению"""
        list_keys = []
        for key, value in dict.items():
            if value != value_req:
                continue
            list_keys.append(key)
            return list_keys

    def get_users_devices_off(
        self,
        list_users: list['User']
    ) -> list['User']:
        """Возвращает список девайсов пользователя offline"""
        off_user_devices = []
        for user_off in USERS_OFFLINE:
            if user_off not in list_users:
                continue
            off_user_devices.append(user_off)
        return off_user_devices

    def add_user_offline_dict(
        self,
        user: 'User'
    ) -> None:
        """Добавляет устройство пользователя в оффлайн"""
        timestamp = datetime.now()
        USERS_OFFLINE[user] = timestamp

    def get_message_time(
        self,
        message: str
    ):
        """Возвращает время в форме datetime из строки сообщения"""
        time_str = message[:19]
        message_time = datetime.strptime(
            time_str,
            DATETIME_FORMAT
        )
        return message_time


if __name__ == '__main__':
    server = Server(HOST, PORT)
    run(server.start())
