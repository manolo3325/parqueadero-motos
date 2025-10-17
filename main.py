from fastapi import FastAPI, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from datetime import datetime
from datetime import timezone
import pytz
from math import ceil
import json
from pathlib import Path
import re

# --- Crear todas las tablas ---
models.Base.metadata.create_all(bind=engine)

# --- Cargar configuración ---
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# --- Crear app FastAPI ---
app = FastAPI(title="🅿️ Parqueadero de Motos API")

# --- Función hora Colombia ---
def hora_colombia():
    tz = pytz.timezone("America/Bogota")
    return datetime.now(tz)

# --- Dependencia para obtener la sesión DB ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Inicializar casilleros ---
def inicializar_casilleros():
    db = SessionLocal()
    total = config["total_casilleros"]
    existentes = db.query(models.Casillero).count()
    for i in range(existentes + 1, total + 1):
        casillero = models.Casillero(numero=i, disponible=True)
        db.add(casillero)
    db.commit()
    db.close()
    print(f"✅ {total} casilleros inicializados")

inicializar_casilleros()

# --- ENDPOINTS ---

# Inicio
@app.get("/")
def home():
    return {"mensaje": "Bienvenido a la API del Parqueadero de Motos 🏍️"}

# Crear propietario
@app.post("/propietarios/")
def crear_propietario(nombre: str, apellido: str, telefono: str, db: Session = Depends(get_db)):
    # ✅ Validar que el nombre y apellido contenga solo letras y espacios
    if not nombre.isalpha() or not apellido.isalpha():
        raise HTTPException(status_code=400, detail="El nombre y apellido solo deben contener letras")
    
    # ✅ Validar teléfono de 10 dígitos
    if not telefono.isdigit() or len(telefono) != 10:
        raise HTTPException(status_code=400, detail="El teléfono debe tener 10 números")

    nombre = nombre.upper()
    apellido = apellido.upper()
    propietario = models.Propietario(nombre=nombre, apellido=apellido, telefono=telefono)
    db.add(propietario)
    db.commit()
    db.refresh(propietario)

    return {
        "mensaje": "Propietario registrado",
        "data": {"id": propietario.id, "nombre": propietario.nombre, "apellido": propietario.apellido, "telefono": propietario.telefono}
    }
def crear_propietario(nombre: str, telefono: str, db: Session = Depends(get_db)):
    # ✅ Validar que el nombre contenga solo letras y espacios
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', nombre):
        raise HTTPException(status_code=400, detail="El nombre solo puede contener letras y espacios")

    # ✅ Validar teléfono de 10 dígitos
    if not telefono.isdigit() or len(telefono) != 10:
        raise HTTPException(status_code=400, detail="El teléfono debe tener 10 números")

    nombre = nombre.upper()
    propietario = models.Propietario(nombre=nombre, telefono=telefono)
    db.add(propietario)
    db.commit()
    db.refresh(propietario)

    return {
        "mensaje": "Propietario registrado",
        "data": {"id": propietario.id, "nombre": propietario.nombre}
    }
# 🧾 Editar propietario existente
@app.put("/propietarios/{id}")
def editar_propietario(
    id: int,
    nombre: str = Form(...),
    apellido: str = Form(...),
    telefono: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validaciones
    if not telefono.isdigit() or len(telefono) != 10:
        raise HTTPException(status_code=400, detail="El teléfono debe tener 10 números")

    if not nombre.replace(" ", "").isalpha() or not apellido.replace(" ", "").isalpha():
        raise HTTPException(status_code=400, detail="El nombre y apellido solo pueden contener letras y espacios")

    propietario = db.query(models.Propietario).filter(models.Propietario.id == id).first()
    if not propietario:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")

    # Actualizar campos
    propietario.nombre = nombre.upper()
    propietario.apellido = apellido.upper()
    propietario.telefono = telefono

    db.commit()
    db.refresh(propietario)

    return {
        "mensaje": "Propietario actualizado correctamente",
        "data": {
            "id": propietario.id,
            "nombre": propietario.nombre,
            "apellido": propietario.apellido,
            "telefono": propietario.telefono
        }
    }



#Ver propietarios
@app.get("/propietarios/")
def listar_propietarios(db: Session = Depends(get_db)):
    propietarios = db.query(models.Propietario).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "telefono": p.telefono
        }
        for p in propietarios
    ]


# Crear moto
@app.post("/motos/")
def crear_moto(placa: str, id_propietario: int, db: Session = Depends(get_db)):
    import re
    if not re.match(r"^[A-Z]{3}[0-9]{2}[A-Z]?$", placa.upper()):
        raise HTTPException(status_code=400, detail="Formato de placa inválido. Ejemplo: ABC12 o ABC12D")
    placa = placa.upper()
    propietario = db.query(models.Propietario).filter(models.Propietario.id == id_propietario).first()
    if not propietario:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")
    moto = models.Moto(placa=placa, id_propietario=id_propietario)
    db.add(moto)
    db.commit()
    db.refresh(moto)
    return {"mensaje": "Moto registrada correctamente", "data": {"placa": moto.placa}}

# Ver todas las motos
@app.get("/motos/")
def listar_motos(db: Session = Depends(get_db)):
    motos = db.query(models.Moto).all()
    return motos

# Registrar entrada
@app.post("/registros/")
def crear_registro(placa_moto: str, num_cascos: int, observaciones: str = None, db: Session = Depends(get_db)):
    placa_moto= placa_moto.upper()
    moto = db.query(models.Moto).filter(models.Moto.placa == placa_moto).first()
    if not moto:
        raise HTTPException(
            status_code=400,
            detail="La moto no existe. Primero debes registrar la moto con su propietario."
        )
    
    # Validar cantidad de cascos (puede ser 0, 1 o 2)
    if num_cascos < 0 or num_cascos > 2:
        raise HTTPException(status_code=400, detail="El número de cascos debe ser entre 0 y 2")

    # Verificar si la moto ya tiene un registro activo
    registro_activo = db.query(models.Registro).filter(
        models.Registro.placa_moto == placa_moto,
        models.Registro.hora_salida == None
    ).first()
    if registro_activo:
        raise HTTPException(status_code=400, detail="Esta moto ya tiene un registro activo")

    # Buscar casillero disponible según el número de cascos
    casillero = None
    if num_cascos > 0:
        # Buscar uno con espacio suficiente (cascos_ocupados + num_cascos <= 2)
        casillero = db.query(models.Casillero).filter(
            models.Casillero.cascos_ocupados + num_cascos <= 2
        ).first()

        if not casillero:
            raise HTTPException(status_code=400, detail="No hay casilleros con espacio disponible")

        # Actualizar cantidad de cascos ocupados
        casillero.cascos_ocupados += num_cascos
        # Si llega al límite de 2 cascos, se marca como no disponible
        if casillero.cascos_ocupados >= 2:
            casillero.disponible = False
    else:
        # Si no deja cascos, no se asigna casillero
        casillero = None

    # Crear registro
    registro = models.Registro(
        placa_moto=placa_moto,
        cascos=num_cascos,
	observaciones=observaciones,
        hora_entrada=hora_colombia(),
        id_casillero=casillero.id if casillero else None
    )

    db.add(registro)
    db.commit()
    db.refresh(registro)

    return {
        "mensaje": "Registro de entrada creado correctamente",
        "data": {
            "id": registro.id,
            "placa": registro.placa_moto,
            "hora_entrada": registro.hora_entrada,
            "num_cascos": registro.cascos,
            "observaciones": registro.observaciones,
            "casillero_asignado": casillero.numero if casillero else "Sin casillero"
        }
    }

#Ver registros
@app.get("/registros/")
def listar_registros(db: Session = Depends(get_db)):
    registros = db.query(models.Registro).all()
    return [
        {
            "id": r.id,
            "placa": r.placa_moto,
            "cascos": r.cascos,
            "hora_entrada": r.hora_entrada,
            "hora_salida": r.hora_salida,
            "valor_pagado": r.valor_pagado,
            "casillero": r.id_casillero
        }
        for r in registros
    ]


# Registrar salida
@app.post("/registros/salida/")
def registrar_salida(placa_moto: str = Query(...), db: Session = Depends(get_db)):
    placa_moto = placa_moto.upper()

    # Buscar registro activo
    registro = db.query(models.Registro).filter(
        models.Registro.placa_moto == placa_moto,
        models.Registro.hora_salida == None
    ).first()

    if not registro:
        raise HTTPException(status_code=404, detail="No hay registro activo para esta moto")

    # Registrar hora de salida
    hora_salida = hora_colombia()
    registro.hora_salida = hora_salida

    # Calcular tiempo total en minutos
    hora_salida_naive = registro.hora_salida.replace(tzinfo=None)
    hora_entrada_naive = registro.hora_entrada.replace(tzinfo=None)
    tiempo_minutos = (hora_salida_naive - hora_entrada_naive).total_seconds() / 60

    # Calcular valor a pagar con tolerancia
    if tiempo_minutos <= config["tolerancia_minutos"]:
        valor = 0
    elif tiempo_minutos >= 24 * 60:
        valor = config["tarifa_dia"]
    else:
        minutos_a_cobrar = tiempo_minutos - config["tolerancia_minutos"]
        horas = ceil(minutos_a_cobrar / 60)
        valor = horas * config["tarifa_hora"]

    registro.valor_pagado = valor

    # Liberar espacio en casillero (si aplica)
    casillero = registro.casillero
    if casillero and registro.cascos > 0:
        # Restar los cascos que esta moto retiró
        casillero.cascos_ocupados -= registro.cascos
        if casillero.cascos_ocupados < 0:
            casillero.cascos_ocupados = 0  # seguridad extra
        # Si ya no hay cascos, se marca disponible
        casillero.disponible = casillero.cascos_ocupados < 2

    db.commit()
    db.refresh(registro)

    return {
        "mensaje": "Salida registrada correctamente",
        "data": {
            "placa": registro.placa_moto,
            "hora_entrada": registro.hora_entrada,
            "hora_salida": registro.hora_salida,
            "tiempo_minutos": round(tiempo_minutos),
            "valor_pagado": valor,
            "casillero_liberado": casillero.numero if casillero and casillero.disponible else None
        }
    }

#Ver registros activos
@app.get("/registros/activos/")
def listar_registros_activos(db: Session = Depends(get_db)):
    activos = db.query(models.Registro).filter(models.Registro.hora_salida == None).all()
    return [
        {
            "id": r.id,
            "placa": r.placa_moto,
            "hora_entrada": r.hora_entrada,
            "cascos": r.cascos,
            "casillero": r.id_casillero
        }
        for r in activos
    ]

