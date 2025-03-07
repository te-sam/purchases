from decimal import Decimal
import pytest
from sqlalchemy import select
from app.customers.dao import CustomerDAO
from app.customers.models import Customers
from app.customers.schemas import CustomerCreate
from app.database import async_session_maker
from app.exceptions import AccessDeniedCustomersError, CustomerNotFound, CustomerNotInPurchaseError, DuplicateRecordError, PurchaseNotFoundError
from app.purchases.dao import purchase_customers


@pytest.mark.parametrize(
    "customer_data, created_by, expected_email",
    [
        (CustomerCreate(name="Иван Иванов", email="ivan@example.com"), 1, "ivan@example.com",),
        (CustomerCreate(name="Петр Петров"), 2, None,),
    ],
)
async def test_add_customer(customer_data, created_by, expected_email):
    # Вызов метода DAO
    new_customer = await CustomerDAO.add(customer_data, created_by)

    # Проверка результата
    assert new_customer is not None
    assert new_customer.id is not None  # Проверяем, что ID был сгенерирован
    assert new_customer.name == customer_data.name
    assert new_customer.email == expected_email
    assert new_customer.created_by == created_by

    # Проверка базы данных
    async with async_session_maker() as session:
        result = await session.execute(select(Customers).where(Customers.id == new_customer.id))
        db_customer = result.scalars().first()

        assert db_customer is not None
        assert db_customer.name == customer_data.name
        assert db_customer.email == expected_email
        assert db_customer.created_by == created_by


@pytest.mark.parametrize(
    "purchase_id, customers, user_id, expected_result, expect_error, error_type",
    [
        (3, [4, 8], 1, {"purchase_id": 3, "customers": [4, 8]}, False, None),  # Успешный случай
        (3, [7], 1, None, True, AccessDeniedCustomersError),  # Клиент не принадлежит пользователю
        (3, [3], 1, None, True, DuplicateRecordError),  # Дубликат клиента
    ],
)
async def test_add_customers_to_purchase(
    purchase_id, customers, user_id, expected_result, expect_error, error_type
):
    if expect_error:
        # Ожидаем ошибку
        with pytest.raises(error_type):
            await CustomerDAO.add_customers_to_purchase(purchase_id, customers, user_id)
    else:
        # Успешное добавление
        result = await CustomerDAO.add_customers_to_purchase(purchase_id, customers, user_id)
        print(result)

        # Проверка результата
        assert result == expected_result

        # Проверка базы данных
        async with async_session_maker() as session:
            query = select(purchase_customers).where(
                (purchase_customers.c.purchase_id == purchase_id) & 
                (purchase_customers.c.customer_id != 3)  # Элемент для проверки дублей
            )
            db_records = (await session.execute(query)).mappings().all()

            # Проверяем, что клиенты добавлены
            assert len(db_records) == len(customers)
            for record in db_records:
                assert record["customer_id"] in customers


@pytest.mark.parametrize(
    "purchase_id, user_id, expected_result, expect_error",
    [
        (1, 2, [{"purchase_name": "Бухич в бане", "customer_names": ["Ильюха", "Кирилл"]}], False),  # Успешный случай
        (999, 1, None, True),  # Несуществующая покупка
    ],
)
async def test_get_customers_to_purchase(purchase_id, user_id, expected_result, expect_error, prepare_database):
    if expect_error:
        # Ожидаем ошибку
        with pytest.raises(PurchaseNotFoundError):
            await CustomerDAO.get_customers_to_purchase(purchase_id, user_id)
    else:
        # Успешное получение клиентов
        result = await CustomerDAO.get_customers_to_purchase(purchase_id, user_id)

        # Проверка результата
        assert result == expected_result

        # Проверка базы данных
        async with async_session_maker() as session:
            query = (
                select(Customers.name)
                .join(purchase_customers, purchase_customers.c.customer_id == Customers.id)
                .where(purchase_customers.c.purchase_id == purchase_id)
            )
            db_customers = (await session.execute(query)).scalars().all()

            # Проверяем, что клиенты в базе данных соответствуют ожидаемым
            assert set(db_customers) == set(expected_result[0]["customer_names"])


@pytest.mark.parametrize(
    "purchase_id, customer_id, user_id, expected_result, expect_error, error_type",
    [
        (1, 5, 2, {"name": "Ильюха", "sum": Decimal("576.12")}, False, None),  # Успешный случай
        (2, 999, 1, None, True, CustomerNotFound),  # Несуществующий клиент
        (999, 2, 1, None, True, PurchaseNotFoundError),  # Несуществующая покупка
        (2, 8, 1, None, True, CustomerNotInPurchaseError),  # Клиент не участвует в покупке
    ],
)
async def test_get_customers_share(purchase_id, customer_id, user_id, expected_result, expect_error, error_type):
    if expect_error:
        with pytest.raises(error_type):
            await CustomerDAO.get_customers_share(purchase_id, customer_id, user_id)
    else:
        result = await CustomerDAO.get_customers_share(purchase_id, customer_id, user_id)
        
        assert result == expected_result