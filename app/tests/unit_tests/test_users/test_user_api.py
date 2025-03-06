from fastapi.testclient import TestClient
from httpx import AsyncClient

async def test_get_users(ac: AsyncClient):
    response = await ac.get("/users")
    assert response.status_code == 200
