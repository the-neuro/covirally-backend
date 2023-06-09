"""adjust max email length to 35

Revision ID: e28961666fca
Revises: 99c7fb046938
Create Date: 2023-02-24 09:13:35.227651

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76e838d6d8a3'
down_revision = '99c7fb046938'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=35),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'email',
               existing_type=sa.String(length=35),
               type_=sa.VARCHAR(length=128),
               existing_nullable=True)
    # ### end Alembic commands ###
