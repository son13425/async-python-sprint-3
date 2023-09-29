from asyncio import transports
import logging
import sys
from asyncio import Protocol, BaseTransport, get_event_loop
from asyncio.streams import StreamReader, StreamWriter
from settings import HOST, PORT


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class Client(Protocol):
    """Клиент месенджера"""

    def connection_made(self, transport: BaseTransport) -> None:
        """Подключение к серверу мессенджера"""
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, message=""):
        """Обработка полученного сообщения"""
        data = message.decode()[:-2]
        print(f'> {data}')

    def send_message(self):
        """Отправить сообщение"""
        while True:
            answer = input('< ')
            if answer:
                self.transport.write((f'{answer} \n').encode())


if __name__ == '__main__':
    # запуск клиента в цикле
    loop = get_event_loop()
    coro = loop.create_server(Client, HOST, PORT)
    server = loop.run_until_complete(coro)

    # работа цикла до момента прерывания пользователем
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('{} - interrupted by the user'.format(
            server.sockets[0].getsockname()
        ))

    # закрыть сервер
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
