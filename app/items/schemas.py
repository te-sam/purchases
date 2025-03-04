from typing import Dict, List
from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    price: float
    shares: List[int]  # {customer_id}

class ItemsList(BaseModel):
    items: List[ItemCreate]

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "name": "Хлеб",
                        "price": 50.99,
                        "shares": [5,6,7,8]
                    },
                    {
                        "name": "Мясо",
                        "price": 1000,
                        "shares": [6,7,8]
                    },
                    {
                        "name": "Пиво",
                        "price": 125,
                        "shares": [5,6]
                    }
                ]
            }
        }
    }