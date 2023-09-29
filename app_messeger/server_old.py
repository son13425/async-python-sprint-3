import asyncio
from asyncio.streams import StreamReader, StreamWriter
from settings import HOST, PORT, BUFSIZE, USERS, MESSAGES
from loggings import logger
from datetime import datetime as dt


async def accept_connection(address):
    """Обработка нового подключения"""
    reader = StreamReader(address)
    writer = StreamWriter(address)
    # while True:
    #     login_request = 'Ваш login:\n'.encode('utf-8')
    #     writer.write(login_request)
    #     await writer.drain()
    #     name = await reader.read(BUFSIZE)
    #     if not name:
    #         return False
    #     USERS[address] = name
    #     welcome_message = f'Добро пожаловать в чат {name}! Команда для выхода: "quit" \n'.encode('utf-8')
    #     logger.info(f'В чат вошел {name} {address}')
    #     writer.write(welcome_message)
    #     await writer.drain()
    #     general_message = f'В чат вошел {name}'
    #     broadcast('Bot', general_message)
    #     return True


async def client_connected(reader: StreamReader, writer: StreamWriter):
    """Обработка нового подключения"""
    address = writer.get_extra_info('peername')
    logger.info('Новое подключение %s', address)
    login_request = 'Ваш login:\n'.encode('utf-8')
    writer.write(login_request)
    await writer.drain()
    data = await reader.read(BUFSIZE)
    name = data.decode('utf-8')
    USERS[address] = name
    print()
    print(USERS)
    print(MESSAGES)
    print()
    welcome_message = f'Добро пожаловать в чат, {name}! Команда для выхода: "quit" \n'.encode('utf-8')
    logger.info(f'В чат вошел {name} {address}')
    writer.write(welcome_message)
    await writer.drain()
    await broadcast(f'В чат вошел {name}', 'Bot')
    writer.close()
    await writer.wait_closed()


async def broadcast(message: str, author: str):
    """Широковещательная рассылка"""
    timestamp = dt.now().strftime('%Y-%m-%d %H:%M')
    message_send = f'{timestamp} | {author} | {message} \n'.encode('utf-8')
    MESSAGES.append((timestamp, author, message))
    for address in USERS:
        print()
        print(address)
        print(message_send)
        print()
        await send_message(message_send, address)


async def send_message(message, address):
    host, port = address
    print()
    print(host)
    print(port)
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(message)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main(host: str, port: int):
    logger.info('Старт сервера: порт %s', PORT)
    srv = await asyncio.start_server(client_connected, host, port)

    async with srv:
        await srv.serve_forever()


if __name__ == '__main__':
    asyncio.run(main(HOST, PORT))
