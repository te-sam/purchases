from typing import Dict, List
from pydantic import BaseModel

class ItemWithShares(BaseModel):
    name: str
    price: float
    shares: List[int]  # {customer_id}

class ItemCreate(BaseModel):
    name: str
    price: float

class ItemsList(BaseModel):
    items: List[ItemCreate]

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "name": "Хлеб",
                        "price": 50.99,
                    },
                    {
                        "name": "Мясо",
                        "price": 1000,
                    },
                    {
                        "name": "Пиво",
                        "price": 125,
                    }
                ]
            }
        }
    }