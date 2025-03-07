from sqlalchemy import delete, insert, select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session_maker
from app.exceptions import AccessDeniedError, PurchaseNotFoundError
from app.purchases.models import Purchases
# from app.logger import logger


class BaseDAO:
    model = None


    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).filter_by(**filter_by)
            result = await session.execute(query)
            return result.mappings().one_or_none()


    @classmethod
    async def find_all(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).filter_by(**filter_by)
            result = await session.execute(query)
            return result.mappings().all()
    

    @classmethod
    async def add(cls, **data):
        try:
            query = insert(cls.model).values(**data).returning(cls.model.__table__.columns)
            async with async_session_maker() as session:
                result = await session.execute(query)
                await session.commit()
                return result.mappings().first()
        except (SQLAlchemyError, Exception) as e:
            if isinstance(e, SQLAlchemyError):
                msg = "Database Exc: Cannot insert data into table"
            elif isinstance(e, Exception):
                msg = "Unknown Exc: Cannot insert data into table"

            print(msg)
            raise
            # logger.error(msg, extra={"table": cls.model.__tablename__}, exc_info=True)
            return None


    @classmethod
    async def delete(cls, **filter_by):
        async with async_session_maker() as session:
            query = delete(cls.model).filter_by(**filter_by)
            await session.execute(query)
            await session.commit()


    async def check_purchase(purchase_id: int, user_id: int, session):
        query = select(Purchases.created_by).where(Purchases.id==purchase_id)
        result = await session.execute(query)
        result = result.scalars().first()
        if not result:
            raise PurchaseNotFoundError
        
        if result != user_id:
            raise AccessDeniedError