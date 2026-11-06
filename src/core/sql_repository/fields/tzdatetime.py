from datetime import timezone
from sqlalchemy import TypeDecorator, DateTime


class TZDateTime(TypeDecorator):
    """
    Кастомный тип который конвертирует дату в дату с указанием tz
    Использование:
    active_at: Mapped[TZDatetime] = mapped_column(TZDatetime(tz=timezone.UTC))
    """
    impl = DateTime(timezone=True)
    cache_ok = True
    __tz: timezone = timezone.utc
    
    def __init__(self, tz: timezone = timezone.utc, *args, **kwargs) -> None:
        self.__tz = tz
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=self.__tz)
            else:
                value = value.astimezone(self.__tz)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=self.__tz)
        return value

