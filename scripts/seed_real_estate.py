import os
import sys
import pandas as pd
from io import StringIO
from datetime import datetime

# Add the root directory to sys.path to run the script inside Docker context
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensiones import db
from app.models.real_estate import RealEstateMetrics

# The base seed data provided by the Quantitative Model
csv_data = """comuna,segment_type,uf_m2,gross_cap_rate,net_cap_rate,vacancy_rate,days_on_market
Ñuñoa,Moderado,85.2,0.048,0.035,0.07,24
Providencia,Luxury,100.4,0.042,0.030,0.05,34
Las Condes,Luxury,112.5,0.038,0.026,0.04,36
Vitacura,Luxury,125.0,0.035,0.022,0.03,33
La Dehesa,Luxury,112.6,0.036,0.024,0.04,36
Santiago Centro,Entry-Level,88.2,0.055,0.045,0.08,36
La Florida,Moderado,79.4,0.052,0.040,0.06,31
Macul,Moderado,77.1,0.050,0.038,0.06,44
Independencia,Entry-Level,67.3,0.053,0.041,0.07,44
San Miguel,Entry-Level,67.2,0.049,0.036,0.15,111
Estacion Central,Entry-Level,46.3,0.058,0.038,0.25,510
La Cisterna,Entry-Level,54.9,0.054,0.042,0.07,32
Cerrillos,Moderado,58.3,0.051,0.039,0.08,67
Colina,Casas,74.0,0.045,0.035,0.05,22
Puente Alto,Casas,63.4,0.055,0.044,0.06,27
San Bernardo,Casas,58.2,0.052,0.040,0.06,31
Lampa,Casas,48.8,0.058,0.046,0.04,13"""

def seed_db():
    app = create_app()
    with app.app_context():
        # Clean current metrics if we want to replace MVP data (Optional)
        # We delete these exact communes from today to avoid duplicates if run multiple times
        print("Creating tables if not exists...")
        db.create_all()
        
        print("Clearing existing metrics...")
        db.session.query(RealEstateMetrics).delete()
        db.session.commit()
        
        print("Parsing seed data...")
        df = pd.read_csv(StringIO(csv_data))
        
        objects_to_add = []
        for _, row in df.iterrows():
            metric = RealEstateMetrics(
                comuna=row['comuna'],
                segment_type=row['segment_type'],
                uf_m2=row['uf_m2'],
                gross_cap_rate=row['gross_cap_rate'],
                net_cap_rate=row['net_cap_rate'],
                vacancy_rate=row['vacancy_rate'],
                days_on_market=row['days_on_market']
                # run_date defaults to utcnow
            )
            objects_to_add.append(metric)
        
        print(f"Adding {len(objects_to_add)} historical commune records...")
        db.session.bulk_save_objects(objects_to_add)
        db.session.commit()
        print("✅ Database Seeded Successfully.")

if __name__ == "__main__":
    seed_db()
