from fastapi import FastAPI
from pydantic import BaseModel
import json
from pathlib import Path

# --- Cargar configuración ---
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()

# --- Crear la app FastAPI ---
app = FastAPI(title="Parqueadero Motos - API (Paso 1)")

# Modelo de respuesta para mostrar config
class ConfigOut(BaseModel):
    tarifa_hora: int
    tolerancia_minutos: int
    tarifa_dia: int
    total_casilleros: int
    capacidad_por_casillero: int

@app.get("/", summary="Bienvenida")
def read_root():
    return {
        "message": "API del Parqueadero (Paso 1). La configuración está cargada. Visita /config para verla."
    }

@app.get("/config", response_model=ConfigOut, summary="Ver configuración actual")
def get_config():
    return config
