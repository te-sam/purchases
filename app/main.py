from fastapi import FastAPI
from app.users.router import router_auth, router_users
from app.purchases.router import router_purchases
from app.customers.router import router_customers

app = FastAPI()

app.include_router(router_auth)
app.include_router(router_users)
app.include_router(router_purchases)
app.include_router(router_customers)