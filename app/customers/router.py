from fastapi import APIRouter, Depends

from app.customers.dao import CustomerDAO
from app.customers.schemas import CustomerCreate, CustomersList
from app.exceptions import (AccessDeniedCustomersError, CustomerNotAddedError,
                            CustomerNotFound, NoCustomersInPurchaseError)
from app.users.dependencies import get_current_user
from app.users.models import Users

router_customers = APIRouter(
    prefix="/customers",
    tags=["Покупатели"]
)


@router_customers.post("", status_code=201)
async def add_customer(customer: CustomerCreate, user: Users = Depends(get_current_user)):
    new_customer = await CustomerDAO.add(customer, created_by=user.id)
    return new_customer


@router_customers.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: int, user: Users = Depends(get_current_user)):
    customer = await CustomerDAO.find_one_or_none(id=customer_id)
    if not customer:
        raise CustomerNotFound
    if customer.created_by != user.id:
        raise AccessDeniedCustomersError
    await CustomerDAO.delete(id=customer.id, created_by=user.id)


@router_customers.post("/{purchase_id}", status_code=201)
async def add_customers_to_purchase(purchase_id: int, customers_list: CustomersList, user: Users = Depends(get_current_user)):
    customers = await CustomerDAO.add_customers_to_purchase(purchase_id, customers_list.customers, user.id)
    if not customers:
        raise CustomerNotAddedError
    return customers


@router_customers.delete("/{purchase_id}/{customer_id}", status_code=204)
async def delete_customer_from_purchase(customer_id: int, purchase_id: int, user: Users = Depends(get_current_user)):
    await CustomerDAO.delete_customer_from_purchase(customer_id=customer_id, purchase_id=purchase_id, user_id=user.id)


# GET customers/{purchase_id}
@router_customers.get("/{purchase_id}")
async def get_customers_to_purchase(purchase_id: int, user: Users = Depends(get_current_user)):
    customers = await CustomerDAO.get_customers_to_purchase(purchase_id, user.id)
    return customers


@router_customers.get("")
async def get_customers():
    customers = await CustomerDAO.find_all()
    return customers


# Узнать сколько пользователь должен за покупку
@router_customers.get("/{purchase_id}/shares/{customer_id}")
async def get_customers_share(purchase_id: int, customer_id: int, user: Users = Depends(get_current_user)):
    amount_customer = await CustomerDAO.get_customers_share(purchase_id, customer_id, user.id)
    return amount_customer    

