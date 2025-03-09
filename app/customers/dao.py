from sqlalchemy import delete, func, insert, select, update

from app.customers.models import Customers
from app.customers.schemas import CustomerCreate
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.exceptions import (AccessDeniedCustomersError, CustomerNotFound,
                            CustomerNotInPurchaseError, DuplicateRecordError,
                            NoCustomersInPurchaseError)
from app.items.models import Items, item_shares
from app.purchases.models import Purchases, purchase_customers


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
                if not customers:
                    return None
                
                await cls.check_purchase(purchase_id, user_id, session)

                added_customers = []

                for customer_id in customers:
                    print(f"id покупателя: {customer_id}")
                    # Запрет на добавление чужих пользователей 
                    query = select(Customers.created_by).where(Customers.id == customer_id)
                    result = await session.execute(query)
                    if result.scalars().first() != user_id:
                        raise AccessDeniedCustomersError
                    
                    # Проверка на дубликаты
                    query = select(purchase_customers).where(
                        purchase_customers.c.purchase_id == purchase_id,
                        purchase_customers.c.customer_id == customer_id
                    )
                    result = await session.execute(query)
                    if result.mappings().first():
                        raise DuplicateRecordError
            
                    query = insert(purchase_customers).values(purchase_id=purchase_id, customer_id=customer_id).returning(customer_id)
                    await session.execute(query)
                    added_customers.append(customer_id)
                await session.commit()

                return {"purchase_id": purchase_id, "customers": added_customers}
            

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
                
                return result
            except Exception as e:
                await session.rollback()
                # Log the exception here if needed
                raise e

    
    @classmethod
    async def get_customers_share(cls, purchase_id: int, customer_id: int, user_id: int):
        async with async_session_maker() as session:
            await cls.check_purchase(purchase_id, user_id, session)

            # Проверка, что пользователь существует
            query = (
                select(Customers.name)  # Выбираем имя покупателя
                .where(Customers.id == customer_id)
            )

            result = await session.execute(query)
            customer = result.scalars().first()

            if not customer:
                raise CustomerNotFound

            # Проверка, что пользователь участвует в покупке
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
                raise CustomerNotInPurchaseError

            # Выборка данных
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
            return result.mappings().first()
    
    @classmethod
    async def delete_customer_from_purchase(cls, customer_id: int, purchase_id: int, user_id: int):
        async with async_session_maker() as session:
            await cls.check_purchase(purchase_id, user_id, session)

            # Проверка, что покупатель существует
            query = select(Customers.name).where(Customers.id == customer_id)
            result = await session.execute(query)
            customer = result.scalars().first()
            if not customer:
                raise CustomerNotFound

            # Покупатель не участвует в покупке
            query = select(purchase_customers).where(purchase_customers.c.customer_id == customer_id, purchase_customers.c.purchase_id == purchase_id)
            result = await session.execute(query)
            if not result.mappings().first():
                raise CustomerNotInPurchaseError

            # Получить список item_id, за которые скидывается customer
            query = (
                select(Items.id)
                .join(item_shares, Items.id == item_shares.c.item_id)
                .where(
                    (Items.purchase_id == purchase_id) &
                    (item_shares.c.customer_id == customer_id)
                )
            )
            result = await session.execute(query)
            item_ids = result.scalars().all()

            # Удлаить все записи item_shares для покупателя, который больше не участвует в покупке
            if item_ids:
                query = delete(item_shares).where(item_shares.c.item_id.in_(item_ids), item_shares.c.customer_id == customer_id)
                await session.execute(query)

            # Пересчитать amount в item_shares
            for item_id in item_ids:
                customer_count_subquery = (
                    select(func.count(item_shares.c.customer_id))
                    .where(item_shares.c.item_id == item_id)
                    .group_by(item_shares.c.item_id)
                    .scalar_subquery()
                )

                # Получаем цену товара
                item_price_query = select(Items.price).where(Items.id == item_id)
                item_price = (await session.execute(item_price_query)).scalar()

                # Рассчитываем новое значение amount
                new_amount = item_price / customer_count_subquery

                # Обновляем amount в таблице item_shares
                query = (
                    update(item_shares)
                    .where(item_shares.c.item_id == item_id)
                    .values(amount=new_amount)
                )

                await session.execute(query)

            # Удалить покупателя из purchase_customers
            query = delete(purchase_customers).where(purchase_customers.c.customer_id == customer_id, purchase_customers.c.purchase_id == purchase_id)
            await session.execute(query)
            
            await session.commit() 