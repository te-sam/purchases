import pytest
from httpx import AsyncClient

@pytest.mark.parametrize("item_id, purchase_id", [
    (14, 15)
])
async def test_delete_items_and_get_purchase(authenticated_ac: AsyncClient, item_id: int, purchase_id: int):
    response = await authenticated_ac.get(f"/purchases/{purchase_id}")
    assert response.status_code == 200
    total_amount_before = response.json()["total_amount"]

    response = await authenticated_ac.get(f"/items/{item_id}")
    assert response.status_code == 200
    price = response.json()["price"]

    response = await authenticated_ac.delete(f"/items/{purchase_id}/{item_id}")
    assert response.status_code == 204

    response = await authenticated_ac.get(f"/purchases/{purchase_id}")
    assert response.status_code == 200
    total_amount_after = response.json()["total_amount"]
    assert  round(total_amount_before - price, 2) == total_amount_after
