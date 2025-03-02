from typing import List
from sqlalchemy import func, insert, select, update
from app.customers.models import Customers
from app.customers.schemas import CustomersList
from app.dao.base import BaseDAO
from app.exceptions import AccessDeniedError, DuplicateRecordError, PurchaseNotFoundError
from app.items.models import Items, item_shares
from app.purchases.models import Purchases, purchase_customers
from app.database import async_session_maker
from app.purchases.schemas import PurchaseCreate


class PurchaseDAO(BaseDAO):
    model = Purchases

    @classmethod
    async def add(cls, purchase_data: PurchaseCreate, created_by):
        async with async_session_maker() as session:
            async with session.begin():  # Используем транзакцию
                # Создаем новую покупку
                new_purchase = Purchases(
                    name=purchase_data.name,
                    created_by=created_by,
                )
                session.add(new_purchase)
                await session.flush()  # Получаем `new_purchase.id` без коммита

                # Добавляем участников в purchase_customers через bulk insert
                query = insert(purchase_customers).values([
                    {"purchase_id": new_purchase.id, "customer_id": customer_id}
                    for customer_id in purchase_data.customer_ids
                ])
                await session.execute(query)

                sum_price = 0
                # Добавляем товары и их распределение
                for item in purchase_data.items:
                    new_item = Items(name=item.name, price=item.price, purchase_id=new_purchase.id)
                    session.add(new_item)
                    await session.flush()  # Получаем `new_item.id`

                    # Добавляем связи в item_shares через bulk insert
                    amount = item.price / len(item.shares)
                    query = insert(item_shares).values([
                        {"item_id": new_item.id, "customer_id": customer_id, "amount": amount}
                        for customer_id in item.shares
                    ])
                    await session.execute(query)
                    
                    sum_price += item.price

                query = update(Purchases).where(Purchases.id==new_purchase.id).values(total_amount=sum_price)
                await session.execute(query)

            await session.commit()
            return new_purchase
        

    @classmethod
    async def add_customer_to_purchase(cls, purchase_id: int, customer_id: int, user_id):
        async with async_session_maker() as session:
            async with session.begin():  # Используем транзакцию
                query = select(Purchases.created_by).where(Purchases.id==purchase_id)
                result = await session.execute(query)
                if result.scalars().first() != user_id:
                    raise AccessDeniedError

                query = select(purchase_customers).where(
                    purchase_customers.c.purchase_id == purchase_id,
                    purchase_customers.c.customer_id == customer_id
                )
                result = await session.execute(query)
                if result.mappings().first():
                    raise DuplicateRecordError
        
                query = insert(purchase_customers).values(purchase_id=purchase_id, customer_id=customer_id).returning(customer_id)
                customer = await session.execute(query)
                await session.commit()

                return customer.scalars().first()

    @classmethod
    async def add_customers_to_purchase(cls, purchase_id: int, customers, user_id):
        async with async_session_maker() as session:
            async with session.begin():  # Используем транзакцию
                query = select(Purchases.created_by).where(Purchases.id==purchase_id)
                result = await session.execute(query)
                if result.scalars().first() != user_id:
                    raise AccessDeniedError

                for customer_id in customers:
                    print(type(customer_id))
                    query = select(purchase_customers).where(
                        purchase_customers.c.purchase_id == purchase_id,
                        purchase_customers.c.customer_id == customer_id
                    )
                    result = await session.execute(query)
                    if result.mappings().first():
                        raise DuplicateRecordError
            
                    query = insert(purchase_customers).values(purchase_id=purchase_id, customer_id=customer_id).returning(customer_id)
                    customer = await session.execute(query)
                await session.commit()

                return customer.mappings().all()
            

    @classmethod
    async def get_customers_to_purchase(cls, purchase_id: int):
        async with async_session_maker() as session:
            query = select(Purchases.id).where(Purchases.id==purchase_id)
            purchase = await session.execute(query)
            
            if not purchase.mappings().first():
                raise PurchaseNotFoundError

            query = (
            select(
                Purchases.name.label("purchase_name"),
                func.array_agg(Customers.name).label("customer_names")  # Собираем имена в массив
            )
            .join(purchase_customers, purchase_customers.c.purchase_id == Purchases.id)
            .join(Customers, purchase_customers.c.customer_id == Customers.id)
            .where(purchase_customers.c.purchase_id == purchase_id)
            .group_by(Purchases.name)  # Группируем по названию покупки
        )
            
            customers = await session.execute(query)
            await session.commit()

            return customers.mappings().all()