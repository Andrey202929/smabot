from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'signals',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('asset', sa.String(), nullable=False),
        sa.Column('timeframe', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('entry', sa.Float(), nullable=False),
        sa.Column('stop_loss', sa.Float(), nullable=False),
        sa.Column('take_profit', sa.Float(), nullable=False),
        sa.Column('rr', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('quality', sa.String(), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.UniqueConstraint('fingerprint')
    )

    op.create_table(
        'results',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('signal_id', sa.UUID(), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('exit_price', sa.Float()),
        sa.Column('pnl', sa.Float()),
        sa.Column('rr_realized', sa.Float()),
        sa.Column('win', sa.Boolean()),
    )

    op.create_table(
        'statistics',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('period', sa.String(), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('statistics')
    op.drop_table('results')
    op.drop_table('signals')
