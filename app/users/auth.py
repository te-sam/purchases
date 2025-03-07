from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from pydantic import EmailStr

from app.config import settings
from app.exceptions import IncorrectEmailOrPasswordException
from app.users.dao import UserDAO


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:  
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
	to_encode = data.copy() #копирование данных, так как словарь изменяемый тип данных
	expire = datetime.utcnow() + timedelta(days=30) #задаем время жизни токена. utc для разных часовых поясов
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(
		to_encode, settings.SECRET_KEY, settings.ALGORITHM
	)
	return encoded_jwt


async def authenticate_user(email: EmailStr, password: str):
    user = await UserDAO.find_one_or_none(email=email)
    if not (user and verify_password(password, user.hash_password)):
        raise IncorrectEmailOrPasswordException
    return user