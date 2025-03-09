from sqlalchemy import delete, insert, select

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.exceptions import AccessDeniedError, CustomerNotInPurchaseError, ItemsNotFound
from app.items.models import Items, item_shares
from app.items.schemas import ItemCreate
from app.purchases.dao import PurchaseDAO
from app.purchases.models import Purchases, purchase_customers


class ItemDAO(BaseDAO):
    model = Items


    @classmethod
    async def add_items_to_purchase(cls, purchase_id: int, items: ItemCreate, user_id: int):
        async with async_session_maker() as session:
            async with session.begin():  # Используем транзакцию
                await cls.check_purchase(purchase_id, user_id, session)

                added_items = []  # Список для хранения данных о добавленных элементах
                sum = 0 

                for item in items:
                    # Вставляем элемент и возвращаем всю строку
                    query = insert(Items).values(
                        purchase_id=purchase_id,
                        name=item.name,
                        price=item.price
                    ).returning(Items)  # Возвращаем всю строку
                    result = await session.execute(query)
                    added_item = result.scalars().first()  # Преобразуем результат в словарь
                    added_item_dict = {
                        "name": added_item.name,
                        "purchase_id": added_item.purchase_id,
                        "id": added_item.id,
                        "price": added_item.price
                    }
                    added_items.append(added_item_dict)  # Сохраняем добавленный элемент
                    # added_items.append(added_item)  # Сохраняем добавленный элемент

                    # Добавляем связи в item_shares через bulk insert
                    for customer_id in item.shares:
                        # Проверка, что пользоватль участвует в покупке
                        query = select(purchase_customers).where(
                            purchase_customers.c.customer_id == customer_id,
                            purchase_customers.c.purchase_id == purchase_id
                        )
                        result = await session.execute(query)
                        if not result.mappings().first():
                            raise CustomerNotInPurchaseError


                        amount = item.price / len(item.shares)
                        query = insert(item_shares).values({"item_id": added_item.id, "customer_id": customer_id, "amount": amount})
                        await session.execute(query)

                    sum += item.price
                
                # Обновляем сумму покупки
                await PurchaseDAO.add_total_amount(purchase_id, sum)

                await session.commit()

                return added_items  # Возвращаем все добавленные элементы
            

    @classmethod
    async def delete_item_from_purchase(cls, item_id: int, purchase_id: int, user_id: int):
        async with async_session_maker() as session:
            await cls.check_purchase(purchase_id, user_id, session)

            # Проверка, что item существует
            query = select(Items.id).where(Items.id == item_id)
            result = await session.execute(query)
            if not result.mappings().first():
                raise ItemsNotFound

            # Пересчитать total_amount
            query = select(Items.price).where(Items.id == item_id)
            result = await session.execute(query)
            price = result.scalar()
            await PurchaseDAO.add_total_amount(purchase_id, -price)

            # Удаление связи в item_shares
            query = delete(item_shares).where(item_shares.c.item_id == item_id)
            await session.execute(query)

            # Удаление элемента
            query = delete(Items).where(Items.id == item_id)
            await session.execute(query)

            await session.commit()
    
    @classmethod
    async def get_item_by_id(cls, item_id: int, user_id: int):
        async with async_session_maker() as session:
            # Проерка, что item существует
            query = select(Items.id).where(Items.id == item_id)
            result = await session.execute(query)
            if not result.mappings().first():
                raise ItemsNotFound
            
            # Проверка, что Items принадлежит покупке, которая принадлежит пользователю
            """
            SELECT purchases.created_by 
            FROM purchases
            JOIN items ON items.purchase_id = purchases.id 
            WHERE items.id = 7
            """
            query = select(Purchases.created_by).join(Items, Purchases.id == Items.purchase_id).where(Items.id == item_id)
            result = await session.execute(query)
            created_by = result.scalars().first()
            if created_by != user_id:
                raise AccessDeniedError
            
            # Возвращаем item
            query = select(Items.id, Items.name, Items.price, Items.purchase_id).where(Items.id == item_id)
            result = await session.execute(query)
            return result.mappings().one_or_none()