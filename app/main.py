from fastapi import FastAPI

from app.customers.router import router_customers
from app.items.router import router_items
from app.purchases.router import router_purchases
from app.users.router import router_auth, router_users

app = FastAPI()

app.include_router(router_auth)
app.include_router(router_users)
app.include_router(router_purchases)
app.include_router(router_customers)
app.include_router(router_items)