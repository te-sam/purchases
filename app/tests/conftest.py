import json
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert

from app.config import settings
from app.customers.models import Customers
from app.database import Base, async_session_maker, engine
from app.items.models import Items, item_shares
from app.main import app as fastapi_app
from app.purchases.models import Purchases, purchase_customers
from app.users.models import Users


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    # Обязательно убеждаемся, что работаем с тестовой БД
    assert settings.MODE == "TEST"

    async with engine.begin() as conn:
        # Удаление всех заданных нами таблиц из БД
        await conn.run_sync(Base.metadata.drop_all)
        # Добавление всех заданных нами таблиц из БД
        await conn.run_sync(Base.metadata.create_all)

    def open_mock_json(model: str):
        with open(f"app/tests/mock_{model}.json", encoding="utf-8") as file:
            return json.load(file)

    users = open_mock_json("users")
    purchases = open_mock_json("purchases")
    customers = open_mock_json("customers")
    items = open_mock_json("items")
    purchase_customers_model = open_mock_json("purchase_customers")
    item_shares_model = open_mock_json("item_shares")

    for purchase in purchases:
        # SQLAlchemy не принимает дату в текстовом формате, поэтому форматируем к datetime
        purchase["created_at"] = datetime.strptime(purchase["created_at"], "%Y-%m-%d %H:%M:%S.%f")

    async with async_session_maker() as session:
        for Model, values in [
            (Users, users),
            (Purchases, purchases),
            (Customers, customers),
            (Items, items),
            (purchase_customers, purchase_customers_model),
            (item_shares, item_shares_model),
        ]:
            query = insert(Model).values(values)
            await session.execute(query)

        await session.commit()


@pytest.fixture(scope="function")
async def ac():
    "Асинхронный клиент для тестирования эндпоинтов"
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
async def authenticated_ac():
    "Асинхронный аутентифицированный клиент для тестирования эндпоинтов"
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        await ac.post("auth/login", json={
            "email": "test@test.com",
            "password": "test",
        })
        assert ac.cookies["purchases_access_token"]
        yield ac


@pytest.fixture(scope="session")
async def authenticated_ac_2():
    "Асинхронный аутентифицированный клиент для тестирования эндпоинтов"
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        await ac.post("auth/login", json={
            "email": "funball@yandex.ru",
            "password": "funball228",
        })
        assert ac.cookies["purchases_access_token"]
        yield ac