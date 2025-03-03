from pydantic import BaseModel
from typing import Dict, List

from app.items.schemas import ItemCreate


class PurchaseCreate(BaseModel):
    name: str
    customer_ids: List[int]
    items: List[ItemCreate]

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Шашлыки на даче",
                "customer_ids": [3,4,5],
                "items": [
                    {
                    "name": "Хлеб",
                    "price": 50.0,
                    "shares": [3,4]
                    },
                    {
                    "name": "Мясо",
                    "price": 1000,
                    "shares": [3,4,5]
                    }
                ]
            }
        }
    }