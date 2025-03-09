from typing import List

from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Кирилл",
                "email": "loh@gmail.com"
            }
        }
    }

class CustomersList(BaseModel):
    customers: list[int]

    def __init__(self, **data):
        print("Pydantic parsing:", data)
        super().__init__(**data)