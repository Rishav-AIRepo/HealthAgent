"""Run once on startup to create all SQLite tables."""
from backend.db.database import engine
from backend.db import models


def init_db() -> None:
    models.Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
