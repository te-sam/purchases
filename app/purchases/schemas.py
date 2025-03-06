from pydantic import BaseModel
from typing import Dict, List

from app.items.schemas import ItemCreate


class PurchaseCreate(BaseModel):
    name: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Шашлыки на даче",
            }
        }
    }