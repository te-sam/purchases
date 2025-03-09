import pytest
from httpx import ASGITransport, AsyncClient

from app.exceptions import NoDataProvidedForUpdate, UserNotFound
from app.main import app as fastapi_app


async def test_read_all_users(ac: AsyncClient):
    response = await ac.get("/users")
    assert response.status_code == 200
    json_response = response.json()

    # Проверяем, что ответ — это список
    assert isinstance(json_response, list)

    columns = ["id", "name", "email", "hash_password"]

    if json_response:  # Если пользователи есть
        user = json_response[0]
        for column in columns:
            assert column in user


@pytest.mark.parametrize("user_data, expected_status", [
    ({"name": "Володя", "email": "volodya@gmail.com", "password": "chernika228"}, 200),
    ({"name": "Кальмар", "email": "test@test.com", "password": "pivo_one_love123"}, 500),
])
async def test_register_user(ac: AsyncClient, user_data, expected_status):
    response = await ac.post("/auth/register", json=user_data)
    assert response.status_code == expected_status

    if response.status_code == 200:
        json_response = response.json()
        assert "id" in json_response
        assert json_response["email"] == user_data["email"]
        assert json_response["name"] == user_data["name"]


@pytest.mark.parametrize("login_data, expected_status", [
    ({"email": "test@test.com", "password": "test"}, 200),  # Успешный вход
    ({"email": "test@test.com", "password": "wrongpassword"}, 401),      # Неверный пароль
    ({"email": "wrong@example.com", "password": "securepassword123"}, 401), # Неверный email
])
async def test_login_user(ac: AsyncClient, login_data, expected_status):
    response = await ac.post("/auth/login", json=login_data)
    assert response.status_code == expected_status

    if response.status_code == 200:
        json_response = response.json()
        assert "access_token" in json_response
        # assert json_response["access_token"] == "bearer"


async def test_logout_user(ac: AsyncClient):
    # Устанавливаем куку перед выходом (симуляция залогиненного состояния)
    ac.cookies.set("purchases_access_token", "test_token")
    assert ac.cookies.get("purchases_access_token") == "test_token"

    # Вызываем logout
    response = await ac.post("/auth/logout")

    # Проверяем успешный статус
    assert response.status_code == 200  # Или другой статус, если так настроено

    # Проверяем, что в заголовках ответа есть Set-Cookie с удалением куки
    cookies = response.headers.get("set-cookie", "")
    print(cookies)
    assert 'purchases_access_token=""' in cookies  # Проверяем, что кука удалена
    assert "Max-Age=0" in cookies or "expires=" in cookies.lower()  # Должно быть истечение срока


@pytest.mark.parametrize("expected_status", [200, 401])
async def test_read_users_me(ac: AsyncClient, expected_status):
    if expected_status == 200:
        login_data = {"email": "test@test.com", "password": "test"}
        response = await ac.post("/auth/login", json=login_data)
        assert response.status_code == 200

    response = await ac.get("/users/me")

    assert response.status_code == expected_status

    if response.status_code == 200:
        json_response = response.json()
        assert "id" in json_response
        assert json_response["email"] == login_data["email"]
        assert "name" in json_response
        assert "hash_password" in json_response


@pytest.mark.parametrize(
    "user_id, expected_status, expected_response",
    [
        (4, 204, None),
        (999, 404, {"detail": UserNotFound.detail}),
    ],
)
async def test_delete_users_by_id(ac: AsyncClient, user_id: int, expected_status: int, expected_response: dict | None):
    response = await ac.delete(f"/users/{user_id}")
    assert response.status_code == expected_status

    if expected_response:
        assert response.json() == expected_response
    else:
        # Для успешного удаления проверяем, что тело ответа пустое
        assert not response.content


@pytest.mark.parametrize(
    "user_id, expected_status, expected_response",
    [
        (2, 200, {"name": "Грандмастер", "email": "art.samohwalov@yandex.ru"}),
        (999, 404, {"detail": UserNotFound.detail}),
    ],
)
async def test_read_users_by_id(ac: AsyncClient, user_id: int, expected_status: int, expected_response: dict | None):
    response = await ac.get(f"/users/{user_id}")
    assert response.status_code == expected_status
    response = response.json()

    if expected_status == 200:
        assert response["id"] == user_id
        assert response["name"] == expected_response["name"]
        assert response["email"] == expected_response["email"]
    else:
        assert response == expected_response


async def test_delete_users_me():
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        await ac.post("auth/login", json={
            "email": "funball@yandex.ru",
            "password": "funball228",
        })
        assert ac.cookies["purchases_access_token"]
        
        response = await ac.delete("/users/me")
        assert response.status_code == 204


@pytest.mark.parametrize(
    "update_data, expected_status, expected_response_key",
    [
        ({"email": "test_update@test.com"}, 200, "email"),  # Меняем только email
        ({"name": "Заядлый тестировщик"}, 200, "name"),  # Меняем только name
        ({"email": "test_full_update@test.com", "name": "Яростный"}, 200, "email"),  # Меняем emal и name
        ({}, 400, "detail"),  # Ничего не меняем
    ],
)
async def test_update_users_me(authenticated_ac: AsyncClient, update_data: dict, expected_status: int, expected_response_key: str):
    response = await authenticated_ac.patch("/users/me", json=update_data)
    assert response.status_code == expected_status

    if response.status_code == 200:
        updated_user = response.json()
        assert updated_user[expected_response_key] == update_data[expected_response_key]
    else:
        assert response.json()[expected_response_key] == NoDataProvidedForUpdate.detail
