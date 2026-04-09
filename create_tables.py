from app import create_app
from app.extensiones import db
from app.models.ml import MarkovCombination

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Done!")
