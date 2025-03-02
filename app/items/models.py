from sqlalchemy import Column, Integer, Table, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


item_shares = Table(
    "item_shares",
    Base.metadata,
    Column("customer_id", Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True),
    Column("item_id", Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("amount", Numeric(10, 2), nullable=False),
)


class Items(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    purchase = relationship("Purchases", back_populates="items")
    customers = relationship("Customers", secondary="item_shares", back_populates="items")
