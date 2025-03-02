from app.customers.models import Customers
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.customers.schemas import CustomerCreate
from app.customers.models import Customers

class CustomerDAO(BaseDAO):
    model = Customers


    @classmethod
    async def add(cls, customer_data: CustomerCreate, created_by):
        async with async_session_maker() as session:
            new_customer = Customers(
                name=customer_data.name,
                email = customer_data.email,
                created_by=created_by,
            )
            session.add(new_customer)
            await session.flush()
            await session.commit()
            return new_customer