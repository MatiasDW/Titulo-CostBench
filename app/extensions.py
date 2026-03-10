# Compatibility alias – core.py imports from `app.extensions`
# while the actual module is `app.extensiones`.
from app.extensiones import db, register_extensions, redis_client  # noqa: F401
