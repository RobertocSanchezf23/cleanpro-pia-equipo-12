"""Política de notificaciones: traduce eventos de dominio en mensajes (US-03, US-05, US-19, PA-01).

Las notificaciones se guardan en la misma transacción que el cambio que las provocó. Así, si la
operación se confirma, el aviso existe; si se deshace, no queda un aviso de algo que no pasó.
"""
from __future__ import annotations

from datetime import datetime

from src.domain.comun import EventoDominio

from .puertos import Notificacion

CLIENTE, COORDINADOR, ADMINISTRACION = "CLIENTE", "COORDINADOR", "ADMINISTRACION"


def notificaciones_para(evento: EventoDominio, ahora: datetime) -> list[Notificacion]:
    d, ref = evento.datos, evento.aggregate_id
    cliente = d.get("cliente_id")

    def n(destinatario: str, mensaje: str) -> Notificacion:
        return Notificacion(destinatario, evento.nombre, ref, mensaje,
                            cliente if destinatario == CLIENTE else None, ahora)

    match evento.nombre:
        case "CotizacionEnviada":
            return [n(CLIENTE, f"Tu cotización {ref} por ${float(d['precio']):,.2f} está lista. "
                               f"Puedes aceptarla hasta el {d['vence_en'][:10]}.")]
        case "CotizacionAceptada":
            return [n(COORDINADOR, f"El cliente aceptó la cotización {ref}; ya se puede programar el servicio.")]
        case "CotizacionRechazada":
            return [n(COORDINADOR, f"El cliente rechazó la cotización {ref}.")]
        case "CotizacionVencida":
            return [n(COORDINADOR, f"La cotización {ref} venció sin respuesta; genera una nueva si el cliente "
                                   f"sigue interesado.")]
        case "ServicioProgramado":
            return [n(CLIENTE, f"Tu servicio {ref} quedó programado para el {d['fecha']} con la cuadrilla "
                               f"{d['cuadrilla_id']} (supervisor: {d['supervisor']}).")]
        case "ServicioReprogramado":
            return [n(CLIENTE, f"Tu servicio {ref} se reprogramó para el {d['fecha']} ({d['motivo']})."),
                    n(ADMINISTRACION, f"El servicio {ref} se reprogramó para el {d['fecha']} ({d['motivo']}).")]
        case "IncidenciaRegistrada":
            avisos = [n(ADMINISTRACION, f"Incidencia {d['tipo']} en el servicio {ref}: {d['descripcion']}")]
            if d.get("cargo"):
                avisos.append(n(COORDINADOR, f"El servicio {ref} tiene un cargo adicional de ${float(d['cargo']):,.2f} "
                                             f"pendiente de autorizar."))
            return avisos
        case "CargoAdicionalAutorizado":
            return [n(ADMINISTRACION, f"Se autorizó el cargo {d['cargo_id']} por ${float(d['monto']):,.2f}.")]
        case "PrecioRecalculado":
            return [n(ADMINISTRACION, f"El precio del servicio {ref} se recalculó de ${float(d['anterior']):,.2f} "
                                      f"a ${float(d['nuevo']):,.2f} (inmueble mayor a lo reportado).")]
        case "ServicioNoRealizado":
            return [n(ADMINISTRACION, f"El servicio {ref} no se realizó por falta de acceso; "
                                      f"corresponde el cargo de cancelación del 50 %.")]
        case "ServicioTerminado":
            return [n(ADMINISTRACION, f"El servicio {ref} terminó; ya se puede facturar.")]
        case "FacturaEmitida":
            return [n(CLIENTE, f"Tu factura {ref} por ${float(d['total']):,.2f} ya está disponible.")]
        case _:
            return []
