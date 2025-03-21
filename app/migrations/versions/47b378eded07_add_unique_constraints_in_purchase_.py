"""add unique constraints in purchase_customers

Revision ID: 47b378eded07
Revises: 5120c8819e66
Create Date: 2025-03-02 18:29:52.298966

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '47b378eded07'
down_revision: Union[str, None] = '5120c8819e66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('uq_purchase_customer', 'purchase_customers', ['purchase_id', 'customer_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('uq_purchase_customer', 'purchase_customers', type_='unique')
    # ### end Alembic commands ###
