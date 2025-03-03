from sqlalchemy import func, insert, select
from app.customers.models import Customers
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.customers.schemas import CustomerCreate
from app.customers.models import Customers
from app.exceptions import CustomerNotFound, DuplicateRecordError, PurchaseNotFoundError, UserNotInPurchaseError
from app.purchases.models import Purchases, purchase_customers
from app.items.models import Items, item_shares

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
        
    
    @classmethod
    async def add_customers_to_purchase(cls, purchase_id: int, customers, user_id):
        async with async_session_maker() as session:
            async with session.begin():  # Используем транзакцию
                await cls.check_purchase(purchase_id, user_id, session)

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
    async def get_customers_to_purchase(cls, purchase_id: int, user_id: int):
        async with async_session_maker() as session:
            try:
                await cls.check_purchase(purchase_id, user_id, session)

                query = (
                    select(
                        Purchases.name.label("purchase_name"),
                        func.array_agg(Customers.name).label("customer_names")
                    )
                    .select_from(Purchases)
                    .join(purchase_customers, purchase_customers.c.purchase_id == Purchases.id)
                    .join(Customers, purchase_customers.c.customer_id == Customers.id)
                    .where(purchase_customers.c.purchase_id == purchase_id)
                    .group_by(Purchases.name)
                )
                
                customers = await session.execute(query)
                result = customers.mappings().all()
                
                if not result:
                    raise PurchaseNotFoundError
                
                return result
            except Exception as e:
                await session.rollback()
                # Log the exception here if needed
                raise e

    
    @classmethod
    async def get_customers_share(cls, purchase_id: int, customer_id: int, user_id: int):
        async with async_session_maker() as session:
            await cls.check_purchase(purchase_id, user_id, session)

            query = (
                select(Customers.name)  # Выбираем имя покупателя
                .where(Customers.id == customer_id)
            )

            result = await session.execute(query)
            customer = result.scalars().first()

            if not customer:
                raise CustomerNotFound

            query = (
                select(item_shares.c.customer_id)  # Выбираем customer_id из item_shares
                .join(purchase_customers, purchase_customers.c.customer_id == item_shares.c.customer_id)  # Соединяем с purchase_customers
                .join(Purchases, Purchases.id == purchase_customers.c.purchase_id)  # Соединяем с purchases
                .where(
                    (item_shares.c.customer_id == customer_id) &  # Фильтр по customer_id
                    (Purchases.id == purchase_id)  # Фильтр по purchase_id
                )
            )

            # Выполнение запроса
            result = await session.execute(query)
            customer_ids = result.scalars().all()

            if not customer_ids:
                raise UserNotInPurchaseError

            query = (
                select(
                    Customers.name,  # Выбираем имя покупателя
                    func.sum(item_shares.c.amount)  # Суммируем amount
                )
                .join(Items, Items.id == item_shares.c.item_id)  # Соединяем с items
                .join(Purchases, Purchases.id == Items.purchase_id)  # Соединяем с purchases
                .join(Customers, Customers.id == item_shares.c.customer_id)  # Соединяем с customers
                .where(
                    (Purchases.id == purchase_id) &  # Фильтр по purchase_id
                    (item_shares.c.customer_id == customer_id)  # Фильтр по customer_id
                )
                .group_by(Customers.name)  # Группируем по имени покупателя
            )

            # Выполнение запроса
            result = await session.execute(query)
            return result.mappings().all()