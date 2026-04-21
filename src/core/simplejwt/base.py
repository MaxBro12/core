import json
import base64
import hmac
import hashlib
import time
from typing import Any
from dataclasses import dataclass

from .exceptions import WrongAlgorithm, InvalidToken


TokenField = dict[str, Any]


@dataclass(frozen=True, slots=True)
class TokenData:
    """
    Данные токена, содержащие заголовки и полезную нагрузку.
    Заголовки headers:
        - alg: алгоритм подписи
        - typ: тип токена - SJWT
    Базовая нагрузка payload:
        - exp: (int) время истечения токена
        - iat: (int) время создания токена
    """
    headers: TokenField
    payload: TokenField


class SimpleJWT:
    """
    Собственная реализация JWT токенов валидирует только токены, созданные с помощью этой библиотеки (SJWT)
    Алгоритмы подписи:
        - HS256
    """
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret = secret_key.encode('utf-8')
        self.alg = algorithm

    @staticmethod
    def __base64_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    @staticmethod
    def __base64_decode(data: str) -> bytes:
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data.encode('utf-8'))

    def __hs256_code(self, data: bytes) -> bytes:
        return hmac.new(
            self.secret,
            data,
            hashlib.sha256
        ).digest()

    def __sign(self, header: str, payload: str) -> str:
        if self.alg == 'HS256':
            signature = self.__hs256_code(f"{header}.{payload}".encode('utf-8'))
        else:
            raise WrongAlgorithm(self.alg)
        return self.__base64_encode(signature)

    def __dump(self, data: TokenField) -> str:
        return self.__base64_encode(
            json.dumps(data, separators=(',', ':')).encode('utf-8')
        )

    @staticmethod
    def __split_token(token: str) -> tuple[str, str, str]:
        try:
            header_encoded, payload_encoded, signature_encoded = token.split('.')
        except ValueError:
            raise InvalidToken("Invalid token format")
        return header_encoded, payload_encoded, signature_encoded

    def __verify_signature(
        self,
        header_encoded: str,
        payload_encoded: str,
        signature_encoded: str,
    ) -> bool:
        """
        Проверяет подпись токена.
        """
        expected_signature = self.__sign(header_encoded, payload_encoded)
        return hmac.compare_digest(expected_signature, signature_encoded)

    def __verify_headers(self, header_encoded: str) -> bool:
        """
        Проверяет заголовки токена:
            - alg: алгоритм подписи (должен совпадать с алгоритмом экземпляра)
            - typ: тип токена (должен быть "SJWT")
        Вернет True, если проверка пройдена успешно.
        """
        header = json.loads(self.__base64_decode(header_encoded))
        return header.get("alg") == self.alg and header.get("typ") == "SJWT"

    def __verify_payload(self, payload: dict) -> bool:
        """
        Проверяет полезную нагрузку токена:
            - iat: время создания токена (должен быть в прошлом)
            - exp: время истечения токена (должен быть в будущем)
        Вернет True, если проверка пройдена успешно.
        """
        frozen_time = time.time()
        return payload.get("exp") is not None \
            and payload.get("iat") is not None \
            and payload['iat'] < frozen_time \
            and payload['exp'] > frozen_time

    def __verify_time(self, payload: dict, valid_time: int) -> bool:
        """
        Проверяет время токена:
            - разница в exp и iat должна быть равна valid_time
        Вернет True, если проверка пройдена успешно.
        """
        return payload['exp'] - payload['iat'] == valid_time

    def create_token(
        self,
        payload: TokenField,
        expire_delta: int = 3600,
        adt_header: TokenField | None = None
    ) -> str:
        """Создает SJWT токен"""
        header = {
            "alg": self.alg,
            "typ": "SJWT"
        }
        if adt_header:
            header.update(adt_header)

        token_payload = payload.copy()
        frozen_time = int(time.time())
        token_payload['exp'] = int(frozen_time + expire_delta) # Время истечения
        token_payload['iat'] = int(frozen_time) # Время создания

        header = self.__dump(header)
        token_payload = self.__dump(token_payload)
        return f"{header}.{token_payload}.{self.__sign(header, token_payload)}"

    def verify_token(
        self,
        token: str,
        valid_time: int | None = None,
        with_signature: bool = True
    ) -> TokenData | None:
        """
        Валидирует токен по заданному алгоритму и секретному ключу.
        Параметры:
            - token: токен для валидации
            - valid_time: время жизни токена в секундах (по умолчанию None - без проверки). Настоятельно рекомендуется устанавливать это значение!
            - with_signature: проверять ли подпись токена (по умолчанию True)
        Возвращает:
            - TokenData: данные токена, если токен валиден, иначе None
        """
        header_encoded, payload_encoded, signature_encoded = self.__split_token(token)
        if with_signature and not self.__verify_signature(
            header_encoded,
            payload_encoded,
            signature_encoded,
        ):
            raise ValueError("Invalid signature")
            return None

        header = json.loads(self.__base64_decode(header_encoded))
        if not self.__verify_headers(header_encoded):
            return None

        payload = json.loads(self.__base64_decode(payload_encoded))

        if not self.__verify_payload(payload):
            return None

        if valid_time and not self.__verify_time(payload, valid_time):
            return None

        return TokenData(
            headers=header,
            payload=payload
        )
