from dataclasses import dataclass
from datetime import datetime
from typing import Literal


Method = Literal['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS']


@dataclass(frozen=True, slots=True)
class ResponseData:
    url: str
    status: int
    headers: dict
    json: dict
    date: datetime = datetime.now()

    @property
    def time(self) -> int:
        return int(self.date.timestamp())

    def __str__(self) -> str:
        return f'{self.url} > {self.status}'

    def __repr__(self) -> str:
        return f'Response(url={self.url}, status={self.status}, headers={self.headers}, json={self.json}, time={self.time})'


def time_to_json(time: datetime):
    return time.strftime('%H:%M:%S %d-%m-%Y')


def time_from_json(time):
    return datetime.strptime(time, '%H:%M:%S %d-%m-%Y')
