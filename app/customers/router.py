from fastapi import APIRouter, Depends
from app.customers.dao import CustomerDAO
from app.customers.schemas import CustomerCreate, CustomersList
from app.exceptions import CustomerNotAddedError
from app.users.dependencies import get_current_user

from app.users.models import Users


router_customers = APIRouter(
    prefix="/customers",
    tags=["Покупатели"]
)


@router_customers.post("")
async def add_customer(customer: CustomerCreate, user: Users = Depends(get_current_user)):
    new_customer = await CustomerDAO.add(customer, created_by=user.id)
    return new_customer


@router_customers.post("/{purchase_id}", status_code=201)
async def add_customers_to_purchase(purchase_id: int, customers_list: CustomersList, user: Users = Depends(get_current_user)):
    customers = await CustomerDAO.add_customers_to_purchase(purchase_id, customers_list.customers, user.id)
    if not customers:
        raise CustomerNotAddedError
    return {"message": "Покупатели добавлены"}


# GET customers/{purchase_id}
@router_customers.get("/{purchase_id}")
async def get_customers_to_purchase(purchase_id: int, user: Users = Depends(get_current_user)):
    customers = await CustomerDAO.get_customers_to_purchase(purchase_id, user.id)
    if not customers:
        return {"message": "В этой покупке нет покупателей"}
    return customers    


