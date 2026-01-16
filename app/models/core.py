# Minimal ORM models for future DB usage.
# Comments in English, logs in Spanish.

from datetime import datetime
from ..extensions import db

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Institution(db.Model, TimestampMixin):
    __tablename__ = "institutions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), unique=True, nullable=False)
    country = db.Column(db.String(64), default="CL")

class Product(db.Model, TimestampMixin):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id"), nullable=False)
    kind = db.Column(db.String(64))  # e.g., cuenta_vista, cuenta_corriente, tarjeta_credito
    plan_name = db.Column(db.String(160))
    institution = db.relationship("Institution", backref=db.backref("products", lazy=True))

class FeeEvent(db.Model, TimestampMixin):
    __tablename__ = "fee_events"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    event = db.Column(db.String(80))       # e.g., transferencia, giro, mantencion
    unit = db.Column(db.String(40))        # per_tx, mensual, anual
    amount = db.Column(db.Numeric(14, 4))  # CLP or UF value
    currency = db.Column(db.String(8), default="CLP")
    cap = db.Column(db.Numeric(14, 4))     # optional cap
    valid_from = db.Column(db.Date)
    valid_to = db.Column(db.Date)
    source_url = db.Column(db.Text)
    product = db.relationship("Product", backref=db.backref("fee_events", lazy=True))

class ExemptionRule(db.Model, TimestampMixin):
    __tablename__ = "exemption_rules"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    condition = db.Column(db.String(200))  # e.g., saldo_promedio > X, edad < Y
    details = db.Column(db.Text)
    valid_from = db.Column(db.Date)
    valid_to = db.Column(db.Date)
    product = db.relationship("Product", backref=db.backref("exemptions", lazy=True))

class Indicator(db.Model, TimestampMixin):
    __tablename__ = "indicators"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    series = db.Column(db.String(40), nullable=False)  # UF, IPC
    value = db.Column(db.Numeric(16, 6), nullable=False)
    source = db.Column(db.String(32))  # BDE or CMF

class CTARecord(db.Model, TimestampMixin):
    __tablename__ = "cta_records"
    id = db.Column(db.Integer, primary_key=True)
    institution = db.Column(db.String(160), nullable=False)
    product = db.Column(db.String(160), nullable=False)
    monthly_cta_clp = db.Column(db.Numeric(14, 4))
    annual_cta_clp = db.Column(db.Numeric(14, 4))
    capture_date = db.Column(db.Date)
    source_url = db.Column(db.Text)

class CardFee(db.Model, TimestampMixin):
    __tablename__ = "card_fees"
    id = db.Column(db.Integer, primary_key=True)
    issuer = db.Column(db.String(160))
    card_name = db.Column(db.String(160))
    annual_maintenance = db.Column(db.Numeric(14, 4))
    cash_advance_fee = db.Column(db.Numeric(14, 4))
    foreign_use_fee = db.Column(db.Numeric(14, 4))
    validity = db.Column(db.String(80))
    source_url = db.Column(db.Text)
