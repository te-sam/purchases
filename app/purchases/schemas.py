from typing import Dict, List

from pydantic import BaseModel

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

class PurchaseUpdate(BaseModel):
    name: str