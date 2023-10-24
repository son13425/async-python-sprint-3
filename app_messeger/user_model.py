from asyncio import StreamReader, StreamWriter
from datetime import datetime


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
        self.time_start: datetime = datetime.now()

    def reader(
        self
    ) -> StreamReader:
        return self.reader

    def writer(
        self
    ) -> StreamWriter:
        return self.writer

    def name(
        self
    ) -> str:
        return self.name

    def password(
        self
    ) -> str:
        return self.password
