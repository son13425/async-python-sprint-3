import asyncio
from asyncio.streams import StreamReader, StreamWriter
from settings import HOST, PORT, BUFSIZE
from loggings import logger


async def client_connected(reader: StreamReader, writer: StreamWriter):
    address = writer.get_extra_info('peername')
    logger.info(writer.get_extra_info('sockname'))
    logger.info('Start serving %s', address)

    while True:
        data = await reader.read(BUFSIZE)
        if not data:
            break
        writer.write(data)
        await writer.drain()
    logger.info('Stop serving %s', address)
    writer.close()


async def main(host: str, port: int):
    srv = await asyncio.start_server(client_connected, host, port)

    async with srv:
        await srv.serve_forever()


if __name__ == '__main__':
    asyncio.run(main(HOST, PORT))
