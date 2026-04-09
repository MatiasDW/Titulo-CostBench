"""
Trading Blueprint – /api/v1/trading

Paper trading system:
  GET  /wallet     – get wallet balance
  GET  /positions  – list open positions
  GET  /history    – list closed trades
  POST /buy        – open a long position
  POST /sell       – open a short position
  POST /close      – close a position
  POST /reset      – reset wallet to initial balance
"""

from decimal import Decimal

from flask import Blueprint, g, jsonify, request

from app.extensiones import db
from app.models.trading import (
    Wallet,
    Position,
    TradeHistory,
    INITIAL_BALANCE,
    TRADEABLE_ASSETS,
)
from app.blueprints.auth import require_auth
from app.ml.logging_utils import get_logger

logger = get_logger("trading.api")

trading_bp = Blueprint("trading", __name__, url_prefix="/api/v1/trading")
_columns_checked = False


def _ensure_schema():
    """Add optional columns if they don't exist (idempotent)."""
    global _columns_checked
    if _columns_checked:
        return
    _columns_checked = True
    try:
        from sqlalchemy import text

        with db.engine.begin() as con:
            con.execute(
                text(
                    "ALTER TABLE positions "
                    "ADD COLUMN IF NOT EXISTS take_profit_price numeric(16,4);"
                )
            )
            con.execute(
                text(
                    "ALTER TABLE positions "
                    "ADD COLUMN IF NOT EXISTS stop_loss_price numeric(16,4);"
                )
            )
    except Exception as e:
        logger.error("schema_check_failed", error=str(e))


@trading_bp.before_app_request
def _before_any_request():
    _ensure_schema()


# ------------------------------------------------------------------
# Helper: get or create wallet
# ------------------------------------------------------------------


def _get_wallet() -> Wallet:
    """Return the user's wallet, creating one if it doesn't exist."""
    wallet = Wallet.query.filter_by(user_id=g.current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=g.current_user.id)
        db.session.add(wallet)
        db.session.commit()
        logger.info("wallet_created", user_id=g.current_user.id)
    return wallet


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@trading_bp.route("/wallet", methods=["GET"])
@require_auth
def get_wallet():
    """GET /wallet – return wallet balance and open positions summary."""
    wallet = _get_wallet()
    positions = Position.query.filter_by(wallet_id=wallet.id).all()
    trades = (
        TradeHistory.query.filter_by(wallet_id=wallet.id)
        .order_by(TradeHistory.closed_at.desc())
        .limit(20)
        .all()
    )

    total_invested = sum(float(p.invested_amount) for p in positions)

    return jsonify(
        {
            "wallet": wallet.to_dict(),
            "positions_count": len(positions),
            "total_invested": round(total_invested, 2),
            "available_cash": float(wallet.balance),
            "total_equity": round(float(wallet.balance) + total_invested, 2),
            "recent_trades": [t.to_dict() for t in trades],
        }
    )


@trading_bp.route("/positions", methods=["GET"])
@require_auth
def get_positions():
    """GET /positions – list all open positions."""
    wallet = _get_wallet()
    positions = Position.query.filter_by(wallet_id=wallet.id).all()
    return jsonify(
        {
            "positions": [p.to_dict() for p in positions],
        }
    )


@trading_bp.route("/history", methods=["GET"])
@require_auth
def get_history():
    """GET /history – list closed trades."""
    wallet = _get_wallet()
    trades = (
        TradeHistory.query.filter_by(wallet_id=wallet.id)
        .order_by(TradeHistory.closed_at.desc())
        .limit(50)
        .all()
    )
    return jsonify(
        {
            "trades": [t.to_dict() for t in trades],
        }
    )


@trading_bp.route("/buy", methods=["POST"])
@require_auth
def buy():
    """POST /buy – open a long position."""
    data = request.get_json(silent=True) or {}
    return _open_position(data, direction="long")


@trading_bp.route("/sell", methods=["POST"])
@require_auth
def sell():
    """POST /sell – open a short position."""
    data = request.get_json(silent=True) or {}
    return _open_position(data, direction="short")


def _open_position(data: dict, direction: str):
    """Shared logic for opening a long or short position."""
    asset = (data.get("asset") or "").lower().strip()
    amount_clp = data.get("amount")  # CLP amount to invest
    price = data.get("price")  # Current market price
    tp = data.get("take_profit_price")
    sl = data.get("stop_loss_price")

    # Validation
    if asset not in TRADEABLE_ASSETS:
        return (
            jsonify(
                {"error": f"Invalid asset. Options: {', '.join(TRADEABLE_ASSETS)}"}
            ),
            400,
        )

    try:
        amount_clp = Decimal(str(amount_clp))
        price = Decimal(str(price))
        tp_val = Decimal(str(tp)) if tp not in (None, "") else None
        sl_val = Decimal(str(sl)) if sl not in (None, "") else None
    except (TypeError, ValueError, ArithmeticError):
        return jsonify({"error": "Invalid amount or price."}), 400

    if amount_clp <= 0 or price <= 0:
        return jsonify({"error": "Amount and price must be positive."}), 400

    wallet = _get_wallet()

    if amount_clp > wallet.balance:
        return (
            jsonify(
                {
                    "error": "Insufficient funds.",
                    "available": float(wallet.balance),
                    "requested": float(amount_clp),
                }
            ),
            400,
        )

    # Calculate quantity
    quantity = amount_clp / price

    # Validate TP/SL
    if tp_val is not None and tp_val <= 0:
        return jsonify({"error": "take_profit_price must be positive."}), 400
    if sl_val is not None and sl_val <= 0:
        return jsonify({"error": "stop_loss_price must be positive."}), 400

    # Create position
    position = Position(
        wallet_id=wallet.id,
        asset=asset,
        direction=direction,
        quantity=quantity,
        entry_price=price,
        invested_amount=amount_clp,
        take_profit_price=tp_val,
        stop_loss_price=sl_val,
    )

    # Deduct from wallet
    wallet.balance -= amount_clp

    db.session.add(position)
    db.session.commit()

    logger.info(
        "position_opened",
        user_id=g.current_user.id,
        asset=asset,
        direction=direction,
        amount=float(amount_clp),
        price=float(price),
        quantity=float(quantity),
        take_profit=float(tp_val) if tp_val is not None else None,
        stop_loss=float(sl_val) if sl_val is not None else None,
    )

    return (
        jsonify(
            {
                "message": f"{direction.capitalize()} position opened.",
                "position": position.to_dict(),
                "wallet_balance": float(wallet.balance),
            }
        ),
        201,
    )


@trading_bp.route("/close", methods=["POST"])
@require_auth
def close_position():
    """POST /close – close an open position."""
    data = request.get_json(silent=True) or {}
    position_id = data.get("position_id")
    exit_price = data.get("price")

    if not position_id:
        return jsonify({"error": "position_id is required."}), 400

    try:
        exit_price = Decimal(str(exit_price))
    except (TypeError, ValueError, ArithmeticError):
        return jsonify({"error": "Invalid exit price."}), 400

    wallet = _get_wallet()
    position = Position.query.filter_by(id=position_id, wallet_id=wallet.id).first()

    if not position:
        return jsonify({"error": "Position not found."}), 404

    # Calculate P&L
    qty = position.quantity
    entry = position.entry_price
    invested = position.invested_amount

    if position.direction == "long":
        pnl = (exit_price - entry) * qty
    else:
        pnl = (entry - exit_price) * qty

    pnl_percent = (pnl / invested * 100) if invested else Decimal("0")

    # Return funds + P&L to wallet
    returned = invested + pnl
    wallet.balance += returned

    # Record trade history
    trade = TradeHistory(
        wallet_id=wallet.id,
        asset=position.asset,
        direction=position.direction,
        quantity=qty,
        entry_price=entry,
        exit_price=exit_price,
        invested_amount=invested,
        pnl=pnl,
        pnl_percent=pnl_percent,
        opened_at=position.opened_at,
    )

    db.session.add(trade)
    db.session.delete(position)
    db.session.commit()

    logger.info(
        "position_closed",
        user_id=g.current_user.id,
        asset=position.asset,
        pnl=float(pnl),
    )

    return jsonify(
        {
            "message": "Position closed.",
            "trade": trade.to_dict(),
            "wallet_balance": float(wallet.balance),
        }
    )


@trading_bp.route("/reset", methods=["POST"])
@require_auth
def reset_wallet():
    """POST /reset – reset wallet to initial balance and clear all positions."""
    wallet = _get_wallet()

    # Delete all open positions
    Position.query.filter_by(wallet_id=wallet.id).delete()

    # Reset balance
    wallet.balance = wallet.initial_balance

    db.session.commit()

    logger.info("wallet_reset", user_id=g.current_user.id)

    return jsonify(
        {
            "message": "Wallet reset to initial balance.",
            "wallet": wallet.to_dict(),
        }
    )
