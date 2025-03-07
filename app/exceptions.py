from fastapi import HTTPException, status


class PurchaseException(HTTPException):
    status_code = 500
    detail = ""
    
    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)

class UserAlreadyExistsException(PurchaseException):
    status_code=status.HTTP_409_CONFLICT
    detail="Пользователь уже существует"
        
class IncorrectEmailOrPasswordException(PurchaseException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Неверная почта или пароль"
        
class TokenExpiredException(PurchaseException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Срок действия токена истек"
        
class TokenAbsentException(PurchaseException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Токен отсутствует"
        
class IncorrectTokenFormatException(PurchaseException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Неверный формат токена"
        
class UserIsNotPresentException(PurchaseException):
    status_code=status.HTTP_401_UNAUTHORIZED


class CannotAddDataToDatabase(PurchaseException):
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    detail="Не удалось добавить запись"

class CannotProcessCSV(PurchaseException):
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    detail="Не удалось обработать CSV файл"

class CustomerNotAddedError(PurchaseException):
    status_code=status.HTTP_409_CONFLICT
    detail="Не удалось добавить покупателя"

class CustomerNotFound(PurchaseException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="Покупатель не найден"

class ItemsNotAddedError(PurchaseException):
    status_code=status.HTTP_409_CONFLICT
    detail="Не удалось добавить товар"

class AccessDeniedCustomersError(PurchaseException):
    status_code=status.HTTP_403_FORBIDDEN
    detail="Не удалось добавить покупателя"

class PurchaseNotAddedError(PurchaseException):
    status_code=status.HTTP_403_FORBIDDEN
    detail="Не удалось добавить покупку"

class DuplicateRecordError(PurchaseException):
    status_code=status.HTTP_409_CONFLICT
    detail="Такая запись уже существует"

class AccessDeniedError(PurchaseException):
    status_code=status.HTTP_403_FORBIDDEN
    detail="Нет доступа к покупке"

class PurchaseNotFoundError(PurchaseException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="Покупка не найдена"

class CustomerNotInPurchaseError(PurchaseException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="Покупатель не участвует в покупке"

class NoCustomersInPurchaseError(PurchaseException):
    status_code=status.HTTP_204_NO_CONTENT
    detail="Покупка не содержит покупателей"

