import re


def parse_line(line: str) -> tuple[str, ...] | None:
    if re.search(r',"([^,]+[\w ]+)",', line):
        return tuple(line.split(','))
