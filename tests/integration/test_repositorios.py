"""Integración con la base de datos: repositorios, Unidad de Trabajo (commit / rollback) y restricciones."""
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from src.domain.comun import Dinero, Rol
from src.domain.cotizacion import EstadoCotizacion
from src.domain.factura import GeneradorDeFactura
from src.domain.servicio import EstadoServicio, TipoIncidencia
from src.infrastructure.db import crear_fabrica_de_sesiones
from src.infrastructure.repositorios import UnidadDeTrabajoSql
from tests.conftest import HORNO, MANANA_9, cotizacion_aceptada, servicio_en_ejecucion, servicio_programado


@pytest.fixture
def uow_factory(sistema):  # 'sistema' crea las tablas y carga clientes, cuadrillas y catálogo
    fabrica = crear_fabrica_de_sesiones(sistema.engine)
    return lambda: UnidadDeTrabajoSql(fabrica)


def guardar(uow_factory, *objetos):
    with uow_factory() as uow:
        for o in objetos:
            repo = {"COT": uow.cotizaciones, "SRV": uow.servicios, "FAC": uow.facturas}[o.id[:3]]
            repo.guardar(o)
        uow.commit()


def test_cotizacion_ida_y_vuelta_conserva_todos_sus_datos(uow_factory):
    original = cotizacion_aceptada(superficie=Decimal("87.5"))
    original.id = "COT-RT"
    guardar(uow_factory, original)
    with uow_factory() as uow:
        leida = uow.cotizaciones.obtener("COT-RT")
    assert leida.estado == EstadoCotizacion.ACEPTADA
    assert leida.inmueble == original.inmueble and leida.extras == original.extras
    assert leida.precio == original.precio and leida.vigencia == original.vigencia
    assert leida.estimacion == original.estimacion


def test_servicio_ida_y_vuelta_con_incidencias_y_cargos(uow_factory):
    cot = cotizacion_aceptada()
    s = servicio_en_ejecucion()
    s.cotizacion_id = cot.id
    s.registrar_incidencia(TipoIncidencia.SERVICIO_ADICIONAL, "Horno", MANANA_9, Rol.SUPERVISOR, extra=HORNO)
    s.registrar_incidencia(TipoIncidencia.INMUEBLE_MAYOR, "Mayor", MANANA_9, Rol.SUPERVISOR,
                           superficie_real=Decimal("130.5"))
    guardar(uow_factory, cot, s)

    with uow_factory() as uow:
        leido = uow.servicios.obtener("SRV-1")
        leido.autorizar_cargo("SRV-1-C1", Rol.COORDINADOR)  # modificar un hijo existente
        uow.servicios.guardar(leido)
        uow.commit()
    with uow_factory() as uow:
        final = uow.servicios.obtener("SRV-1")
    assert final.estado == EstadoServicio.EN_EJECUCION and final.recalculo_pendiente
    assert final.superficie_real == Decimal("130.5")
    assert [i.tipo for i in final.incidencias] == [TipoIncidencia.SERVICIO_ADICIONAL, TipoIncidencia.INMUEBLE_MAYOR]
    assert final.cargos[0].autorizado and final.cargos[0].monto == Dinero(200)
    assert final.programacion == s.programacion


def test_commit_guarda_y_rollback_descarta(uow_factory):
    cot = cotizacion_aceptada()
    with uow_factory() as uow:
        uow.cotizaciones.guardar(cot)
        uow.rollback()
    with uow_factory() as uow:
        assert uow.cotizaciones.obtener(cot.id) is None
        uow.cotizaciones.guardar(cot)
        uow.commit()
    with uow_factory() as uow:
        assert uow.cotizaciones.obtener(cot.id) is not None


def test_si_no_se_confirma_la_unidad_de_trabajo_deshace_todo(uow_factory):
    with pytest.raises(RuntimeError):
        with uow_factory() as uow:
            uow.cotizaciones.guardar(cotizacion_aceptada())
            raise RuntimeError("falla a mitad del caso de uso")
    with uow_factory() as uow:
        assert uow.cotizaciones.obtener("COT-1") is None


def test_h06_la_base_rechaza_dos_servicios_para_la_misma_cotizacion(uow_factory):
    cot = cotizacion_aceptada()
    primero = servicio_programado()
    segundo = servicio_programado(inicio=datetime(2026, 11, 10, 9, 0))
    segundo.id = "SRV-2"
    guardar(uow_factory, cot, primero)
    with uow_factory() as uow:
        assert uow.servicios.existe_para_cotizacion(cot.id)
        uow.servicios.guardar(segundo)
        with pytest.raises(IntegrityError):
            uow.commit()


def test_sup04_la_base_rechaza_dos_facturas_para_el_mismo_servicio(uow_factory):
    cot = cotizacion_aceptada()
    s = servicio_en_ejecucion()
    s.registrar_terminacion(MANANA_9, Rol.SUPERVISOR)
    f1 = GeneradorDeFactura().generar("FAC-1", s, False, MANANA_9, Rol.ADMINISTRACION)
    f2 = GeneradorDeFactura().generar("FAC-2", s, False, MANANA_9, Rol.ADMINISTRACION)
    guardar(uow_factory, cot, s, f1)
    with uow_factory() as uow:
        assert uow.facturas.existe_para_servicio("SRV-1")
        assert uow.facturas.obtener("FAC-1").total == Dinero(1450)
        uow.facturas.guardar(f2)
        with pytest.raises(IntegrityError):
            uow.commit()


def test_res01_ocupaciones_solo_cuentan_servicios_activos_de_esa_cuadrilla(uow_factory):
    cot = cotizacion_aceptada()
    s = servicio_programado()
    guardar(uow_factory, cot, s)
    with uow_factory() as uow:
        assert len(uow.servicios.ocupaciones_de_cuadrilla("CUA-01")) == 1
        assert uow.servicios.ocupaciones_de_cuadrilla("CUA-01", excluir_id="SRV-1") == []
        assert uow.servicios.ocupaciones_de_cuadrilla("CUA-02") == []
        s.registrar_acceso_denegado(15, MANANA_9, Rol.SUPERVISOR)
        uow.servicios.guardar(s)
        uow.commit()
    with uow_factory() as uow:
        assert uow.servicios.ocupaciones_de_cuadrilla("CUA-01") == []  # un servicio no realizado libera la agenda


def test_catalogo_clientes_y_cuadrillas_de_demostracion(uow_factory):
    with uow_factory() as uow:
        assert uow.catalogo.buscar("HORNO").precio == Dinero(200)
        assert uow.catalogo.buscar("NO-EXISTE") is None
        assert uow.clientes.obtener("CLN-C007").activo is False  # inactivo en el paquete del PIA
        assert uow.cuadrillas.obtener("CUA-04").activa is False
        assert uow.cuadrillas.obtener("CUA-99") is None
