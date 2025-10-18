from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# --- MODELO: Propietarios ---
class Propietario(Base):
    __tablename__ = "propietarios"

    telefono = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)

    motos = relationship("Moto", back_populates="propietario")


# --- MODELO: Motos ---
class Moto(Base):
    __tablename__ = "motos"

    placa = Column(String(6), primary_key=True, index=True)
    propietario_telefono = Column(Integer, ForeignKey("propietarios.telefono"))

    propietario = relationship("Propietario", back_populates="motos")
    registros = relationship("Registro", back_populates="moto")


# --- MODELO: Casilleros ---
class Casillero(Base):
    __tablename__ = "casilleros"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, nullable=False)
    disponible = Column(Boolean, default=True)
    cascos_ocupados = Column(Integer, default=0)


# --- MODELO: Registros ---
class Registro(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True, index=True)
    placa_moto = Column(String(6), ForeignKey("motos.placa"))
    hora_entrada = Column(DateTime, default=datetime.now)
    hora_salida = Column(DateTime, nullable=True)
    valor_pagado = Column(Float, default=0)
    cascos = Column(Integer, default=0)
    id_casillero = Column(Integer, ForeignKey("casilleros.id"))
    moto = relationship("Moto", back_populates="registros")
    casillero = relationship("Casillero")
    observaciones = Column(String, nullable=True)
    tipo_cobro = Column(String, default="por_horas")  # por_horas, por_dia o mensualidad
    proximo_pago = Column(DateTime, nullable=True)
    fecha_ultimo_pago = Column(DateTime, nullable=True)

