import string
from secrets import choice


class UniqueGenerationFailed(Exception):
    def __init__(self):
        super().__init__('Cant create unique string')


def generate_trash_string(length: int):
    ans = ''
    ALPHABET = string.digits + string.ascii_letters
    for _ in range(length):
        ans += choice(ALPHABET)
    return ans


def generate_unique_trash_string(
    length: int,
    existed: list[str] | tuple[str],
    tries: int = 5
) -> str:
    for _ in range(tries):
        t_str = generate_trash_string(length=length)
        if t_str not in existed:
            return t_str
    raise UniqueGenerationFailed
