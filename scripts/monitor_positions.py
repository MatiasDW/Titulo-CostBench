"""Background monitor to enforce Stop Loss / Take Profit for paper trading.
Runs inside the docker compose service `trading-worker`.
"""

import time
from decimal import Decimal
import pandas as pd
from sqlalchemy import text

from app import create_app
from app.extensiones import db
from app.models.trading import Position, TradeHistory, Wallet

# Map trading asset keys to series_id in macro parquet
SERIES_MAP = {
    "gold": "GOLDAMGBD228NLBM",
    "copper": "PCOPPUSDM",
    "oil": "DCOILWTICO",
    "btc": "BTC-CLP",
    "eth": "ETH-CLP",
    "usdclp": "USDCLP",
    "uf": "UF",
}

MACRO_PATH = "data/market/macro_indicators.parquet"
SLEEP_SECONDS = 300  # 5 minutes


def load_latest_prices():
    df = pd.read_parquet(MACRO_PATH)
    latest = {}
    for key, sid in SERIES_MAP.items():
        sub = df[df["series_id"] == sid]
        if sub.empty:
            continue
        row = sub.sort_values("date").iloc[-1]
        latest[key] = Decimal(str(row["value"]))
    return latest


def ensure_schema():
    try:
        with db.engine.begin() as con:
            con.execute(
                text(
                    "ALTER TABLE positions ADD COLUMN IF NOT EXISTS take_profit_price numeric(16,4);"
                )
            )
            con.execute(
                text(
                    "ALTER TABLE positions ADD COLUMN IF NOT EXISTS stop_loss_price numeric(16,4);"
                )
            )
    except Exception as e:
        print("schema check failed", e)


def close_position(pos: Position, price: Decimal, wallet: Wallet):
    qty = Decimal(str(pos.quantity))
    entry = Decimal(str(pos.entry_price))
    invested = Decimal(str(pos.invested_amount))

    if pos.direction == "long":
        pnl = (price - entry) * qty
    else:
        pnl = (entry - price) * qty

    pnl_percent = (pnl / invested * Decimal("100")) if invested else Decimal("0")
    returned = invested + pnl
    wallet.balance += returned

    trade = TradeHistory(
        wallet_id=wallet.id,
        asset=pos.asset,
        direction=pos.direction,
        quantity=qty,
        entry_price=entry,
        exit_price=price,
        invested_amount=invested,
        pnl=pnl,
        pnl_percent=pnl_percent,
        opened_at=pos.opened_at,
    )
    db.session.add(trade)
    db.session.delete(pos)


def check_positions(app):
    latest = load_latest_prices()
    for asset, px in latest.items():
        # Fetch positions for this asset with TP/SL
        positions = (
            Position.query.filter_by(asset=asset)
            .filter(
                (Position.take_profit_price.isnot(None))
                | (Position.stop_loss_price.isnot(None))
            )
            .all()
        )
        for pos in positions:
            triggered = False
            tp = pos.take_profit_price
            sl = pos.stop_loss_price
            if pos.direction == "long":
                if tp is not None and px >= tp:
                    triggered = True
                if sl is not None and px <= sl:
                    triggered = True
            else:  # short
                if tp is not None and px <= tp:
                    triggered = True
                if sl is not None and px >= sl:
                    triggered = True

            if triggered:
                wallet = Wallet.query.filter_by(id=pos.wallet_id).first()
                if wallet:
                    close_position(pos, px, wallet)
                    app.logger.info(
                        "auto_close",
                        extra={
                            "asset": asset,
                            "price": float(px),
                            "position_id": pos.id,
                        },
                    )
    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        ensure_schema()
    app.logger.info("trading-worker started")
    while True:
        with app.app_context():
            try:
                check_positions(app)
            except Exception as e:
                app.logger.error("trading-worker-error", extra={"error": str(e)})
                db.session.rollback()
        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main()
