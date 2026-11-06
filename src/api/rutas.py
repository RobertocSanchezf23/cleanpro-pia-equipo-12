"""Endpoints REST (controllers). Solo traducen HTTP ↔ casos de uso: no contienen reglas de negocio."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from src.application.cotizaciones import SolicitudDeCotizacion
from src.application.servicios import DatosDeIncidencia, DatosDeProgramacion
from src.domain.servicio import TipoIncidencia
from src.infrastructure.sistema import Sistema

from .dependencias import RolHeader, hora_local, sistema
from .esquemas import (
    AccesoDenegadoEntrada,
    AusenciaEntrada,
    CotizacionEntrada,
    CotizacionSalida,
    EstimacionEntrada,
    FacturaEntrada,
    FacturaSalida,
    IncidenciaEntrada,
    ProgramacionEntrada,
    ReprogramacionEntrada,
    ServicioSalida,
)

S = Annotated[Sistema, Depends(sistema)]

general = APIRouter()
cotizaciones = APIRouter(prefix="/cotizaciones", tags=["1. Cotizaciones (CU-01, CU-02)"])
servicios = APIRouter(prefix="/servicios", tags=["2. Servicios (CU-03, CU-04)"])
facturas = APIRouter(prefix="/facturas", tags=["3. Facturación (CU-05)"])
consultas = APIRouter(tags=["4. Consultas y reportes (CQRS)"])


# ----- General ----------------------------------------------------------------
@general.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/docs")


@general.get("/salud", tags=["0. Salud"], summary="Estado del servicio y de la base de datos")
def salud(s: S):
    with s.unidad_de_trabajo() as uow:
        uow.session.execute(text("SELECT 1"))
    return {"estado": "ok", "base_de_datos": s.engine.dialect.name}


# ----- Cotizaciones -------------------------------------------------------------
@cotizaciones.post("", status_code=201, response_model=CotizacionSalida, summary="US-01 Solicitar cotización")
def solicitar_cotizacion(datos: CotizacionEntrada, rol: RolHeader, s: S):
    c = s.cotizaciones.solicitar(SolicitudDeCotizacion(**datos.model_dump()), rol)
    return CotizacionSalida.de(c)


@cotizaciones.get("", summary="REP-01 Cotizaciones por estado")
def listar_cotizaciones(s: S, estado: str | None = Query(None, examples=["PENDIENTE"])):
    return s.consultas.cotizaciones(estado)


@cotizaciones.get("/{cotizacion_id}", response_model=CotizacionSalida,
                  summary="Consultar cotización (US-22: la marca como vencida si ya pasó su vigencia)")
def consultar_cotizacion(cotizacion_id: str, s: S):
    return CotizacionSalida.de(s.cotizaciones.consultar(cotizacion_id))


@cotizaciones.post("/{cotizacion_id}/estimacion", response_model=CotizacionSalida,
                   summary="US-06 Estimar duración, personal y precio (RB-03)")
def estimar(cotizacion_id: str, datos: EstimacionEntrada, rol: RolHeader, s: S):
    return CotizacionSalida.de(s.cotizaciones.estimar(cotizacion_id, datos.duracion_horas, datos.personal, rol))


@cotizaciones.post("/{cotizacion_id}/envio", response_model=CotizacionSalida, summary="US-07 Enviar al cliente")
def enviar(cotizacion_id: str, rol: RolHeader, s: S):
    return CotizacionSalida.de(s.cotizaciones.enviar(cotizacion_id, rol))


@cotizaciones.post("/{cotizacion_id}/aceptacion", response_model=CotizacionSalida, summary="US-02 Aceptar")
def aceptar(cotizacion_id: str, rol: RolHeader, s: S):
    return CotizacionSalida.de(s.cotizaciones.aceptar(cotizacion_id, rol))


@cotizaciones.post("/{cotizacion_id}/rechazo", response_model=CotizacionSalida, summary="US-02 Rechazar")
def rechazar(cotizacion_id: str, rol: RolHeader, s: S):
    return CotizacionSalida.de(s.cotizaciones.rechazar(cotizacion_id, rol))


@cotizaciones.post("/{cotizacion_id}/renovacion", status_code=201, response_model=CotizacionSalida,
                   summary="US-22 Generar una nueva cotización a partir de una vencida")
def renovar(cotizacion_id: str, rol: RolHeader, s: S):
    return CotizacionSalida.de(s.cotizaciones.renovar(cotizacion_id, rol))


# ----- Servicios ------------------------------------------------------------------
@servicios.post("", status_code=201, response_model=ServicioSalida,
                summary="US-08 / US-09 Programar servicio y asignar cuadrilla")
def programar(datos: ProgramacionEntrada, rol: RolHeader, s: S):
    servicio = s.programacion.programar(DatosDeProgramacion(
        datos.cotizacion_id, datos.cuadrilla_id, datos.supervisor, hora_local(datos.inicio)), rol)
    return ServicioSalida.de(servicio)


@servicios.get("", summary="REP-02 Servicios (filtro opcional por estado)")
def listar_servicios(s: S, estado: str | None = Query(None, examples=["PROGRAMADO"])):
    return s.consultas.servicios(estado)


@servicios.get("/{servicio_id}", response_model=ServicioSalida, summary="Detalle del servicio")
def consultar_servicio(servicio_id: str, s: S):
    return ServicioSalida.de(s.ejecucion.obtener(servicio_id))


@servicios.post("/{servicio_id}/reprogramacion", response_model=ServicioSalida, summary="US-04 Reprogramar (RB-09)")
def reprogramar(servicio_id: str, datos: ReprogramacionEntrada, rol: RolHeader, s: S):
    return ServicioSalida.de(s.programacion.reprogramar(servicio_id, hora_local(datos.nuevo_inicio), rol, datos.cargo))


@servicios.post("/{servicio_id}/ausencia", response_model=ServicioSalida,
                summary="US-10 Empleado ausente: reasignar o reprogramar (RB-10)")
def ausencia(servicio_id: str, datos: AusenciaEntrada, rol: RolHeader, s: S):
    nuevo = hora_local(datos.nuevo_inicio) if datos.nuevo_inicio else None
    return ServicioSalida.de(s.programacion.registrar_ausencia(servicio_id, datos.integrante, datos.reasignado,
                                                               rol, nuevo))


@servicios.post("/{servicio_id}/acceso-denegado", response_model=ServicioSalida,
                summary="US-16 Cliente no permite el acceso (RB-11)")
def acceso_denegado(servicio_id: str, datos: AccesoDenegadoEntrada, rol: RolHeader, s: S):
    return ServicioSalida.de(s.ejecucion.registrar_acceso_denegado(servicio_id, datos.minutos_espera, rol))


@servicios.post("/{servicio_id}/inicio", response_model=ServicioSalida, summary="US-13 Registrar inicio (RB-05)")
def registrar_inicio(servicio_id: str, rol: RolHeader, s: S):
    return ServicioSalida.de(s.ejecucion.registrar_inicio(servicio_id, rol))


@servicios.post("/{servicio_id}/incidencias", status_code=201, response_model=ServicioSalida,
                summary="US-15 Registrar incidencia (RB-06, RB-12, RB-13, RB-14)")
def registrar_incidencia(servicio_id: str, datos: IncidenciaEntrada, rol: RolHeader, s: S):
    return ServicioSalida.de(s.ejecucion.registrar_incidencia(servicio_id, DatosDeIncidencia(
        TipoIncidencia(datos.tipo), datos.descripcion, datos.extra, datos.monto, datos.superficie_real), rol))


@servicios.post("/{servicio_id}/cargos/{cargo_id}/autorizacion", response_model=ServicioSalida,
                summary="US-11 Autorizar cargo adicional (RB-12, RB-14, RB-15)")
def autorizar_cargo(servicio_id: str, cargo_id: str, rol: RolHeader, s: S):
    return ServicioSalida.de(s.ejecucion.autorizar_cargo(servicio_id, cargo_id, rol))


@servicios.post("/{servicio_id}/recalculo", response_model=ServicioSalida,
                summary="US-12 Recalcular precio por inmueble mayor (RB-13)")
def recalcular(servicio_id: str, rol: RolHeader, s: S):
    return ServicioSalida.de(s.ejecucion.recalcular_precio(servicio_id, rol))


@servicios.post("/{servicio_id}/terminacion", response_model=ServicioSalida,
                summary="US-14 Registrar terminación (RB-05, RES-03)")
def registrar_terminacion(servicio_id: str, rol: RolHeader, s: S):
    return ServicioSalida.de(s.ejecucion.registrar_terminacion(servicio_id, rol))


# ----- Facturas ------------------------------------------------------------------
@facturas.post("", status_code=201, response_model=FacturaSalida,
               summary="US-20 Registrar facturación (RB-07, RB-11, RB-14, SUP-04)")
def facturar(datos: FacturaEntrada, rol: RolHeader, s: S):
    return FacturaSalida.de(s.facturacion.facturar(datos.servicio_id, rol))


@facturas.get("/{factura_id}", response_model=FacturaSalida, summary="US-05 Consultar factura")
def consultar_factura(factura_id: str, s: S):
    return FacturaSalida.de(s.facturacion.obtener(factura_id))


@facturas.post("/{factura_id}/pago", response_model=FacturaSalida, summary="Registrar pago (H-14)")
def registrar_pago(factura_id: str, rol: RolHeader, s: S):
    return FacturaSalida.de(s.facturacion.registrar_pago(factura_id, rol))


# ----- Consultas y reportes --------------------------------------------------------
@consultas.get("/clientes", summary="Clientes (datos de demostración del paquete del PIA)")
def clientes(s: S):
    return s.consultas.clientes()


@consultas.get("/cuadrillas", summary="Cuadrillas")
def cuadrillas(s: S):
    return s.consultas.cuadrillas()


@consultas.get("/cuadrillas/{cuadrilla_id}/servicios", summary="US-17 Servicios asignados a una cuadrilla")
def servicios_de_cuadrilla(cuadrilla_id: str, s: S):
    return s.consultas.servicios_de_cuadrilla(cuadrilla_id)


@consultas.get("/catalogo/extras", summary="Catálogo de extras (SUP-06)")
def catalogo(s: S):
    return s.consultas.catalogo()


@consultas.get("/notificaciones", summary="US-19 / US-03 / US-05 Notificaciones registradas")
def notificaciones(s: S, destinatario: str | None = Query(None, examples=["ADMINISTRACION"]),
                   cliente_id: str | None = None):
    return s.consultas.notificaciones(destinatario, cliente_id)


@consultas.get("/reportes/resumen", summary="US-21 Resumen de servicios, incidencias y facturación")
def resumen(s: S):
    return s.consultas.resumen()


@consultas.get("/reportes/incidencias", summary="REP-03 Incidencias registradas")
def reporte_incidencias(s: S, servicio_id: str | None = None):
    return s.consultas.incidencias(servicio_id)


@consultas.get("/reportes/facturacion", summary="REP-04 Facturación y estado de pago")
def reporte_facturacion(s: S):
    return s.consultas.facturacion()


@consultas.get("/reportes/carga-cuadrillas", summary="REP-05 Servicios por cuadrilla")
def carga_cuadrillas(s: S):
    return s.consultas.carga_por_cuadrilla()
