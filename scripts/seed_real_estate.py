import argparse
import os
import sys

# Add the root directory to sys.path to run the script inside Docker context
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.real_estate_bootstrap import ensure_real_estate_ready


def seed_db(reset: bool = False):
    app = create_app()
    with app.app_context():
        print("Bootstrapping real_estate_metrics...")
        rows = ensure_real_estate_ready(reset=reset)
        print(f"Real estate dataset ready with {rows} rows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Real Estate metrics data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing rows and insert the canonical dataset",
    )
    args = parser.parse_args()
    seed_db(reset=args.reset)
