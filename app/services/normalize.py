"""
Normalization service for Bank Cost Benchmark data.
Standardizes raw ingestion data into canonical formats.
"""
import pandas as pd
import re
from typing import Optional

def to_clp(text: str) -> Optional[float]:
    """
    Parses a CLP currency string to float.
    Handles format '$1.234' (Chilean/European style with dot thousand separator).
    Returns None if parsing fails.
    """
    if pd.isna(text) or text == "" or str(text).strip() == "":
        return None
    
    # Check if it's already a number
    if isinstance(text, (int, float)):
        return float(text)
        
    s = str(text)
    # Remove $ and spaces
    s = re.sub(r'[$\s]', '', s)
    
    # In CMF/Chile data, dot is usually thousand separator, comma is decimal?
    # But CMF example was "$448". 
    # Let's handle the specific case seen in CMF "$448" -> 448.0
    # And potentially "$1.000" -> 1000.0
    
    # Remove dots (thousand separators in CLT)
    s = s.replace('.', '')
    # Replace comma with dot (decimal separator)
    s = s.replace(',', '.')
    
    try:
        return float(s)
    except ValueError:
        return None

def canon_cta(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes CMF Account Simulators data to canonical schema.
    
    Input columns: ['Institución', 'Producto', 'Costo neto total', 'source', 'extraction_date']
    Output columns: ['date', 'institucion', 'producto', 'cta_mensual_clp', 'fuente', 'fecha_captura']
    
    * Note: 'date' is derived from extraction_date for versioning.
    """
    out = df.copy()
    
    # Rename map
    rename_map = {
        'Institución': 'institucion',
        'Producto': 'producto',
        'Costo neto total': 'raw_cost',
        'source': 'fuente',
        'extraction_date': 'fecha_captura'
    }
    
    canonical = {
        'BANCO DE CHILE': 'BANCO DE CHILE',
        'BANCO SANTANDER': 'BANCO SANTANDER',
        'SCOTIABANK CHILE': 'SCOTIABANK',
        'BANCO DEL ESTADO DE CHILE': 'BANCO ESTADO',
        'ITAU CORPBANCA': 'ITAU',
        'BANCO DE CREDITO E INVERSIONES': 'BCI',
        'BANCO BICE': 'BANCO BICE',
        'BANCO SECURITY': 'BANCO SECURITY',
        'BANCO CONSORCIO': 'BANCO CONSORCIO',
        'BANCO RIPLEY': 'BANCO RIPLEY',
        'BANCO FALABELLA': 'BANCO FALABELLA'
    }
    
    out = out.rename(columns=rename_map)
    
    # Parse Cost
    out['cta_mensual_clp'] = out['raw_cost'].apply(to_clp)
    
    # Normalize strings
    out['institucion'] = out['institucion'].str.strip().str.upper()
    out['producto'] = out['producto'].str.strip()
    
    # Add 'date' column (normalized to date object from ISO timestamp)
    out['date'] = pd.to_datetime(out['fecha_captura']).dt.normalize()
    
    # Select canonical columns
    cols = ['date', 'institucion', 'producto', 'cta_mensual_clp', 'fuente', 'fecha_captura']
    # Filter only columns that exist (in case 'date' is created from extraction)
    return out[cols]

def canon_uf(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes UF data to canonical schema.
    
    Input columns: ['fecha', 'valor_uf', 'source', 'serie_id', 'extraction_date']
    Output columns: ['fecha', 'valor', 'fuente', 'serie_id', 'fecha_captura']
    """
    out = df.copy()
    
    rename_map = {
        'valor_uf': 'valor',
        'source': 'fuente',
        'extraction_date': 'fecha_captura'
    }
    out = out.rename(columns=rename_map)
    
    out['fecha'] = pd.to_datetime(out['fecha'])
    out['fecha_captura'] = pd.to_datetime(out['fecha_captura'])
    
    cols = ['fecha', 'valor', 'fuente', 'serie_id', 'fecha_captura']
    return out[cols]
