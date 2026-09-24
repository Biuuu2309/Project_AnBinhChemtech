from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.database import Base


def ensure_schema(engine: Engine) -> None:
    """create_all + minimal SQLite column adds for existing prototype DBs."""
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        customer_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(customers)"))}
        if customer_cols:
            if "is_active" not in customer_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))
            if "created_at" not in customer_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN created_at DATETIME"))
            if "updated_at" not in customer_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN updated_at DATETIME"))

        quote_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(quotations)"))}
        if quote_cols and "attempt_count" not in quote_cols:
            conn.execute(text("ALTER TABLE quotations ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0"))
        if quote_cols and "idempotency_key" not in quote_cols:
            conn.execute(text("ALTER TABLE quotations ADD COLUMN idempotency_key VARCHAR(100)"))
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_quotations_idempotency_key "
                    "ON quotations(idempotency_key)"
                )
            )
