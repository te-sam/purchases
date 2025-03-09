import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.parametrize("purchase_id", [13])
async def test_delete_and_get_purchase(authenticated_ac: AsyncClient, purchase_id: int):
    response = await authenticated_ac.get(f"/purchases/{purchase_id}")
    assert response.status_code == 200

    response = await authenticated_ac.delete(f"/purchases/{purchase_id}")
    assert response.status_code == 204

    response = await authenticated_ac.get(f"/purchases/{purchase_id}")
    assert response.status_code == 404


@pytest.mark.parametrize("purchase_id", [14])
async def test_update_and_get_purchase(authenticated_ac: AsyncClient, purchase_id: int):
    response = await authenticated_ac.get(f"/purchases/{purchase_id}")
    assert response.status_code == 200
    name = response.json()["purchase_name"]

    response = await authenticated_ac.patch(f"/purchases/{purchase_id}", json={"name": "Поход в Ленту"})
    assert response.status_code == 200

    response = await authenticated_ac.get(f"/purchases/{purchase_id}")
    assert response.status_code == 200
    assert response.json()["purchase_name"] != name
    assert response.json()["purchase_name"] == "Поход в Ленту"