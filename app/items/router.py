from fastapi import APIRouter, Depends
from app.exceptions import ItemsNotAddedError
from app.items.dao import ItemDAO

from app.items.schemas import ItemsList
from app.users.dependencies import get_current_user
from app.users.models import Users


router_items = APIRouter(
    prefix="/items",
    tags=["Товары"]
)


# POST /items/{purchase_id}
@router_items.post("/{purchase_id}", status_code=201)
async def add_items_to_purchase(purchase_id: int, items_list: ItemsList, user: Users = Depends(get_current_user)):
    items = await ItemDAO.add_items_to_purchase(purchase_id=purchase_id, items=items_list.items, user_id=user.id)
    if not items:
        raise ItemsNotAddedError
    return {"message": "Товары добавлены"}