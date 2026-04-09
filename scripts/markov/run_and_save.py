from app import create_app
from app.ml.train.scheduler import trigger_markov_now

app = create_app()

with app.app_context():
    print("Triggering Markov logic to save into the DB...")
    res = trigger_markov_now()
    print("Result:", res)
