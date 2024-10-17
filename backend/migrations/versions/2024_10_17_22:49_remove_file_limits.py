"""remove_file_limits

Revision ID: 737f21ac4fce
Revises: 3b80cc5e7547
Create Date: 2024-10-17 22:49:39.757479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '737f21ac4fce'
down_revision: Union[str, None] = '3b80cc5e7547'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('recipes', 'image',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.TEXT(),
               existing_nullable=True)
    op.alter_column('users', 'avatar',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.TEXT(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'avatar',
               existing_type=sa.TEXT(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)
    op.alter_column('recipes', 'image',
               existing_type=sa.TEXT(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)
    # ### end Alembic commands ###
