"""Changeded grades table in tasks

Revision ID: 313b3b7cdd8e
Revises: af09e7ee672d
Create Date: 2023-03-23 00:25:09.153375

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '313b3b7cdd8e'
down_revision = 'af09e7ee672d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('grades', sa.Column('task_id', sa.String(), nullable=True))
    op.drop_index('ix_grades_task', table_name='grades')
    op.create_index(op.f('ix_grades_task_id'), 'grades', ['task_id'], unique=False)
    op.drop_constraint('grades_task_fkey', 'grades', type_='foreignkey')
    op.create_foreign_key(None, 'grades', 'tasks', ['task_id'], ['id'])
    op.drop_column('grades', 'task')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('grades', sa.Column('task', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'grades', type_='foreignkey')
    op.create_foreign_key('grades_task_fkey', 'grades', 'tasks', ['task'], ['id'])
    op.drop_index(op.f('ix_grades_task_id'), table_name='grades')
    op.create_index('ix_grades_task', 'grades', ['task'], unique=False)
    op.drop_column('grades', 'task_id')
    # ### end Alembic commands ###
