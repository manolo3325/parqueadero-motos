from database import Base, engine
from models import Propietario, Moto, Casillero, Registro

print("📦 Creando las tablas en la base de datos...")
Base.metadata.create_all(bind=engine)
print("✅ Tablas creadas correctamente.")
