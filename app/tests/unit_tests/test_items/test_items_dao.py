from decimal import Decimal
import pytest
from sqlalchemy import select
from app.exceptions import CustomerNotInPurchaseError
from app.items.dao import ItemDAO
from app.items.models import Items, item_shares
from app.items.schemas import ItemCreate
from app.database import async_session_maker


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

            assert len(db_items) == len(items)
            for db_item, expected_item in zip(db_items, expected_result):
                assert db_item.name == expected_item["name"]
                assert db_item.price == expected_item["price"]

                query = select(item_shares).where(item_shares.c.item_id == db_item.id)
                db_shares = (await session.execute(query)).mappings().all()
                
                assert len(db_shares) == len(expected_item["shares"])

                for share, customer_id in zip(db_shares, expected_item["shares"]):
                    assert share.item_id == db_item.id
                    assert share.customer_id == customer_id
                    assert share.amount == expected_item["amount"]