import asyncio
from asyncio import StreamReader, StreamWriter, sleep, start_server
from settings import HOST, PORT, BUFSIZE
from loggings import logger_server
from aioconsole import aprint


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
            logger_server.error('Сервер остановлен администратором!')


    def listen(self):
        """Сервер"""
        pass



if __name__ == '__main__':
    server = Server(HOST, PORT)
    asyncio.run(server.start())
