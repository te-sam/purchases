from sqlalchemy import insert
from app.dao.base import BaseDAO
from app.items.models import Items, item_shares
from app.items.schemas import ItemCreate
from app.database import async_session_maker


class ItemDAO(BaseDAO):
    model = Items


    @classmethod
    async def add_items_to_purchase(cls, purchase_id: int, items: ItemCreate, user_id: int):
        async with async_session_maker() as session:
            async with session.begin():  # Используем транзакцию
                await cls.check_purchase(purchase_id, user_id, session)

                added_items = []  # Список для хранения данных о добавленных элементах

                for item in items:
                    # Вставляем элемент и возвращаем всю строку
                    query = insert(Items).values(
                        purchase_id=purchase_id,
                        name=item.name,
                        price=item.price
                    ).returning(Items)  # Возвращаем всю строку
                    result = await session.execute(query)
                    added_item = result.mappings().first()  # Преобразуем результат в словарь
                    print(added_item)
                    added_items.append(added_item)  # Сохраняем добавленный элемент

                    # Добавляем связи в item_shares через bulk insert
                    amount = item.price / len(item.shares)
                    query = insert(item_shares).values([
                        {"item_id": added_item["Items"].id, "customer_id": customer_id, "amount": amount}
                        for customer_id in item.shares
                    ])
                    await session.execute(query)

                await session.commit()

                return added_items  # Возвращаем все добавленные элементы
            