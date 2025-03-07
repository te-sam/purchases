from httpx import AsyncClient
import pytest


async def test_get_users(ac: AsyncClient):
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
async def test_login(ac: AsyncClient, login_data, expected_status):
    response = await ac.post("/auth/login", json=login_data)
    assert response.status_code == expected_status

    if response.status_code == 200:
        json_response = response.json()
        assert "access_token" in json_response
        # assert json_response["access_token"] == "bearer"


async def test_logout(ac: AsyncClient):
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