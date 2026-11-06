"""Datos de demostración (se cargan solo si la base está vacía y CARGAR_DATOS_DEMO=true).

- Clientes: los 40 contratantes del paquete de datos del PIA (datos/clientes_demo.csv).
- Cuadrillas y catálogo de extras: datos de ejemplo del caso ficticio (H-11).
- Dos cotizaciones listas para la demo: una ACEPTADA (para programar) y una PENDIENTE enviada hace
  dos semanas (al consultarla queda VENCIDA, US-22).
"""
from __future__ import annotations

import csv
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from src.domain.comun import Dinero, Rol
from src.domain.cotizacion import Cotizacion
from src.domain.entidades import Cliente
from src.domain.precio import CalculadoraDePrecio
from src.domain.valores import DatosDelInmueble, EstimacionOperativa, ExtraSolicitado, Frecuencia, TipoInmueble

from .db import ClienteRow, CuadrillaRow, ExtraRow
from .repositorios import SqlCotizaciones

ARCHIVO_CLIENTES = Path(__file__).resolve().parents[2] / "datos" / "clientes_demo.csv"

CUADRILLAS = [
    ("CUA-01", "Cuadrilla Norte", 4, True),
    ("CUA-02", "Cuadrilla Centro", 3, True),
    ("CUA-03", "Cuadrilla Sur", 5, True),
    ("CUA-04", "Cuadrilla Apodaca", 3, False),  # inactiva: sirve para demostrar RB-04
]

EXTRAS = [  # H-11: catálogo de ejemplo (SUP-06)
    ("VENTANAS", "Limpieza de ventanas", 25000),
    ("REFRIGERADOR", "Limpieza interior de refrigerador", 18000),
    ("ALFOMBRA", "Lavado de alfombra", 30000),
    ("HORNO", "Limpieza de horno", 20000),
    ("TAPICERIA", "Limpieza de muebles tapizados", 35000),
]


def cargar_datos_demo(fabrica: sessionmaker, reloj) -> bool:
    with fabrica() as session:
        if session.scalar(select(ClienteRow.id).limit(1)) is not None:
            return False
        with open(ARCHIVO_CLIENTES, encoding="utf-8-sig", newline="") as f:
            for fila in csv.DictReader(f):
                session.add(ClienteRow(id=fila["actor_id"], nombre=fila["nombre"], activo=fila["activo"] == "1",
                                       ciudad=fila["ciudad"]))
        for id, nombre, integrantes, activa in CUADRILLAS:
            session.add(CuadrillaRow(id=id, nombre=nombre, integrantes=integrantes, activa=activa))
        for codigo, descripcion, centavos in EXTRAS:
            session.add(ExtraRow(codigo=codigo, descripcion=descripcion, precio_centavos=centavos))
        session.flush()

        ahora = reloj.ahora()
        cliente = Cliente("CLN-C001", "Contratante 01")
        calc = CalculadoraDePrecio()
        ventanas = ExtraSolicitado("VENTANAS", "Limpieza de ventanas", Dinero(Decimal("250")))
        repo = SqlCotizaciones(session)

        aceptada = Cotizacion.solicitar(
            "COT-DEMO-01", cliente, DatosDelInmueble("Av. Constitución 100, Monterrey", 120, TipoInmueble.RESIDENCIAL),
            Frecuencia.UNICA, (ventanas,), ahora - timedelta(days=1), Rol.CLIENTE)
        aceptada.estimar(EstimacionOperativa(3, 3), calc, Rol.COORDINADOR)
        aceptada.enviar(ahora - timedelta(days=1), Rol.COORDINADOR)
        aceptada.aceptar(ahora - timedelta(hours=2), Rol.CLIENTE)
        repo.guardar(aceptada)

        sin_respuesta = Cotizacion.solicitar(
            "COT-DEMO-02", cliente, DatosDelInmueble("Calle Morelos 250, Apodaca", 300, TipoInmueble.EMPRESARIAL),
            Frecuencia.MENSUAL, (), ahora - timedelta(days=14), Rol.CLIENTE)
        sin_respuesta.estimar(EstimacionOperativa(5, 4), calc, Rol.COORDINADOR)
        sin_respuesta.enviar(ahora - timedelta(days=14), Rol.COORDINADOR)
        repo.guardar(sin_respuesta)
        session.commit()
        return True
