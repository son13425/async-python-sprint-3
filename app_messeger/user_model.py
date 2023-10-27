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
        self._reader: StreamReader = reader
        self._writer: StreamWriter = writer
        self._name: str = name
        self._password: str = password
        self.time_start: datetime = datetime.now()

    @property
    def reader(
        self
    ) -> StreamReader:
        return self._reader

    @property
    def writer(
        self
    ) -> StreamWriter:
        return self._writer

    @property
    def name(
        self
    ) -> str:
        return self._name

    @property
    def password(
        self
    ) -> str:
        return self._password
