"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | torepr}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${up_revision | torepr}
down_revision: Union[str, None] = ${down_revision | torepr}
branch_labels: Union[str, Sequence[str], None] = ${branch_labels | torepr}
depends_on: Union[str, Sequence[str], None] = ${depends_on | torepr}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
