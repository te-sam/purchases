from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Customers(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    email = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    creator = relationship("Users", back_populates="customers")
    purchases = relationship("Purchases", secondary="purchase_customers", back_populates="customers")
    items = relationship("Items", secondary="item_shares", back_populates="customers")
