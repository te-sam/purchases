from httpx import AsyncClient
import pytest


@pytest.mark.parametrize("customer_data, expected_status", [
    ({"name": "Саныч", "email": "sanich@yandex.ru"}, 201),  # ✅ Успешное создание
    (None, 422),  # ❌ Некорректные данные
])
async def test_add_customer_for_auth(authenticated_ac: AsyncClient, customer_data, expected_status):
    response = await authenticated_ac.post("/customers", json=customer_data)
    assert response.status_code == expected_status

    if response.status_code == 201:
        json_response = response.json()
        assert "id" in json_response
        assert json_response["name"] == customer_data["name"]
        assert json_response["email"] == customer_data["email"]


@pytest.mark.parametrize("customer_data, expected_status", [
    ({"name": "Саныч", "email": "sanich@yandex.ru"}, 401),
    (None, 401), 
])
async def test_add_customer_not_auth(ac: AsyncClient, customer_data, expected_status):
    response = await ac.post("/customers", json=customer_data)
    assert response.status_code == expected_status

    if response.status_code == 201:
        json_response = response.json()
        assert "id" in json_response
        assert json_response["name"] == customer_data["name"]
        assert json_response["email"] == customer_data["email"]


@pytest.mark.parametrize(
    "purchase_id, customers_list, expected_status, expected_response",
    [
        (2, {"customers": [1, 2]}, 409, None),  # Такая запись уже существует
        (2, {"customers": []}, 409, None),  # Не удалось добавить покупателя
        (999, {"customers": [1, 2]}, 404, None),  # Покупка не найдена
        (4, {"customers": [1, 2]}, 403, None),  # Нет доступа к покупке
        (5, {"customers": [1, 2]}, 201, {"purchase_id": 5, "customers": [1, 2]}),  # Успешное создание
    ],
)
async def test_add_customers_to_purchase(authenticated_ac: AsyncClient, purchase_id, customers_list, expected_status, expected_response):
    # Вызов эндпоинта
    response = await authenticated_ac.post(f"/customers/{purchase_id}", json=customers_list)
    print(response.json()) 
    # Проверка статуса ответа
    assert response.status_code == expected_status

    # Проверка тела ответа (если ожидается успешный ответ)
    if expected_status == 201:
        json_response = response.json()
        assert json_response == expected_response


@pytest.mark.parametrize(
    "purchase_id, expected_status, expected_response",
    [
        (1, 403, None),  # Нет доступа
        (2, 200, [{'purchase_name': 'Рыбалка', 'customer_names': ['Соня', 'Кристина', 'Гоша']}]),  # Успешный запрос
        (999, 404, None),  # Покупка не найдена
        (1, 403, None),  # Нет доступа (дубликат для примера)
        (6, 200, []),  # Покупка без покупателей
    ],
)
async def test_get_customers_to_purchase(authenticated_ac: AsyncClient, purchase_id, expected_status, expected_response):
    # Вызов эндпоинта
    response = await authenticated_ac.get(f"/customers/{purchase_id}")
    json_response = response.json()
    print(json_response)
    # Проверка статуса ответа
    assert response.status_code == expected_status

    # Проверка тела ответа
    if response.status_code == 200:
        json_response = response.json()
        assert json_response == expected_response


async def test_a():
    assert 1 ==1


@pytest.mark.parametrize("purchase_id, customer_id, expected_status, expected_response", [
    (2, 2, 200, {"name": "Кристина", "sum": 1149.58}),  # ✅ Успешный запрос
    (2, 999, 404, {"detail": "Покупатель не найден"}),  # ❌ Покупатель не найден
    (2, 4, 404, {"detail": "Покупатель не участвует в покупке"}),  # ❌ Покупатель не участвует
    (999, 2, 404, {"detail": "Покупка не найдена"}),  # ❌ Покупка не найдена
    (1, 2, 403, {"detail": "Нет доступа к покупке"}),  # ❌ Нет доступа к покупке
])
async def test_get_customers_share(authenticated_ac: AsyncClient, purchase_id, customer_id, expected_status, expected_response):
    response = await authenticated_ac.get(f"/customers/{purchase_id}/shares/{customer_id}")
    print(response.json())

    assert response.status_code == expected_status
    assert response.json() == expected_response