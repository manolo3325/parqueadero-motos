# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Configuración de la base de datos SQLite ---
DATABASE_URL = "sqlite:///./parqueadero.db"

# Crea el motor que conecta con la base de datos
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Crea la sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()
