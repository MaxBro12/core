import re

key = "test/{param1}/{param2}"
def extract_path_params(key: str, path: str) -> dict[str, str]:
    """
    Извлекает параметры из пути на основе шаблона с фигурными скобками.
    """
    # Находим все ключи в фигурных скобках
    param_names = re.findall(r'\{(\w+)\}', key)

    if not param_names:
        return {}

    # Создаем regex паттерн, заменяя {param} на capture groups
    pattern = key
    for param_name in param_names:
        pattern = pattern.replace(f'{{{param_name}}}', r'([^/]+)')

    # Добавляем якоря для полного совпадения
    pattern = f'^{pattern}$'

    # Ищем совпадения
    match = re.match(pattern, path)

    if not match:
        raise ValueError(f"Path '{path}' doesn't match pattern '{key}'")

    # Создаем словарь с параметрами
    params = {}
    for i, param_name in enumerate(param_names):
        params[param_name] = match.group(i + 1)

    return params


print(extract_path_params(key, "test/value1/value2"))
