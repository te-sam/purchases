from typing import List
from fastapi import APIRouter, Depends
from app.customers.schemas import CustomersList
from app.exceptions import CustomerNotAddedError
from app.purchases.dao import PurchaseDAO

from app.purchases.schemas import PurchaseCreate
from app.users.dependencies import get_current_user
from app.users.models import Users

router_purchases = APIRouter(
    prefix="/purchases",
    tags=["Покупки"]
)


@router_purchases.post("")
async def create_new_purchase(purchase: PurchaseCreate, user: Users = Depends(get_current_user)):
    new_purchase = await PurchaseDAO.add(purchase, created_by=user.id)
    if not new_purchase:
        return {"message": "Ошибка создания покупки"}  # здесь будет генерация ошибки
    return new_purchase


@router_purchases.post("/{purchase_id}/customers/{customer_id}")
async def add_customer_to_purchase(purchase_id: int, customer_id: int, user: Users = Depends(get_current_user)):
    customer = await PurchaseDAO.add_customer_to_purchase(purchase_id, customer_id, user.id)
    if not customer:
        raise CustomerNotAddedError
    return {"message": "Покупатель добавлен"}


@router_purchases.post("/{purchase_id}/customers")
async def add_customers_to_purchase(purchase_id: int, customers_list: CustomersList, user: Users = Depends(get_current_user)):
    print("Endpoint called")
    print("Received data:", customers_list.dict())  # Должно вывести {'customers': [6]}
    customers = await PurchaseDAO.add_customers_to_purchase(purchase_id, customers_list.customers, user.id)
    if not customers:
        raise CustomerNotAddedError
    return {"message": "Покупатели добавлены"}

# GET /purchases/{purchase_id}/customers/
@router_purchases.get("/{purchase_id}/customers")
async def get_customers_to_purchase(purchase_id: int):
    customers = await PurchaseDAO.get_customers_to_purchase(purchase_id)
    if not customers:
        return {"message": "В этой покупке нет покупателей"}
    return customers