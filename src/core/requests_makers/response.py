from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Any


from .exceptions import ResponseStatusError


Method = Literal['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS']


@dataclass(frozen=True, slots=True)
class ResponseData:
    """
    Класс ответа на запрос:
        - url: URL запроса
        - status: статус код ответа
        - headers: заголовки ответа
        - json: данные ответа в формате json
        - date: дата и время когда пришел ответ: datetime
        - time: время ответа в формате timestamp: int
    """

    url: str
    status: int
    headers: dict
    json: dict
    date: datetime = datetime.now()

    @property
    def time(self) -> int:
        """
        Возвращает время ответа в формате timestamp: int
        """
        return int(self.date.timestamp())

    def raise_for_status(self, not_trigger_codes: list[int] | tuple[int, ...] | None = None) -> None:
        """
        Проверка статуса ответа, если он не 200, 204 вызывается ResponseStatusError
        Можно добавить коды на которые ошибка не будет райзиться.
        """
        if not_trigger_codes is None:
            not_trigger_codes = ()
        if self.status not in {200,204, *not_trigger_codes}:
            raise ResponseStatusError(self.status, self.headers, self.json)

    def __getitem__(self, key: str) -> Any:
        return self.json[key]

    def __str__(self) -> str:
        return f'{self.url} > {self.status}'

    def __repr__(self) -> str:
        return f'Response(url={self.url}, status={self.status}, headers={self.headers}, json={self.json}, time={self.time})'


def time_to_json(time: datetime):
    return time.strftime('%H:%M:%S %d-%m-%Y')


def time_from_json(time):
    return datetime.strptime(time, '%H:%M:%S %d-%m-%Y')
