from typing import List
from fastapi import APIRouter, Depends
from app.customers.schemas import CustomersList
from app.exceptions import CustomerNotAddedError, ItemsNotAddedError, PurchaseNotAddedError
from app.items.schemas import ItemsList
from app.purchases.dao import PurchaseDAO

from app.purchases.schemas import PurchaseCreate
from app.users.dependencies import get_current_user
from app.users.models import Users

router_purchases = APIRouter(
    prefix="/purchases",
    tags=["Покупки"]
)


@router_purchases.post("", status_code=201)
async def create_new_purchase(purchase: PurchaseCreate, user: Users = Depends(get_current_user)):
    if not purchase:
        raise ValueError("purchase is null")
    if not user:
        raise ValueError("user is null")
    try:
        new_purchase = await PurchaseDAO.add(purchase, created_by=user.id)
        if not new_purchase:
            raise PurchaseNotAddedError
        return new_purchase
    except Exception as e:
        raise e

