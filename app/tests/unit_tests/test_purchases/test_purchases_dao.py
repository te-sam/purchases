import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.exceptions import AccessDeniedError, PurchaseNotFoundError
from app.purchases.dao import PurchaseDAO
from app.purchases.models import Purchases
from app.purchases.schemas import PurchaseCreate
from app.database import async_session_maker


async def test_add_purchase():
    # Моки данных
    purchase_data = PurchaseCreate(name="Тестовая покупка")
    created_by = 1  # ID пользователя, который создал покупку

    # Вызов функции DAO
    new_purchase = await PurchaseDAO.add(purchase_data, created_by)

    # Проверка результата
    assert new_purchase is not None
    assert new_purchase.id is not None  # Проверяем, что ID был сгенерирован
    assert new_purchase.name == "Тестовая покупка"
    assert new_purchase.created_by == created_by

    # Проверка базы данных
    async with async_session_maker() as session:
        result = await session.execute(select(Purchases).where(Purchases.id == new_purchase.id))
        db_purchase = result.scalars().first()

        assert db_purchase is not None
        assert db_purchase.name == "Тестовая покупка"
        assert db_purchase.created_by == created_by


@pytest.mark.parametrize(
    "purchase_id, user_id, purchase_name, customer_ids, expected_items",
    [
        (2, 1, "Рыбалка", {1, 2, 3}, 
        [
             {"name": "Пиво", "price": 580.00, "shares": {1, 2, 3}}, 
             {"name": "Шашлык", "price": 1350.52, "shares": {2, 3}}, 
             {"name": "Апельсиновый сок", "price": 280.99, "shares": {2}}
        ]),  # Первый случай
        (1, 2, "Бухич в бане", {5, 6}, 
        [
             {"name": "Водка", "price": 357.00, "shares": {5}}, 
             {"name": "Сухарики", "price": 115.23, "shares": {5, 6}}, 
             {"name": "Сигареты", "price": 322.99, "shares": {5, 6}}
        ]
        ),  # Второй случай
    ],
)
async def test_get_purchase_by_id(purchase_id, user_id, purchase_name, customer_ids, expected_items):
    # Вызов функции DAO
    result = await PurchaseDAO.get_purchase_by_id(purchase_id, user_id)

    # Проверка результата
    assert result is not None
    assert result["purchase_name"] == purchase_name
    assert set(result["customer_ids"]) == customer_ids

    # Проверяем элементы
    assert len(result["items"]) == len(expected_items)

    # Проверяем все элементы
    for expected_item in expected_items:
        # Ищем элемент с таким же именем
        actual_item = next(item for item in result["items"] if item["name"] == expected_item["name"])
        
        # Проверяем цену и доли
        assert actual_item["price"] == expected_item["price"]
        assert set(actual_item["shares"]) == expected_item["shares"]


@pytest.mark.parametrize(
    "purchase_id, total_amount, expect_error",
    [
        (1, 1000, False),  # Корректное значение
        (2, -20, True),    # Отрицательное значение (ожидаем ошибку)
    ],
)
async def test_update_total_amount(purchase_id, total_amount, expect_error):
    if expect_error:
        # Ожидаем ошибку IntegrityError
        with pytest.raises(IntegrityError):
            await PurchaseDAO.update_total_amount(purchase_id, total_amount)
    else:
        # Корректное обновление
        await PurchaseDAO.update_total_amount(purchase_id, total_amount)

        # Проверка базы данных
        async with async_session_maker() as session:
            result = await session.execute(select(Purchases).where(Purchases.id == purchase_id))
            db_purchase = result.scalars().first()

            assert db_purchase is not None
            assert db_purchase.total_amount == total_amount



@pytest.mark.parametrize(
"purchase_id, user_id, expect_error, error_type",
[
    (
        2,  # purchase_id
        1,  # user_id
        None,  # expect_error
        None,  # error_type
    ),
    (
        999,  # purchase_id (несуществующая покупка)
        1,  # user_id
        True,  # expect_error
        PurchaseNotFoundError,  # error_type
    ),
    (
        1,  # purchase_id
        1,  # user_id (другой пользователь)
        True,  # expect_error
        AccessDeniedError,  # error_type
    ),
],
)
async def test_check_purchase(purchase_id, user_id, expect_error, error_type):
    # Подготовка тестовых данных
    async with async_session_maker() as session:
        if expect_error:
            # Ожидаем ошибку
            with pytest.raises(error_type):
                await PurchaseDAO.check_purchase(purchase_id, user_id, session)
        else:
            # Успешная проверка
            await PurchaseDAO.check_purchase(purchase_id, user_id, session)