from alembic import context
from sqlalchemy import create_engine

from companion.adapters.postgres.tables import metadata


def run_migrations() -> None:
    """Run migrations against the URL set on the Alembic config."""
    engine = create_engine(context.config.get_main_option("sqlalchemy.url") or "")
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations()
