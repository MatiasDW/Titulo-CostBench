"""Schema/data bootstrap helpers for Real Estate metrics."""

from datetime import datetime

from app.extensiones import db
from app.models.real_estate import RealEstateMetrics
from app.services.real_estate_seed_data import REAL_ESTATE_SEED_DATA


def ensure_real_estate_ready(reset: bool = False) -> int:
    """
    Ensure the Real Estate table exists and has seed data.

    Returns:
        Number of rows currently in real_estate_metrics after bootstrap.
    """
    # Create only the table this bootstrap owns, not the full metadata graph.
    RealEstateMetrics.__table__.create(bind=db.engine, checkfirst=True)

    if reset:
        db.session.query(RealEstateMetrics).delete()
        db.session.commit()

    existing_count = db.session.query(RealEstateMetrics).count()
    if existing_count > 0:
        return existing_count

    run_date = datetime.utcnow()
    records = [
        RealEstateMetrics(
            comuna=item["comuna"],
            segment_type=item["segment_type"],
            uf_m2=item["uf_m2"],
            gross_cap_rate=item["gross_cap_rate"],
            net_cap_rate=item["net_cap_rate"],
            vacancy_rate=item["vacancy_rate"],
            days_on_market=item["days_on_market"],
            run_date=run_date,
        )
        for item in REAL_ESTATE_SEED_DATA
    ]
    db.session.bulk_save_objects(records)
    db.session.commit()

    return len(records)
