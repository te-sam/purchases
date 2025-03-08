from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app as fastapi_app
from app.exceptions import TokenAbsentException, UserNotFound

@pytest.mark.parametrize("user_id", [5])
async def test_delete_and_get_users(ac: AsyncClient, user_id: int):
    response = await ac.get(f"/users/{user_id}")
    assert response.status_code == 200
    response = response.json()
    assert response["id"] == user_id

    response = await ac.delete(f"/users/{user_id}")
    assert response.status_code == 204

    response = await ac.get(f"/users/{user_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == UserNotFound.detail


async def test_delete_user_me_and_get_me():
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        await ac.post("auth/login", json={
            "email": "meat3@mail.ru",
            "password": "funball228",
        })
        assert ac.cookies["purchases_access_token"]

        response = await ac.delete("/users/me")
        assert response.status_code == 204

        response = await ac.get("/users/me")
        assert response.status_code == 401
        assert response.json()["detail"] == TokenAbsentException.detail
        assert not ac.cookies.get("purchases_access_token")

