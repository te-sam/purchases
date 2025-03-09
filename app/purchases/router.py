from fastapi import APIRouter, Depends

from app.exceptions import (AccessDeniedError, NoDataProvidedForUpdate,
                            PurchaseNotAddedError, PurchaseNotFoundError,
                            PurchaseNotUpdatedError, UserNotFound)
from app.purchases.dao import PurchaseDAO
from app.purchases.schemas import PurchaseCreate, PurchaseUpdate
from app.users.dependencies import get_current_user
from app.users.models import Users

router_purchases = APIRouter(
    prefix="/purchases",
    tags=["Покупки"]
)


@router_purchases.post("", status_code=201)
async def create_new_purchase(purchase: PurchaseCreate, user: Users = Depends(get_current_user)):
    if not purchase:
        raise ValueError("purchase is null")
    if not user:
        raise ValueError("user is null")
    try:
        new_purchase = await PurchaseDAO.add(purchase, created_by=user.id)
        if not new_purchase:
            raise PurchaseNotAddedError
        return new_purchase
    except Exception as e:
        raise e
    

@router_purchases.get("/{purchase_id}")
async def get_purchase_by_id(purchase_id: int, user: Users = Depends(get_current_user)):
    purchase = await PurchaseDAO.get_purchase_by_id(purchase_id, user.id)
    return purchase


@router_purchases.delete("/{purchase_id}", status_code=204)
async def delete_purchase_by_id(purchase_id: int, user: Users = Depends(get_current_user)):
    purchase = await PurchaseDAO.find_one_or_none(id=purchase_id)
    if not purchase:
        raise PurchaseNotFoundError
    if purchase.created_by != user.id:
        raise AccessDeniedError
    await PurchaseDAO.delete(id=purchase.id, created_by=user.id)


@router_purchases.patch("/{purchase_id}")
async def update_purchases_by_id(
    purchase_id: int,
    update_data: PurchaseUpdate,
    current_user: Users = Depends(get_current_user),
):  
    purchase = await PurchaseDAO.find_one_or_none(id=purchase_id)
    if not purchase:
        raise PurchaseNotFoundError
    if purchase.created_by != current_user.id:
        raise AccessDeniedError
    # Обновляем только те поля, которые переданы в запросе
    update_dict = update_data.model_dump(exclude_unset=True)  # Исключаем поля со значением None
    if not update_dict:
        raise NoDataProvidedForUpdate
    
    # Обновляем данные пользователя в базе данных
    updated_purchase = await PurchaseDAO.update(purchase_id, created_by=current_user.id, **update_dict)
    if not updated_purchase:
        raise PurchaseNotUpdatedError

    return updated_purchase

