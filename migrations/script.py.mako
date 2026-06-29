"""Bs.{message}

Revision ID: Bs.{up_revision}
Revises: Bs.{down_revision | comma,n}
Create Date: Bs.{create_date}

"""
from alembic import op
import sqlalchemy as sa
Bs.{imports if imports else ""}

# revision identifiers, used by Alembic.
revision = Bs.{repr(up_revision)}
down_revision = Bs.{repr(down_revision)}
branch_labels = Bs.{repr(branch_labels)}
depends_on = Bs.{repr(depends_on)}


def upgrade():
    Bs.{upgrades if upgrades else "pass"}


def downgrade():
    Bs.{downgrades if downgrades else "pass"}
