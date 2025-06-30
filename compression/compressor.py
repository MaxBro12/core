from functools import wraps

import zstandard as zstd
from cryptography.fernet import Fernet

from .exceptions import KeyDontLoadException

class Compressor:
    key_aes: bytes | None = None

    def __init__(self, key_aes: bytes | None = None, load_key_file: str | None = None):
        if key_aes is not None:
            self.key_aes = key_aes
        elif load_key_file is not None:
            self.key_aes = self.__load_key(load_key_file)

    @staticmethod
    def __load_key(key_path: str) -> bytes:
        with open(key_path, 'rb') as f:
            return f.read()

    @staticmethod
    def generate_key():
        return Fernet.generate_key()

    @classmethod
    def compress_zstd_str(cls, data: str | bytes) -> bytes:
        return zstd.compress(data)

    @classmethod
    def decompress_zstd_str(cls, data: bytes) -> bytes:
        return zstd.decompress(data)

    @staticmethod
    def __key_aes_required(func):
        @wraps(func)
        def wrap(self, *args, **kwargs):
            if self.key_aes is None:
                raise KeyDontLoadException
            return func(self, *args, **kwargs)
        return wrap

    @__key_aes_required
    def encrypt_aes(self, data: str | bytes, encoder: str = 'utf-8') -> bytes:
        if type(data) is str:
            data = data.encode(encoding=encoder)
        return Fernet(self.key_aes).encrypt(data)

    @__key_aes_required
    def decrypt_aes(self, crypted_data: bytes) -> str | bytes:
        return Fernet(self.key_aes).decrypt(crypted_data)
