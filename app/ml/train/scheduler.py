"""
Scheduled Training Jobs
APScheduler-based quincenal retraining for production.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.ml.logging_utils import get_logger

logger = get_logger("ml.scheduler")

# APScheduler import with graceful fallback
APSCHEDULER_AVAILABLE = False
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    # APScheduler not installed - scheduler features disabled
    BackgroundScheduler = None
    CronTrigger = None


# Global scheduler instance
_scheduler: Optional["BackgroundScheduler"] = None


def get_scheduler() -> "BackgroundScheduler":
    """Get or create the global scheduler."""
    global _scheduler
    
    if not APSCHEDULER_AVAILABLE:
        raise ImportError("APScheduler required")
    
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="America/Santiago")
    
    return _scheduler


def schedule_quincenal_training():
    """Schedule quincenal (day 1 and 15) ARIMA training at 3am."""
    scheduler = get_scheduler()
    
    trigger = CronTrigger(
        day="1,15",
        hour=3,
        minute=0,
        timezone="America/Santiago"
    )
    
    scheduler.add_job(
        func=trigger_training_now,
        trigger=trigger,
        id="quincenal_arima_training",
        name="Quincenal ARIMA Training",
        replace_existing=True
    )
    
    logger.info("quincenal_job_scheduled")


def trigger_training_now() -> dict:
    """
    Manually trigger the ARIMA training job for all assets.
    
    Returns dict with results per asset.
    """
    logger.info("training_job_started")
    
    results = {}
    
    try:
        # Check BDE credentials
        bde_user = os.getenv("BDE_USER")
        bde_pass = os.getenv("BDE_PASS")
        
        if not bde_user or not bde_pass:
            logger.warning("bde_creds_missing", 
                          message="BDE_USER and BDE_PASS not set, skipping BDE assets")
        
        # Load from existing parquet for assets we have
        from app.ml.train.arima_trainer import train_asset_model
        import pandas as pd
        
        parquet_path = Path("data/market/macro_indicators.parquet")
        
        if parquet_path.exists():
            df_all = pd.read_parquet(parquet_path)
            
            # Assets to train from parquet
            asset_mapping = {
                "GOLD": "GOLDAMGBD228NLBM",
                "COPPER": "PCOPPUSDM",
                "OIL": "DCOILWTICO",
                "USDCLP": "USD-CLP",  # If exists
            }
            
            for asset, series_id in asset_mapping.items():
                df_asset = df_all[df_all["series_id"] == series_id][["date", "value"]].copy()
                
                if not df_asset.empty:
                    df_asset = df_asset.sort_values("date").dropna()
                    result = train_asset_model(asset, df_asset)
                    results[asset] = result
                    
                    if result["status"] == "ok":
                        logger.info("asset_trained", asset=asset, 
                                   model=result["best_model"],
                                   mae=result["metrics"]["mae"])
                    else:
                        logger.warning("asset_failed", asset=asset, 
                                      error=result["error"])
                else:
                    results[asset] = {
                        "status": "error",
                        "asset": asset,
                        "best_model": None,
                        "metrics": {},
                        "model_path": None,
                        "error": f"series_id {series_id} not found in parquet"
                    }
        
        # Try BDE if credentials exist
        if bde_user and bde_pass:
            try:
                from app.ml.ingest.bde_client import fetch_usdclp, fetch_uf
                
                # USD/CLP
                df_usd = fetch_usdclp(aggregate_monthly=True)
                if len(df_usd) >= 24:
                    result = train_asset_model("USDCLP_BDE", df_usd)
                    results["USDCLP_BDE"] = result
                
                # UF
                df_uf = fetch_uf(aggregate_monthly=True)
                if len(df_uf) >= 24:
                    result = train_asset_model("UF", df_uf)
                    results["UF"] = result
                    
            except Exception as e:
                logger.error("bde_fetch_failed", error=str(e))
                results["BDE_ERROR"] = {"status": "error", "error": str(e)}
        
        logger.info("training_job_complete", assets_trained=len(results))
        
    except Exception as e:
        logger.error("training_job_failed", error=str(e))
        results["_error"] = str(e)
    
    return results


def start_scheduler():
    """Start the background scheduler."""
    if not APSCHEDULER_AVAILABLE:
        logger.error("cannot_start_scheduler", reason="APScheduler not installed")
        return False
    
    scheduler = get_scheduler()
    schedule_quincenal_training()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler_started")
    
    return True


def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown()
        logger.info("scheduler_stopped")
