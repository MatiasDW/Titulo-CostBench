import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Naming convention for Alembic friendliness
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))

def register_extensions(app):
    data_dir = app.config["DATA_DIR"]
    os.makedirs(data_dir, exist_ok=True)
    db.init_app(app)
