import pandas as pd
import os

def inspect_parquet(directory='data'):
    print(f"\n{'='*50}\nInspeccionando archivos Parquet en '{directory}'\n{'='*50}")
    
    if not os.path.exists(directory):
        print(f"El directorio {directory} no existe.")
        return

    files = [f for f in os.listdir(directory) if f.endswith('.parquet')]
    
    if not files:
        print("No se encontraron archivos .parquet")
        return

    for f in files:
        path = os.path.join(directory, f)
        try:
            df = pd.read_parquet(path)
            print(f"\n📄 ARCHIVO: {f}")
            print(f"{'-'*len(f)}")
            print(f"Dimensiones: {df.shape}")
            print(f"Columnas: {df.columns.tolist()}")
            print("\n🔍 Primeras 5 filas:")
            print(df.head().to_string())
            print("\n📊 Info de tipos:")
            print(df.dtypes)
            print("\n" + "="*30)
        except Exception as e:
            print(f"Error leyendo {f}: {e}")

if __name__ == "__main__":
    inspect_parquet()
