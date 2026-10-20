from pydantic import BaseModel


class Ok(BaseModel):
    ok: bool = False


class Detail(BaseModel):
    """Модель для детальной информации в основном об ошибке."""
    detail: str
