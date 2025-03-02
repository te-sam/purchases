from fastapi import APIRouter, HTTPException, Response, Depends
from app.exceptions import CannotAddDataToDatabase
from app.users.auth import authenticate_user, create_access_token, get_password_hash

from app.users.dao import UserDAO
from app.users.dependencies import get_current_user
from app.users.schemas import SUserAuth, SUserRegister
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

@router_users.get("")
async def get_all_users():
    users = await UserDAO.find_all()
    return users