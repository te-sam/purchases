from sqlalchemy import insert
from app.dao.base import BaseDAO
from app.items.models import Items
from app.items.schemas import ItemCreate
from app.database import async_session_maker


class ItemDAO(BaseDAO):
    model = Items


    @classmethod
    async def add_items_to_purchase(cls, purchase_id: int, items: ItemCreate, user_id: int):
        async with async_session_maker() as session:
            async with session.begin():  # Используем транзакцию
                await cls.check_purchase(purchase_id, user_id, session)

                for item in items:
                    query = insert(Items).values(purchase_id=purchase_id, name=item.name, price=item.price).returning(Items.id)
                    items = await session.execute(query)
                await session.commit()

                return items.mappings().all()
            