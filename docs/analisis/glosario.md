# Glosario de dominio — CleanPro

Versión 2.0 (PIA). Los 30 términos son los de la Unidad 2. La segunda tabla agrega los términos que se corrigieron o se crearon en la Unidad 3 y en el PIA. La última columna dice cómo se llama cada concepto en el código (`src/domain`), para que el lenguaje del negocio y el del software sean el mismo (lenguaje ubicuo).

## Términos de la Unidad 2

| No. | Término | Definición | En el código |
|---|---|---|---|
| 1 | Cotización | Documento con la duración estimada, el personal necesario y el precio de un servicio, calculado con base en el inmueble, la frecuencia y los extras. | `Cotizacion` (aggregate) |
| 2 | Solicitud de cotización | Petición inicial del cliente con ubicación, superficie, tipo de inmueble, frecuencia y extras; da origen al proceso de cotización. | `EstadoCotizacion.SOLICITADA` |
| 3 | Tarifa base | Costo por metro cuadrado: $12 MXN/m² residencial y $15 MXN/m² empresarial. | `TARIFA_POR_M2` (`src/domain/precio.py`) |
| 4 | Extra | Servicio adicional a la limpieza estándar que genera un cargo según el catálogo de extras. | `ExtraSolicitado` |
| 5 | Frecuencia | Periodicidad: única o recurrente (semanal, quincenal o mensual); la recurrente tiene 10 % de descuento sobre el precio base. | `Frecuencia` |
| 6 | Vigencia de la cotización | 5 días hábiles desde el envío; después, la cotización se marca como vencida. | `Vigencia` |
| 7 | Cliente | Persona o empresa que solicita el servicio, responde la cotización y recibe el servicio y la factura. | `Cliente` |
| 8 | Coordinador | Rol que estima, envía la cotización, programa, asigna la cuadrilla y autoriza cambios, extras y reprogramaciones. | `Rol.COORDINADOR` |
| 9 | Cuadrilla | Grupo de personal asignado para ejecutar un servicio. | `Cuadrilla` |
| 10 | Supervisor | Rol que registra el inicio, la terminación y las incidencias del servicio. | `Rol.SUPERVISOR` |
| 11 | Administración | Rol que recibe las notificaciones de incidencias, registra la facturación y consulta reportes. | `Rol.ADMINISTRACION` |
| 12 | Rol | Perfil que determina las operaciones que puede realizar un usuario. | `Rol` |
| 13 | Programación del servicio | Asignación de fecha y hora para ejecutar el servicio, después de que el cliente aceptó la cotización. | `Programacion` |
| 14 | Asignación de cuadrilla | Vincular una cuadrilla disponible a un servicio programado. | `Servicio.cuadrilla_id`, `CuadrillaDisponible` |
| 15 | Ejecución del servicio | Realización del servicio entre el registro de inicio y el de terminación. | `EstadoServicio.EN_EJECUCION` |
| 16 | Registro de inicio del servicio | Anotación del supervisor de que la cuadrilla comenzó; cambia el estado a "en ejecución". | `Servicio.registrar_inicio()` |
| 17 | Registro de terminación del servicio | Anotación del supervisor de que el servicio terminó; habilita la factura. | `Servicio.registrar_terminacion()` |
| 18 | Incidencia | Evento no rutinario durante el servicio que el supervisor registra y que se notifica a administración. | `Incidencia`, `TipoIncidencia` |
| 19 | Reprogramación de última hora | Cambio de fecha u hora de un servicio programado; sin costo con 2 h o más de anticipación. | `Servicio.reprogramar()` |
| 20 | Empleado ausente | Integrante de la cuadrilla que no se presenta; obliga a reasignar personal. | `TipoIncidencia.EMPLEADO_AUSENTE` |
| 21 | Cliente no permite acceso | El cliente no permite el ingreso; tras 15 minutos, el servicio se considera no realizado. | `Servicio.registrar_acceso_denegado()` |
| 22 | Cargo de cancelación | 50 % del valor del servicio, facturado cuando no se pudo realizar por falta de acceso. | `OrigenConcepto.CANCELACION` |
| 23 | Servicio adicional en sitio | Extra solicitado durante la ejecución; lo autoriza el coordinador y lo cotiza el supervisor con el catálogo. | `TipoIncidencia.SERVICIO_ADICIONAL` |
| 24 | Catálogo de extras | Lista predefinida de extras con precios de referencia. | `CatalogoDeExtras` |
| 25 | Material especial requerido | Incidencia por un material fuera del catálogo estándar; genera un cargo que autoriza el coordinador. | `TipoIncidencia.MATERIAL_ESPECIAL` |
| 26 | Inmueble mayor a lo reportado | La superficie real excede en más de 15 % a la cotizada; obliga a recalcular el precio. | `TipoIncidencia.INMUEBLE_MAYOR` |
| 27 | Recálculo de cotización | Ajuste del precio cuando las condiciones reales del inmueble difieren de lo reportado. | `Servicio.recalcular_precio()` |
| 28 | Factura | Documento con el monto a cobrar por un servicio, incluidos los cargos de sus incidencias, y su estado de pago. | `Factura` (aggregate) |
| 29 | Reporte administrativo | Información consolidada de cotizaciones, servicios, incidencias y facturación. | `src/application/consultas.py` |
| 30 | Trazabilidad | Relación consultable entre una cotización, su servicio, sus incidencias y su factura. | Referencias por id y eventos de dominio |

## Términos corregidos o nuevos (Unidad 3 y PIA)

| Término | Cambio | Definición | Origen | En el código |
|---|---|---|---|---|
| Estado de la cotización | Corregido | Solicitada, Pendiente, Aceptada, Rechazada o Vencida. | H-03, US-22 | `EstadoCotizacion` |
| Estado del servicio | Corregido | Programado, En ejecución, Terminado o No realizado. | H-02, RB-11 | `EstadoServicio` |
| Servicio no realizado | Nuevo (U3) | Servicio que no se ejecutó porque el cliente no permitió el acceso; se factura solo el cargo de cancelación. | RB-11, H-01 | `EstadoServicio.NO_REALIZADO` |
| Cargo adicional | Nuevo (U3) | Monto asociado a un servicio adicional en sitio, a un material especial o a una reprogramación de última hora; nace pendiente y lo autoriza el coordinador. | RB-12, RB-14, H-07, H-10 | `CargoAdicional` |
| Estimación operativa | Nuevo (U3) | Duración y personal que captura el coordinador al estimar la cotización. | US-06, H-04 | `EstimacionOperativa` |
| Precio acordado | Nuevo (U3) | Precio de la cotización aceptada que se copia al servicio al programarlo. | RB-02 | `Servicio.precio_acordado` |
| Concepto facturado | Nuevo (U3) | Cada renglón de la factura: servicio, cargo adicional o cargo de cancelación. | RES-04 | `ConceptoFacturado` |
| Dinero | Nuevo (U3) | Monto en MXN con dos decimales; evita redondeos distintos en cada cálculo. | PA-02 | `Dinero` |
| Recálculo pendiente | Nuevo (PIA) | Situación de un servicio con inmueble mayor a lo reportado que todavía no tiene precio recalculado; impide registrar la terminación. | RB-13, H-09 | `Servicio.recalculo_pendiente` |
| Aviso tardío | Nuevo (PIA) | Incidencia que se registra cuando un servicio se reprograma por falta de personal con menos de 1 hora de anticipación. | RB-10, H-08 | `TipoIncidencia.AVISO_TARDIO` |
| Día hábil | Nuevo (PIA) | Lunes a viernes; se usa para calcular la vigencia de la cotización. | RB-08, H-12 | `Vigencia` |
| Estado de pago | Nuevo (PIA) | Pendiente o Pagada. | H-14 | `EstadoPago` |
| Notificación | Nuevo (PIA) | Mensaje registrado para el cliente o para administración cuando ocurre un evento del dominio. | US-03, US-19, FAL-07 | `Notificacion` |
