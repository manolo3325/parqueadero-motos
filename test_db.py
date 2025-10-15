# test_db.py
from database import SessionLocal
from models import Propietario, Moto

# 1️⃣ Crear una nueva sesión
db = SessionLocal()

# 2️⃣ Crear un nuevo propietario
nuevo_propietario = Propietario(
    nombre="JUAN MANUEL ORTEGON",
    telefono="3104567890"
)

# 3️⃣ Crear una moto asociada a ese propietario
nueva_moto = Moto(
    placa="TRK89C",
    propietario=nuevo_propietario
)

# 4️⃣ Guardar los datos en la base de datos
db.add(nuevo_propietario)
db.add(nueva_moto)
db.commit()

print("✅ Propietario y moto guardados correctamente!")

# 5️⃣ Consultar los datos guardados
propietarios = db.query(Propietario).all()
motos = db.query(Moto).all()

print("\n📋 Propietarios registrados:")
for p in propietarios:
    print(f"- {p.id}: {p.nombre} ({p.telefono})")

print("\n🏍️ Motos registradas:")
for m in motos:
    print(f"- {m.placa} (Propietario ID: {m.id_propietario})")

# 6️⃣ Cerrar la sesión
db.close()
