"""Machine Learning models for database storage."""

from datetime import datetime
from app.extensiones import db


class MarkovCombination(db.Model):
    """Stores purely statistical Granger causality and transition matrices for analytical history."""

    __tablename__ = "markov_combinations"

    id = db.Column(db.Integer, primary_key=True)
    predictor = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(50), nullable=False)
    p_value = db.Column(db.Numeric(10, 8), nullable=False)
    lag1_correlation = db.Column(db.Numeric(10, 4), nullable=False)
    transition_matrix = db.Column(db.JSON, nullable=False)
    run_date = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "predictor": self.predictor,
            "target": self.target,
            "p_value": float(self.p_value) if self.p_value is not None else None,
            "lag1_correlation": (
                float(self.lag1_correlation)
                if self.lag1_correlation is not None
                else None
            ),
            "transition_matrix": self.transition_matrix,
            "run_date": self.run_date.isoformat() if self.run_date else None,
        }
