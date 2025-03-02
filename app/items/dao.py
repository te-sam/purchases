from app.dao.base import BaseDAO
from app.items.models import Items, ItemShares


class ItemDAO(BaseDAO):
    model = Items

class ItemDAO(BaseDAO):
    model = ItemShares