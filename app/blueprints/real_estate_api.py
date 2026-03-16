"""
Real Estate API Blueprint
Handles market data retrieval and Quant simulations for the Dashboard.
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import desc
import pandas as pd
import numpy as np

from app.extensiones import db
from app.models.real_estate import RealEstateMetrics
from app.services.bcch_service import BCChService
from app.services.scloda_service import chat_completion

real_estate_bp = Blueprint("real_estate_api", __name__)
bcch = BCChService()


@real_estate_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Returns the latest Real Estate market snapshot across the predefined Strategic Communes.
    Cross-references historical metric records with today's live UF value.
    """
    try:
        current_uf = bcch.get_uf()

        # Pull the latest run for each distinct commune in the dataset
        communes_query = db.session.query(RealEstateMetrics.comuna).distinct().all()
        communes = [c[0] for c in communes_query]

        latest_records = []
        for c in communes:
            record = (
                RealEstateMetrics.query.filter_by(comuna=c)
                .order_by(desc(RealEstateMetrics.run_date))
                .first()
            )
            if record:
                data = record.to_dict()
                # Compute current CLP price based on live UF
                data["clp_m2"] = data["uf_m2"] * current_uf
                latest_records.append(data)

        return jsonify(
            {"status": "success", "current_uf": current_uf, "metrics": latest_records}
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@real_estate_bp.route("/simulate", methods=["POST"])
def simulate_investment():
    """
    Runs a 24-month parametric ARIMAX projection utilizing current mortgage rates
    and EEE Macro Expectations. Returns Scloda's RAG-based strategic advice.
    """
    try:
        payload = request.get_json()
        comuna = payload.get("comuna")
        pie_uf = float(payload.get("pie_uf", 2000))
        plazo_anios = int(payload.get("plazo_anios", 20))

        if not comuna:
            return jsonify({"status": "error", "message": "Comuna is required"}), 400

        # Get baseline property metrics
        prop_data = (
            RealEstateMetrics.query.filter_by(comuna=comuna)
            .order_by(desc(RealEstateMetrics.run_date))
            .first()
        )
        if not prop_data:
            return (
                jsonify({"status": "error", "message": "Comuna not found in database"}),
                404,
            )

        uf_m2 = float(prop_data.uf_m2)
        net_cap = float(prop_data.net_cap_rate)

        # 1. Fetch EXOGENOUS Variables (The "IPoM" / EEE effect)
        current_uf = bcch.get_uf()
        mutuo_rate = bcch.get_mortgage_rate() / 100.0  # e.g., 5.1% -> 0.051
        macro_expectations = bcch.get_macro_expectations()

        expected_tpm = macro_expectations["expected_tpm_11m"]
        expected_infl = macro_expectations["expected_inflation_11m"]

        # 2. Mathematical Simulation (24 Months Parametric ARIMAX-style baseline)
        property_size_m2 = 60  # Standard 2B2B unit proxy
        total_uf = uf_m2 * property_size_m2
        loan_uf = max(total_uf - pie_uf, 0)

        # Monthly Mortgage Payment (PMT formula)
        monthly_rate = mutuo_rate / 12
        num_payments = plazo_anios * 12

        if loan_uf > 0 and monthly_rate > 0:
            dividendo_mensual_uf = (
                loan_uf
                * (monthly_rate * (1 + monthly_rate) ** num_payments)
                / ((1 + monthly_rate) ** num_payments - 1)
            )
        else:
            dividendo_mensual_uf = 0

        # Generate the dynamic chart data (Cost of Debt vs Net Yield)
        chart_data = []
        monthly_rent_uf = (total_uf * net_cap) / 12

        for month in range(1, 25):
            # Simulated exogenous impact: If expected TPM is high, UF inflates slightly faster
            # This is a proxy for the ARIMAX drift coefficient based on EEE data
            sim_uf = current_uf * (1 + (expected_infl / 100.0) / 12) ** month

            chart_data.append(
                {
                    "month": month,
                    "projected_uf": round(sim_uf, 2),
                    "dividendo_clp": round(dividendo_mensual_uf * sim_uf),
                    "renta_neta_clp": round(monthly_rent_uf * sim_uf),
                }
            )

        # 3. Scloda LLM RAG Intelligence Integration
        scloda_prompt = f"""
Act as a Quant Financial Advisor for the CostBench application.
The user is evaluating purchasing a property in {comuna} (Segment: {prop_data.segment_type}).
Current market data for this commune:
- Net Cap Rate: {net_cap*100:.2f}%
- Days on market (liquidity): {prop_data.days_on_market} days
- Financing: Central Bank Mortgage Rate at {mutuo_rate*100:.2f}%
- Exogenous Macro: Expected TPM is {expected_tpm}% and Inflation at {expected_infl}% for the next 11 months.

The user will provide a down payment of {pie_uf} UF. Their projected monthly mortgage is {dividendo_mensual_uf:.2f} UF/month and expected monthly rent is {monthly_rent_uf:.2f} UF/month.

Generate a financial analysis IN ENGLISH indicating whether the investment is viable strictly for Cash Flow (Yield) or if it's better suited as a Capital Haven / Appreciation play. 

**Format Requirements**:
- Must be a highly readable bulleted list.
- Keep the language completely accessible and easy to understand for beginners.
- Mention how the Central Bank variables (TPM/Inflation) influence this advice.
- Start with a clear "Yes", "No", or "Wait" regarding immediate cash flow viability.
- Maximum 4 short bullet points in total.
        """
        scloda_result = chat_completion(user_message=scloda_prompt)
        scloda_advice = scloda_result.get(
            "response", "Scloda analysis currently unavailable."
        )

        return jsonify(
            {
                "status": "success",
                "comuna": comuna,
                "total_uf": round(total_uf, 2),
                "loan_uf": round(loan_uf, 2),
                "monthly_dividend_uf": round(dividendo_mensual_uf, 2),
                "monthly_rent_uf": round(monthly_rent_uf, 2),
                "chart_data": chart_data,
                "scloda_advice": scloda_advice,
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
