from fastapi import APIRouter, Depends
from app.customers.dao import CustomerDAO
from app.customers.schemas import CustomerCreate
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


