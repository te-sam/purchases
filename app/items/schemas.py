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
                        "name": "Колбаски",
                        "price": 100.9,
                        "shares": [5,6]
                    },
                    {
                        "name": "Рулетик",
                        "price": 80,
                        "shares": [6,7,8]
                    },
                ]
            }
        }
    }