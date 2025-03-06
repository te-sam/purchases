from sqlalchemy import CheckConstraint, Column, Integer, Numeric, Table, Text, ForeignKey, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base


purchase_customers = Table(
    "purchase_customers",
    Base.metadata,
    Column("purchase_id", Integer, ForeignKey("purchases.id", ondelete="CASCADE"), primary_key=True),
    Column("customer_id", Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("purchase_id", "customer_id", name="uq_purchase_customer") 
)


class Purchases(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    total_amount = Column(Numeric(10, 2))

    creator = relationship("Users", back_populates="purchases")
    customers = relationship("Customers", secondary="purchase_customers", back_populates="purchases")
    items = relationship("Items", back_populates="purchase")

    __table_args__ = (
        CheckConstraint('total_amount >= 0', name='check_total_amount_positive'),
    )
