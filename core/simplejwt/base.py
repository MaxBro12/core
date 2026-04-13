import json
import base64
import hmac
import hashlib
import time
from typing import Dict, Any
from dataclasses import dataclass

from .exceptions import WrongAlgorithm, InvalidToken, SimpleJWTException


PayloadData = Dict[str, Any]


@dataclass(frozen=True, slots=True)
class TokenData:
    headers: PayloadData
    payload: PayloadData


class SimpleJWT:
    """Собственная реализация JWT токенов валидирует только токены, созданные с помощью этой библиотеки"""
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

    def __dump(self, data: PayloadData) -> str:
        return self.__base64_encode(
            json.dumps(data, separators=(',', ':')).encode('utf-8')
        )

    def create_token(
        self,
        payload: PayloadData,
        expire_delta: int = 3600,
        adt_header: PayloadData | None = None
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
        self, token: str,
        valid_time: int | None = None,
        with_signature: bool = True
    ) -> TokenData | None:
        """Валидирует SJWT токен. Не забудьте добавить параметр valid_time для проверки времени жизни токена"""
        try:
            header_encoded, payload_encoded, signature_encoded = token.split('.')
        except ValueError:
            raise InvalidToken()
        if with_signature:
            expected_signature = self.__sign(header_encoded, payload_encoded)
            if not hmac.compare_digest(
                expected_signature,
                signature_encoded,
            ):
                return None

        payload = json.loads(self.__base64_decode(payload_encoded))

        if payload.get('exp') is None or payload['exp'] < time.time():
            return None

        if valid_time and payload['exp'] - payload['iat'] != valid_time:
            return None

        return TokenData(
            headers=json.loads(self.__base64_decode(header_encoded)),
            payload=payload
        )
