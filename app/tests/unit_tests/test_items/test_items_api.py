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
@pytest.mark.asyncio
async def test_add_items_to_purchase(authenticated_ac: AsyncClient, request, purchase_id, items, expected_status):
    response = await authenticated_ac.post(f"/items/{purchase_id}", json={"items": items})
    assert response.status_code == expected_status
    

    if response.status_code == 201:
        json_response = response.json()
        assert isinstance(json_response, list)
        assert all("name" in item and "price" in item and "id" in item for item in json_response)