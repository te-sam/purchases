from decimal import Decimal
import pytest
from sqlalchemy import select
from app.customers.dao import CustomerDAO
from app.customers.models import Customers
from app.customers.schemas import CustomerCreate
from pydantic import EmailStr
from app.database import async_session_maker
from app.exceptions import AccessDeniedCustomersError, AccessDeniedError, CustomerNotFound, DuplicateRecordError, PurchaseNotFoundError, UserNotInPurchaseError
from app.purchases.dao import PurchaseDAO, purchase_customers


@pytest.mark.parametrize(
    "customer_data, created_by, expected_email",
    [
        (
            CustomerCreate(name="Иван Иванов", email="ivan@example.com"),  # customer_data
            1,  # created_by
            "ivan@example.com",  # expected_email
        ),
        (
            CustomerCreate(name="Петр Петров"),  # customer_data без email
            2,  # created_by
            None,  # expected_email
        ),
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
        (
            3,  # purchase_id
            [4, 8],  # customers
            1,  # user_id
            [4,8],  # expected_result
            False,  # expect_error
            None,  # error_type
        ),
        (
            3,  # purchase_id
            [7],  # customers (клиент не принадлежит пользователю)
            1,  # user_id
            None,  # expected_result
            True,  # expect_error
            AccessDeniedCustomersError,  # error_type
        ),
        (
            3,  # purchase_id
            [3],  # customers (дубликат)
            1,  # user_id
            None,  # expected_result
            True,  # expect_error
            DuplicateRecordError,  # error_type
        ),
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
        (
            1,  # purchase_id
            2,  # user_id
            [{"purchase_name": "Бухич в бане", "customer_names": ["Ильюха", "Кирилл"]}],  # expected_result
            False,  # expect_error
        ),
        (
            999,  # purchase_id (несуществующая покупка)
            1,  # user_id
            None,  # expected_result
            True,  # expect_error
        ),
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
        (
            1,  # purchase_id
            5,  # customer_id
            2,  # user_id
            [{"name": "Ильюха", "sum": Decimal("576.12")}],  # expected_result
            False,  # expect_error
            None,  # error_type
        ),
        (
            2,  # purchase_id
            999,  # customer_id (несуществующий клиент)
            1,  # user_id
            None,  # expected_result
            True,  # expect_error
            CustomerNotFound,  # error_type
        ),
        (
            999,  # purchase_id (несуществующая покупка)
            2,  # customer_id
            1,  # user_id
            None,  # expected_result
            True,  # expect_error
            PurchaseNotFoundError,  # error_type
        ),
        (
            2,  # purchase_id
            8,  # customer_id (есть, но не участвует в покупке)
            1,  # user_id
            None,  # expected_result
            True,  # expect_error
            UserNotInPurchaseError,  # error_type
        ),
    ],
)
async def test_get_customers_share(purchase_id, customer_id, user_id, expected_result, expect_error, error_type):
    if expect_error:
        with pytest.raises(error_type):
            await CustomerDAO.get_customers_share(purchase_id, customer_id, user_id)
    else:
        result = await CustomerDAO.get_customers_share(purchase_id, customer_id, user_id)
        
        assert result == expected_result