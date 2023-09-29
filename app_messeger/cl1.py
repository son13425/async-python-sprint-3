import asyncio


async def client(message):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    print(f'Send: {message!r}')
    writer.write(message.encode())

    data = await reader.read()
    print(f'Reseived: {data.decode()!r}')

    print('Close the connection')
    writer.close()

asyncio.run(client('Hello'))
