import bcchapi
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

user = os.getenv('BDE_USER')
password = os.getenv('BDE_PASS')

print(f"Probando credenciales para usuario: {user}")
print(f"Password (masked): {password[:2]}...{password[-2:] if password else ''}")

try:
    siete = bcchapi.Siete(user, password)
    print("Objeto Siete inicializado. Intentando buscar 'uf'...")
    
    # Intentar una operación simple
    res = siete.buscar("uf")
    print("¡Éxito! Credenciales válidas.")
    print(f"Se encontraron {len(res)} series.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPosibles causas:")
    print("1. Usuario o contraseña incorrectos")
    print("2. La API no está activada en el sitio del Banco Central")
    print("3. Caracteres especiales en la contraseña (intenta ponerla entre comillas en el .env)")
