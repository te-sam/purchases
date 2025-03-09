from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.database import async_session_maker
from app.exceptions import AccessDeniedError, CustomerNotInPurchaseError, ItemsNotFound, PurchaseNotFoundError
from app.items.dao import ItemDAO
from app.items.models import Items, item_shares
from app.items.schemas import ItemCreate
from app.purchases.models import Purchases


@pytest.mark.parametrize(
    "purchase_id, items, user_id, expected_result, expect_error, error_type",
    [
        (
            4,  # purchase_id
            [  # items
                ItemCreate(name="Кетчуп", price=Decimal("67.80"), shares=[5, 6]),
                ItemCreate(name="Бананы", price=Decimal("215.52"), shares=[5]),
            ],
            2,  # user_id
            [  # expected_result
                {"name": "Кетчуп", "price": Decimal("67.80"), "shares": [5, 6], "amount": Decimal("33.90")},
                {"name": "Бананы", "price": Decimal("215.52"), "shares": [5], "amount": Decimal("215.52")},
            ],
            False,  # expect_error
            None,  # error_type
        ),
        (
            4,  # purchase_id
            [ItemCreate(name="Лук", price=Decimal("90.0"), shares=[8])],  # items (пользователь 8 не участвует в покупке)
            2,  # user_id
            None,  # expected_result
            True,  # expect_error
            CustomerNotInPurchaseError,  # error_type
        ),
    ],
)
async def test_add_items_to_purchase(
    purchase_id, items, user_id, expected_result, expect_error, error_type
):
    if expect_error:
        # Ожидаем ошибку
        with pytest.raises(error_type):
            await ItemDAO.add_items_to_purchase(purchase_id, items, user_id)
    else:
        async with async_session_maker() as session:
            # Забираем значение цены всей покупки
            query = select(Purchases.total_amount).where(Purchases.id == purchase_id)
            sum_before = Decimal((await session.execute(query)).scalars().first())

        # Успешное добавление элементов
        result = await ItemDAO.add_items_to_purchase(purchase_id, items, user_id)

        # Проверка результата
        assert len(result) == len(expected_result)
        for added_item, expected_item in zip(result, expected_result):
            assert added_item["name"] == expected_item["name"]
            assert added_item["price"]== expected_item["price"]


        # Проверка базы данных
        async with async_session_maker() as session:
            # Проверяем, что элементы добавлены
            query = select(Items).where(Items.purchase_id == purchase_id)
            db_items = (await session.execute(query)).scalars().all()

            sum_purchase = 0
            assert len(db_items) == len(items)
            for db_item, expected_item in zip(db_items, expected_result):
                assert db_item.name == expected_item["name"]
                assert db_item.price == expected_item["price"]
                sum_purchase += db_item.price

                query = select(item_shares).where(item_shares.c.item_id == db_item.id)
                db_shares = (await session.execute(query)).mappings().all()
                
                assert len(db_shares) == len(expected_item["shares"])

                for share, customer_id in zip(db_shares, expected_item["shares"]):
                    assert share.item_id == db_item.id
                    assert share.customer_id == customer_id
                    assert share.amount == expected_item["amount"]
            
            # Проверка обновления итоговой суммы покупки
            query = select(Purchases.total_amount).where(Purchases.id == purchase_id)
            sum_after = (await session.execute(query)).scalars().first()
            assert sum_after - sum_before == sum_purchase


@pytest.mark.parametrize(
    "item_id, purchase_id, user_id, expected_exception",
    [
        (10, 11, 3, None), # Успешное удаление
        (1, 999, 1, PurchaseNotFoundError),  # Покупка не найдена
        (1, 1, 999, AccessDeniedError),  # Нет доступа к покупке
        (999, 2, 1, ItemsNotFound),  # Товар не найден
    ],
)
async def test_delete_item_from_purchase(
    item_id: int,
    purchase_id: int,
    user_id: int,
    expected_exception: Exception | None
):
    if expected_exception:
        with pytest.raises(expected_exception):
            await ItemDAO.delete_item_from_purchase(
                item_id=item_id,
                purchase_id=purchase_id,
                user_id=user_id,
            )
    else:
        # Успешное удаление
        await ItemDAO.delete_item_from_purchase(
            item_id=item_id,
            purchase_id=purchase_id,
            user_id=user_id,
        )

        # Проверяем, что товар удален
        async with async_session_maker() as session:
            query = select(Items).where(Items.id == item_id)
            result = await session.execute(query)
            assert not result.scalars().first()

            # Проверяем, что записи в item_shares удалены
            query = select(item_shares).where(item_shares.c.item_id == item_id)
            result = await session.execute(query)
            assert not result.scalars().first()

            # Проверяем, что total_amount обновлен
            query = select(Purchases.total_amount).where(Purchases.id == purchase_id)
            result = await session.execute(query)
            expected_total_amount = result.scalar()

            query = select(func.sum(Items.price)).where(Items.purchase_id == purchase_id)
            result = await session.execute(query)
            total_amount = result.scalar()
            assert total_amount == expected_total_amount # Проверяем, что total_amount равен сумме цен товаров в покупке