from fastapi import APIRouter, HTTPException, Response, Depends
from app.exceptions import CannotAddDataToDatabase, NoDataProvidedForUpdate, UserNotFound
from app.users.auth import authenticate_user, create_access_token, get_password_hash

from app.users.dao import UserDAO
from app.users.dependencies import get_current_user
from app.users.schemas import SUserAuth, SUserRegister, UserUpdate
from app.users.models import Users

router_auth = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

router_users = APIRouter(
    prefix="/users",
    tags=["Пользователи"]
)


@router_auth.post("/register")
async def register_user(user_data: SUserRegister):
    #проверка, что пользователя не существует
    existng_user = await UserDAO.find_one_or_none(email=user_data.email)
    if existng_user:
        raise HTTPException(status_code=500)
    hashed_password = get_password_hash(user_data.password)
    print(f"{user_data.name=}\n{user_data.email=}\n{hashed_password=}")
    new_user = await UserDAO.add(name=user_data.name, email=user_data.email, hash_password=hashed_password)
    if not new_user:
        raise CannotAddDataToDatabase
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}


@router_auth.post("/login")
async def login_user(response: Response, user_data: SUserAuth):
    user = await authenticate_user(user_data.email, user_data.password)
    access_token = create_access_token({"sub": str(user.id)})
    response.set_cookie("purchases_access_token", access_token, httponly=True)
    return {"access_token": access_token}


@router_auth.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie("purchases_access_token")


@router_users.get("/me")
async def read_users_me(current_user: Users = Depends(get_current_user)):
    return current_user


@router_users.get("/{user_id}")
async def read_users_by_id(user_id: int):
    user = await UserDAO.find_one_or_none(id=user_id)
    if not user:
        raise UserNotFound
    return user


@router_users.get("")
async def read_all_users():
    users = await UserDAO.find_all()
    return users


@router_users.delete("/me")
async def delete_users_me(current_user: Users = Depends(get_current_user)):
    user = await UserDAO.find_one_or_none(id=current_user.id)
    if not user:
        raise UserNotFound
    await UserDAO.delete(id=user.id)
    response = Response(status_code=204)
    response.delete_cookie(key="purchases_access_token")
    return response
    

@router_users.delete("/{user_id}", status_code=204)
async def delete_users_by_id(user_id: int):
    user = await UserDAO.find_one_or_none(id=user_id)
    if not user:
        raise UserNotFound
    await UserDAO.delete(id=user.id)


@router_users.patch("/me")
async def update_users_me(
    update_data: UserUpdate,
    current_user: Users = Depends(get_current_user),
):
    # Обновляем только те поля, которые переданы в запросе
    update_dict = update_data.model_dump(exclude_unset=True)  # Исключаем поля со значением None
    if not update_dict:
        raise NoDataProvidedForUpdate
    
    # Обновляем данные пользователя в базе данных
    updated_user = await UserDAO.update(current_user.id, **update_dict)
    if not updated_user:
        raise UserNotFound

    return updated_user




