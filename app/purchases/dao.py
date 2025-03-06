
from sqlalchemy import and_, insert, update, select, func, distinct
from app.dao.base import BaseDAO
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

            await session.commit()
            return new_purchase
        

    @classmethod
    async def get_purchase_by_id(cls, purchase_id: int, user_id: int):
        async with async_session_maker() as session:
            await cls.check_purchase(purchase_id, user_id, session)

            # Подзапрос для получения shares (customer_id) для каждого item
            shares_subquery = (
                select(distinct(item_shares.c.customer_id))
                .where(item_shares.c.item_id == Items.id)
                .scalar_subquery()
            )

            # Основной запрос
            query = (
                select(
                    Purchases.name.label("purchase_name"),
                    func.array_agg(distinct(purchase_customers.c.customer_id)).label("customer_ids"),
                    func.array_agg(
                        func.jsonb_build_object(
                            "name", Items.name,
                            "price", Items.price,
                            "shares", func.array(shares_subquery)
                        ).distinct()  # Убедимся, что элементы в массиве уникальны
                    ).label("items")
                )
                .join(purchase_customers, Purchases.id == purchase_customers.c.purchase_id)
                .join(Items, Purchases.id == Items.purchase_id)
                .where(Purchases.id == purchase_id)
                .group_by(Purchases.id, Purchases.name)
            )

            # Выполнение запроса
            result = await session.execute(query)
            return result.mappings().first()


    @classmethod
    async def update_total_amount(cls, purchase_id: int, total_amount: float):
        async with async_session_maker() as session:
            query = update(Purchases).where(Purchases.id == purchase_id).values(total_amount=total_amount)
            await session.execute(query)
            await session.commit()