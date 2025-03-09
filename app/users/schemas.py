from pydantic import BaseModel, EmailStr


class SUserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Пончик",
                "email": "art.samohwalov@yandex.ru",
                "password": "123456"
            }
        }
    }

class SUserAuth(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "art.samohwalov@yandex.ru",
                "password": "123456"
            }
        }
    }

class UserUpdate(BaseModel):
    email: EmailStr | None = None  # Поле email (необязательное)
    name: str | None = None        # Поле name (необязательное)