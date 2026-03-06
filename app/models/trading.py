"""Trading models: Wallet, Position, and TradeHistory for paper trading."""
from datetime import datetime
from app.extensiones import db


INITIAL_BALANCE = 10_000_000  # CLP $10M starting balance
TRADEABLE_ASSETS = ("gold", "copper", "oil", "btc", "eth", "usdclp", "uf")


class Wallet(db.Model):
    """Virtual wallet for paper trading — one per user."""

    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    balance = db.Column(db.Numeric(16, 2), nullable=False, default=INITIAL_BALANCE)
    initial_balance = db.Column(
        db.Numeric(16, 2), nullable=False, default=INITIAL_BALANCE
    )
    currency = db.Column(db.String(8), nullable=False, default="CLP")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    user = db.relationship("User", backref=db.backref("wallet", uselist=False))
    positions = db.relationship(
        "Position", backref="wallet", lazy=True, cascade="all, delete-orphan"
    )
    trades = db.relationship(
        "TradeHistory", backref="wallet", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": float(self.balance),
            "initial_balance": float(self.initial_balance),
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Position(db.Model):
    """An open trading position (long or short)."""

    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(
        db.Integer, db.ForeignKey("wallets.id"), nullable=False
    )
    asset = db.Column(db.String(20), nullable=False)
    direction = db.Column(db.String(10), nullable=False, default="long")  # long | short
    quantity = db.Column(db.Numeric(16, 8), nullable=False)
    entry_price = db.Column(db.Numeric(16, 4), nullable=False)
    invested_amount = db.Column(db.Numeric(16, 2), nullable=False)  # CLP spent
    opened_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def to_dict(self, current_price: float = None) -> dict:
        entry = float(self.entry_price)
        qty = float(self.quantity)
        result = {
            "id": self.id,
            "asset": self.asset,
            "direction": self.direction,
            "quantity": qty,
            "entry_price": entry,
            "invested_amount": float(self.invested_amount),
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
        }
        if current_price is not None:
            if self.direction == "long":
                pnl = (current_price - entry) * qty
            else:
                pnl = (entry - current_price) * qty
            result["current_price"] = current_price
            result["unrealized_pnl"] = round(pnl, 2)
            result["pnl_percent"] = round(
                (pnl / float(self.invested_amount)) * 100, 2
            ) if float(self.invested_amount) else 0
        return result


class TradeHistory(db.Model):
    """A closed trade with realized P&L."""

    __tablename__ = "trade_history"

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(
        db.Integer, db.ForeignKey("wallets.id"), nullable=False
    )
    asset = db.Column(db.String(20), nullable=False)
    direction = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(16, 8), nullable=False)
    entry_price = db.Column(db.Numeric(16, 4), nullable=False)
    exit_price = db.Column(db.Numeric(16, 4), nullable=False)
    invested_amount = db.Column(db.Numeric(16, 2), nullable=False)
    pnl = db.Column(db.Numeric(16, 2), nullable=False)
    pnl_percent = db.Column(db.Numeric(8, 2), nullable=False)
    opened_at = db.Column(db.DateTime(timezone=True), nullable=False)
    closed_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "asset": self.asset,
            "direction": self.direction,
            "quantity": float(self.quantity),
            "entry_price": float(self.entry_price),
            "exit_price": float(self.exit_price),
            "invested_amount": float(self.invested_amount),
            "pnl": float(self.pnl),
            "pnl_percent": float(self.pnl_percent),
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }
