import pytest
from httpx import AsyncClient


@pytest.mark.parametrize("purchase_id, items, expected_status", [
    (7, [{"name": "Колбаски", "price": 100.9, "shares": [9, 10]}], 201),  # ✅ Успешное добавление
    (999, [{"name": "Пиво", "price": 80.9, "shares": [1]}], 404),  # ❌ Покупка не найдена
    (7, [{"name": "Чипсы", "price": 50, "shares": [999]}], 404),  # ❌ Покупателя не существует и он не участвует в покупке
    (7, [{"name": "Кальмары", "price": 87.23, "shares": [5,6]}], 404),  # ❌ Покупателя существует, но он не участвует в покупке
    (7, None, 422),  # ❌ Некорректные данные (отправили `None`)
    (1,  [{"name": "Чипсы", "price": 50, "shares": [999]}], 403),  # ❌ Покупка не принадлежит пользователю
])
async def test_add_items_to_purchase(authenticated_ac: AsyncClient, request, purchase_id, items, expected_status):
    response = await authenticated_ac.post(f"/items/{purchase_id}", json={"items": items})
    assert response.status_code == expected_status
    

    if response.status_code == 201:
        json_response = response.json()
        assert isinstance(json_response, list)
        assert all("name" in item and "price" in item and "id" in item for item in json_response)


@pytest.mark.parametrize("purchase_id, item_id, expected_status", [
    (16, 17, 204),  # ✅ Успешное удаление
    (1, 2, 403),  # ❌ Покупка не принадлежит пользователю
    (999, 1, 404),  # ❌ Покупка не найдена
    (2, 999, 404),  # ❌ item не найден
])
async def test_delete_item_from_purchase(authenticated_ac: AsyncClient, purchase_id: int, item_id: int, expected_status):
    response = await authenticated_ac.delete(f"items/{purchase_id}/{item_id}")
    assert response.status_code == expected_status