import os
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

logger = logging.getLogger(__name__)

# Naming convention for Alembic friendliness
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))

# Redis client – initialised lazily in register_extensions()
redis_client = None


def register_extensions(app):
    global redis_client

    data_dir = app.config["DATA_DIR"]
    os.makedirs(data_dir, exist_ok=True)
    db.init_app(app)

    # Redis
    redis_url = app.config.get("REDIS_URL")
    if redis_url:
        try:
            import redis
            redis_client = redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()
            logger.info("Redis connected at %s", redis_url)
        except Exception as exc:
            logger.warning("Redis unavailable (%s) – running without cache", exc)
            redis_client = None

