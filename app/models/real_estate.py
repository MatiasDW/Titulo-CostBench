from datetime import datetime
from app.extensiones import db


class RealEstateMetrics(db.Model):
    """
    Stores longitudinal (Append-Only) property market data for Quantum Analysis.
    Focuses on strategic communes in Santiago, measuring Cap Rates and UF/m2.
    """

    __tablename__ = "real_estate_metrics"

    id = db.Column(db.Integer, primary_key=True)
    comuna = db.Column(db.String(100), nullable=False)
    segment_type = db.Column(db.String(50), nullable=False)

    # Valuation & Yield Metrics
    uf_m2 = db.Column(db.Numeric(10, 2), nullable=False)
    gross_cap_rate = db.Column(db.Numeric(6, 4), nullable=False)
    net_cap_rate = db.Column(db.Numeric(6, 4), nullable=False)

    # Market Health Metrics
    vacancy_rate = db.Column(db.Numeric(6, 4), nullable=False)
    days_on_market = db.Column(db.Integer, nullable=False)

    # Temporal Anchor
    run_date = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "comuna": self.comuna,
            "segment_type": self.segment_type,
            "uf_m2": float(self.uf_m2),
            "gross_cap_rate": float(self.gross_cap_rate),
            "net_cap_rate": float(self.net_cap_rate),
            "vacancy_rate": float(self.vacancy_rate),
            "days_on_market": self.days_on_market,
            "run_date": self.run_date.isoformat() if self.run_date else None,
        }
