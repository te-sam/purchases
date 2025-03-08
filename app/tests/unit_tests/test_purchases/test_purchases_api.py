from httpx import AsyncClient
import pytest


@pytest.mark.parametrize("purchase_data, expected_status", [
    ({"name": "Посидели на лавочке"}, 201),  # ✅ Успешное создание
    (None, 422),                                     # ❌ Неверные данные
])
async def test_create_new_purchase(authenticated_ac: AsyncClient, purchase_data, expected_status):
    response = await authenticated_ac.post("/purchases", json=purchase_data)
    assert response.status_code == expected_status

    if response.status_code == 201:
        json_response = response.json()
        assert "id" in json_response
        assert json_response["name"] == purchase_data["name"]


@pytest.mark.parametrize("purchase_id, expected_status", [
    (2, 200),  # ✅ Покупка найдена
    (999, 404),  # ❌ Покупка не найдена
    (1, 403),  # ❌ Покупка принадлежит другому пользователю
])
async def test_get_purchase_by_id(authenticated_ac: AsyncClient, purchase_id, expected_status):
    response = await authenticated_ac.get(f"/purchases/{purchase_id}")
    assert response.status_code == expected_status

    if response.status_code == 200:
        json_response = response.json()
        assert "id" in json_response
        assert json_response["id"] == purchase_id
        assert "purchase_name" in json_response
        assert "customer_ids" in json_response
        assert "items" in json_response


@pytest.mark.parametrize(
    "purchase_id, expected_status",
    [
        (9, 204),  # Успешное удаление
        (999, 404),  # Покупка не найдена
        (1, 403),  # Нет доступа к покупке
    ],
)
async def test_delete_purchase_by_id(authenticated_ac: AsyncClient, purchase_id: int, expected_status: int):
    response = await authenticated_ac.delete(f"/purchases/{purchase_id}")
    assert response.status_code == expected_status