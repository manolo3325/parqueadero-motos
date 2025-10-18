from fastapi import FastAPI, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from datetime import datetime, timedelta
from datetime import timezone
import pytz
from math import ceil
import json
from pathlib import Path
import re
from dateutil.relativedelta import relativedelta
from models import Registro, Casillero, Moto

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
    # Validar nombre y apellido: solo letras y un espacio intermedio permitido
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ]+(?: [A-Za-zÁÉÍÓÚáéíóúÑñ]+)?$", nombre):
        raise HTTPException(status_code=400, detail="El nombre solo puede contener letras y un espacio intermedio.")
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ]+(?: [A-Za-zÁÉÍÓÚáéíóúÑñ]+)?$", apellido):
        raise HTTPException(status_code=400, detail="El apellido solo puede contener letras y un espacio intermedio.")

    # Validar teléfono
    if not re.match(r"^[0-9]{10}$", telefono):
        raise HTTPException(status_code=400, detail="El teléfono debe tener exactamente 10 dígitos.")

    propietario_existente = db.query(models.Propietario).filter(models.Propietario.telefono == telefono).first()
    if propietario_existente:
        raise HTTPException(status_code=400, detail="El propietario con este teléfono ya existe.")

    nuevo_propietario = models.Propietario(nombre=nombre.upper(), apellido=apellido.upper(), telefono=telefono)
    db.add(nuevo_propietario)
    db.commit()
    db.refresh(nuevo_propietario)

    return {"mensaje": "Propietario creado correctamente", "data": {"nombre": nombre, "apellido": apellido, "telefono": telefono}}

# Consultar un propietario
@app.get("/propietarios/{telefono}")
def obtener_propietario(telefono: str, db: Session = Depends(get_db)):
    propietario = db.query(models.Propietario).filter(models.Propietario.telefono == telefono).first()
    if not propietario:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")
    return {
        "nombre": propietario.nombre,
        "apellido": propietario.apellido,
        "telefono": propietario.telefono
    }


# 🧾 Editar propietario existente
@app.put("/propietarios/{telefono}")
def editar_propietario(
    telefono: str,
    nombre: str | None = None,
    apellido: str | None = None,
    nuevo_telefono: str | None = None,
    db: Session = Depends(get_db)
):
    propietario = db.query(models.Propietario).filter(models.Propietario.telefono == telefono).first()
    if not propietario:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")

    # Si no se envía un campo, se deja el valor actual
    propietario.nombre = nombre.upper() if nombre else propietario.nombre
    propietario.apellido = apellido.upper() if apellido else propietario.apellido
    propietario.telefono = nuevo_telefono if nuevo_telefono else propietario.telefono

    db.commit()
    db.refresh(propietario)

    return {
        "mensaje": "Propietario actualizado correctamente",
        "data": {
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
            "telefono": p.telefono,
            "nombre": p.nombre,
            "apellido": p.apellido
        }
        for p in propietarios
    ]


# Crear moto
@app.post("/motos/")
def crear_moto(placa: str, propietario_telefono: str, db: Session = Depends(get_db)):

    # Validar formato de la placa (3 letras + 2 números + opcional 1 letra)
    if not re.match(r"^[A-Z]{3}[0-9]{2}[A-Z]?$", placa.upper()):
        raise HTTPException(status_code=400, detail="Formato de placa inválido. Ejemplo: ABC12 o ABC12D")

    placa = placa.upper()

    # Verificar que el propietario exista
    propietario = db.query(models.Propietario).filter(models.Propietario.telefono == propietario_telefono).first()
    if not propietario:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")

    # Verificar si la moto ya está registrada
    moto_existente = db.query(models.Moto).filter(models.Moto.placa == placa).first()
    if moto_existente:
        return {"mensaje": f"La moto con placa {placa} ya está registrada."}

    # Crear y guardar la nueva moto
    moto = models.Moto(placa=placa, propietario_telefono=propietario_telefono)
    db.add(moto)
    db.commit()
    db.refresh(moto)

    return {"mensaje": "Moto registrada correctamente", "data": {"placa": moto.placa}}


# Ver todas las motos
@app.get("/motos/")
def listar_motos(db: Session = Depends(get_db)):
    motos = db.query(models.Moto).all()
    return motos

@app.get("/motos/{placa}")
def obtener_moto(placa: str, db: Session = Depends(get_db)):
    placa = placa.upper()
    moto = db.query(models.Moto).filter(models.Moto.placa == placa).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")

    propietario = db.query(models.Propietario).filter(models.Propietario.telefono == moto.propietario_telefono).first()

    return {
        "placa": moto.placa,
        "propietario": {
            "nombre": propietario.nombre if propietario else "Desconocido",
            "apellido": propietario.apellido if propietario else "Desconocido",
            "telefono": moto.propietario_telefono
        },
        "tipo_cobro": moto.tipo_cobro if hasattr(moto, "tipo_cobro") else "No definido"
    }

# Editar Moto
@app.put("/motos/{placa}")
def editar_moto(placa: str, nuevo_telefono: str, db: Session = Depends(get_db)):
    placa = placa.upper()

    # Buscar la moto
    moto = db.query(models.Moto).filter(models.Moto.placa == placa).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")

    # Validar formato del teléfono (solo números, 10 dígitos)
    if not re.match(r"^\d{10}$", nuevo_telefono):
        raise HTTPException(status_code=400, detail="El teléfono debe tener 10 dígitos numéricos")

    # Verificar que el propietario exista
    propietario = db.query(models.Propietario).filter(models.Propietario.telefono == nuevo_telefono).first()
    if not propietario:
        raise HTTPException(status_code=404, detail="Propietario con ese teléfono no encontrado")

    # Actualizar el teléfono del propietario en la moto
    moto.propietario_telefono = nuevo_telefono
    db.commit()
    db.refresh(moto)

    return {
        "mensaje": f"Teléfono actualizado correctamente para la moto {placa}",
        "data": {
            "placa": moto.placa,
            "propietario_telefono": moto.propietario_telefono,
            "propietario_nombre": propietario.nombre,
            "propietario_apellido": propietario.apellido
        }
    }



# Registrar entrada
@app.post("/registros/")
def crear_registro(
    placa: str,
    tipo_cobro: str = "por_horas",
    num_cascos: int = 0,
    observaciones: str | None = None,
    db: Session = Depends(get_db)
):
    placa = placa.upper()
    tipo_cobro = tipo_cobro.lower().replace(" ", "_")
    if tipo_cobro not in ["por_horas", "por_dia", "mensualidad"]:
        raise HTTPException(status_code=400, detail="Tipo de cobro inválido. Usa: por horas, por dia o mensualidad.")

    if num_cascos < 0 or num_cascos > 2:
        raise HTTPException(status_code=400, detail="El número de cascos debe ser 0, 1 o 2.")

    # Verificar moto
    moto = db.query(models.Moto).filter(models.Moto.placa == placa).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no registrada.")

    # Verificar registro activo
    activo = db.query(models.Registro).filter(
        models.Registro.placa_moto == placa,
        models.Registro.hora_salida.is_(None)
    ).first()
    if activo:
        raise HTTPException(status_code=400, detail="La moto ya tiene un registro activo.")

    # Helper: ocupación real en un casillero (basado en registros activos)
    def ocupacion_actual(casillero_id: int) -> int:
        registros_activos = db.query(models.Registro).filter(
            models.Registro.id_casillero == casillero_id,
            models.Registro.hora_salida.is_(None)
        ).all()
        return sum(r.cascos or 0 for r in registros_activos)

    # Traer casilleros ordenados (por 'numero' si lo tienes, si no por id)
    casilleros = db.query(models.Casillero).order_by(models.Casillero.id).all()

    # Construir listas con ocupación actual
    parciales = []  # (casillero_obj, ocup)
    vacios = []     # casillero_obj
    suficientes = []  # casilleros con espacio >= num_cascos (para buscar único casillero)

    for c in casilleros:
        ocup = ocupacion_actual(c.id)
        espacio = 2 - ocup
        if espacio >= num_cascos and num_cascos > 0:
            # casillero que por sí solo puede albergar TODOS los cascos de la moto
            suficientes.append((c, ocup))
        if ocup == 0:
            vacios.append(c)
        elif ocup < 2:
            parciales.append((c, ocup))
        # si ocup >= 2 => no disponible

    # Ordenar por numero/id ascendente para determinismo
    suficientes.sort(key=lambda t: getattr(t[0], "numero", t[0].id))
    parciales.sort(key=lambda t: getattr(t[0], "numero", t[0].id))
    vacios.sort(key=lambda c: getattr(c, "numero", c.id))

    asignaciones = []  # lista de (casillero_obj, uso)
    restante = num_cascos
    id_casillero_principal = None
    casilleros_asignados_numeros = []

    # --------- PRIORIDAD: si num_cascos > 0 buscamos un único casillero capaz de alojarlos todos ----------
    if num_cascos > 0:
        if suficientes:
            # elegimos el primer casillero (menor número) que tenga espacio >= num_cascos
            c_obj, ocup = suficientes[0]
            uso = num_cascos
            asignaciones.append((c_obj, uso))
            restante -= uso
            id_casillero_principal = c_obj.id
        else:
            # No existe casillero único con suficiente espacio -> combinar parciales + vacios
            # 1) llenar parciales (menor número)
            for c_obj, ocup in parciales:
                if restante <= 0:
                    break
                espacio = 2 - ocup
                uso = min(espacio, restante)
                if uso > 0:
                    asignaciones.append((c_obj, uso))
                    restante -= uso
                    if id_casillero_principal is None:
                        id_casillero_principal = c_obj.id
            # 2) usar vacíos
            for c_obj in vacios:
                if restante <= 0:
                    break
                uso = min(2, restante)
                asignaciones.append((c_obj, uso))
                restante -= uso
                if id_casillero_principal is None:
                    id_casillero_principal = c_obj.id

    # Si aún hay restante => no hay capacidad
    if restante > 0:
        raise HTTPException(status_code=400, detail="No hay casilleros con capacidad suficiente para los cascos solicitados.")

    # --------- Aplicar asignaciones (actualizar casillero.cascos_ocupados y disponible) ----------
    # Primero recalculamos ocupaciones por seguridad y acumulamos actualizaciones,
    # luego hacemos solo UN commit al final para mantener consistencia.
    for c_obj, uso in asignaciones:
        ocup_act = ocupacion_actual(c_obj.id)
        espacio = 2 - ocup_act
        if espacio <= 0:
            raise HTTPException(status_code=400, detail=f"Espacio insuficiente en casillero {getattr(c_obj,'numero',c_obj.id)} al reservar.")
        uso_final = min(uso, espacio)
        c_obj.cascos_ocupados = (c_obj.cascos_ocupados or 0) + uso_final
        c_obj.disponible = False if c_obj.cascos_ocupados >= 2 else True
        db.add(c_obj)
        casilleros_asignados_numeros.append(getattr(c_obj, "numero", c_obj.id))

    # Guardar cambios de casilleros una sola vez
    db.commit()

    # --------- Calcular proximo pago ----------
    proximo_pago = None
    if tipo_cobro == "por_dia":
        proximo_pago = datetime.now() + timedelta(days=1)
    elif tipo_cobro == "mensualidad":
        proximo_pago = datetime.now() + timedelta(days=30)

    # --------- Crear registro ----------
    nuevo_registro = models.Registro(
        placa_moto=placa,
        hora_entrada=datetime.now(),
        cascos=num_cascos,
        id_casillero=id_casillero_principal,
        tipo_cobro=tipo_cobro,
        proximo_pago=proximo_pago,
        observaciones=observaciones
    )
    db.add(nuevo_registro)
    db.commit()
    db.refresh(nuevo_registro)

    return {
        "mensaje": "Registro creado exitosamente.",
        "placa": nuevo_registro.placa_moto,
        "hora_entrada": nuevo_registro.hora_entrada,
        "tipo_cobro": nuevo_registro.tipo_cobro,
        "cascos": nuevo_registro.cascos,
        "casilleros_asignados": casilleros_asignados_numeros,
        "observaciones": nuevo_registro.observaciones,
        "proximo_pago": nuevo_registro.proximo_pago,
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

@app.post("/registros/salida/")
def registrar_salida(placa_moto: str, db: Session = Depends(get_db)):
    registro = db.query(Registro).filter(
        Registro.placa_moto == placa_moto.upper(),
        Registro.hora_salida.is_(None)
    ).first()

    if not registro:
        return {"mensaje": f"No hay registro activo para la moto con placa {placa_moto}"}

    # Normalizar zona horaria
    hora_entrada = registro.hora_entrada
    if hora_entrada.tzinfo is not None:
        hora_entrada = hora_entrada.replace(tzinfo=None)

    hora_salida = datetime.now(pytz.timezone("America/Bogota")).replace(tzinfo=None)
    registro.hora_salida = hora_salida

    tiempo_total = hora_salida - hora_entrada
    total_segundos = int(tiempo_total.total_seconds())
    horas_ent = total_segundos // 3600
    minutos_ent = (total_segundos % 3600) // 60

    tipo_cobro = registro.tipo_cobro.lower()
    valor_total = 0
    mensaje = ""

    # ===== COBRO POR HORAS =====
    if tipo_cobro == "por_horas":
        if horas_ent < 7:
            # Tolerancia de 10 minutos
            horas_cobradas = horas_ent
            if minutos_ent > 10:
                horas_cobradas += 1
            elif minutos_ent == 0 and horas_ent == 0:
                horas_cobradas = 1  # mínimo 1 hora
            valor_total = horas_cobradas * 1100
            mensaje = f"Tiempo: {horas_ent} hora(s) y {minutos_ent} minuto(s). Valor a pagar: ${valor_total:,}"
        else:
            # Tiempo mayor a 7 horas
            valor_total = 7000
            mensaje = (
                f"Tiempo: {horas_ent} hora(s) y {minutos_ent} minuto(s). "
                f"Supera las 7 horas, puede cobrar por día (${valor_total}) o mantener cobro por horas."
            )

    # ===== COBRO POR DÍA =====
    elif tipo_cobro == "por_dia":
        if horas_ent < 7:
            valor_total = 7000
            mensaje = (
                f"Tiempo: {horas_ent} hora(s) y {minutos_ent} minuto(s). "
                "El tiempo fue menor a 7 horas. Puede cobrar por horas o mantener cobro por día ($7.000)."
            )
        else:
            valor_total = 7000
            mensaje = f"Cobro diario aplicado. Tiempo total: {horas_ent} hora(s) y {minutos_ent} minuto(s). Valor: ${valor_total:,}"

    # ===== COBRO MENSUALIDAD =====
    elif tipo_cobro == "mensualidad":
        if registro.proximo_pago is None:
            mensaje = "Esta moto está registrada con mensualidad, pero no tiene fecha de pago configurada."
        else:
            hoy = datetime.now(pytz.timezone("America/Bogota")).date()
            proximo_pago = registro.proximo_pago.date()
            dias_mora = (hoy - proximo_pago).days
            if dias_mora > 0:
                mensaje = f"Está en mora hace {dias_mora} día(s). Próximo pago pendiente desde {proximo_pago}."
            elif dias_mora == 0:
                mensaje = f"El pago vence hoy ({proximo_pago})."
            else:
                mensaje = f"El próximo pago es el {proximo_pago}."
            valor_total = 45000  # valor mensual fijo

    # Guardar cambios en la base de datos
    db.commit()
    db.refresh(registro)

    return {
        "mensaje": mensaje,
        "placa": registro.placa_moto,
        "tipo_cobro": tipo_cobro,
        "hora_entrada": registro.hora_entrada,
        "hora_salida": registro.hora_salida,
        "valor_total": valor_total,
        "tiempo_total": f"{horas_ent} hora(s) y {minutos_ent} minuto(s)"
    }

@app.post("/registros/pago_mensualidad/")
def pagar_mensualidad(placa_moto: str, db: Session = Depends(get_db)):
    registro = db.query(Registro).filter(
        Registro.placa_moto == placa_moto
    ).order_by(Registro.id.desc()).first()

    if not registro:
        return {"mensaje": f"No hay registros para la moto con placa {placa_moto}"}

    ahora = datetime.now(pytz.timezone("America/Bogota"))
    proximo_pago = ahora + timedelta(days=30)
    valor_mensualidad = 45000  # valor fijo mensual

    registro.tipo_cobro = "mensualidad"
    registro.proximo_pago = proximo_pago
    registro.valor_total = valor_mensualidad

    db.commit()

    return {
        "mensaje": (
            f"Mensualidad pagada exitosamente. "
            f"Próximo pago: {proximo_pago.strftime('%Y-%m-%d')}"
        ),
        "placa": registro.placa_moto,
        "valor_pagado": valor_mensualidad,
        "proximo_pago": proximo_pago.strftime("%Y-%m-%d"),
        "tipo_cobro": registro.tipo_cobro
    }


