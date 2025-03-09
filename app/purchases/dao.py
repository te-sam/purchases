
from decimal import Decimal

from sqlalchemy import and_, distinct, func, insert, select, update

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.items.models import Items, item_shares
from app.purchases.models import Purchases, purchase_customers
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
                    total_amount=0
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
                    Purchases.id,
                    Purchases.name.label("purchase_name"),
                    Purchases.total_amount,
                    func.array_agg(distinct(purchase_customers.c.customer_id)).label("customer_ids"),
                    func.array_agg(
                        func.jsonb_build_object(
                            "name", Items.name,
                            "price", Items.price,
                            "shares", func.array(shares_subquery)
                        ).distinct()  # Убедимся, что элементы в массиве уникальны
                    ).label("items")
                )
                .join(Items, Purchases.id == Items.purchase_id, isouter=True)  # Сначала соединяем с Items
                .join(purchase_customers, Purchases.id == purchase_customers.c.purchase_id, isouter=True)  # LEFT JOIN
                .where(Purchases.id == purchase_id)
                .group_by(Purchases.id, Purchases.name)
            )

            # Выполнение запроса
            result = await session.execute(query)
            result = result.mappings().first()
            print(result)
            return result


    @classmethod
    async def add_total_amount(cls, purchase_id: int, total_amount: float):
        async with async_session_maker() as session:
            query = select(Purchases.total_amount).where(Purchases.id == purchase_id)
            result = await session.execute(query)
            existing_amount = result.scalar()

            updated_amount = Decimal(existing_amount) + Decimal(total_amount)

            query = update(Purchases).where(Purchases.id == purchase_id).values(total_amount=updated_amount)
            await session.execute(query)
            await session.commit()