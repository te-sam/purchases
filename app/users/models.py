from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hash_password = Column(String(255), nullable=False)

    purchases = relationship("Purchases", back_populates="creator")
    customers = relationship("Customers", back_populates="creator")
