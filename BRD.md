# BRD — CleanPro (Business Requirements Document)

**Materia:** Componentes de Lógica de Negocio · FIME UANL
**Profesor:** Miguel Ángel Gómez Marroquín
**Equipo 12:** Roberto Carlos Sánchez Flores (2151262) · Donovan Adrian Serrato Lores (2154304) · Laura Sofía Vargas Ramírez (2152053)
**Versión:** 2.0 (PIA). Integra el BRD de la Unidad 2 (v1.0) con los hallazgos de la Unidad 3 y el refinamiento hecho para la implementación.

Documentos relacionados:
- [User Stories y criterios Gherkin](analisis/user-stories.md)
- [Glosario de dominio](analisis/glosario.md)
- [BPMN del proceso principal](analisis/bpmn.md)
- [Matriz de trazabilidad](trazabilidad.md)
- Originales de la Unidad 2: [`analisis/originales-u2/`](analisis/originales-u2)

---

## 1. Objetivo

Analizar y documentar los requerimientos de CleanPro: las necesidades, las reglas de negocio y las funcionalidades necesarias para mejorar la cotización, la programación, la asignación y la ejecución de los servicios de limpieza, así como el registro de incidencias y la facturación del servicio.

## 2. Información general

CleanPro presta servicios de limpieza residencial y empresarial. El precio del servicio depende de las características del inmueble, de la frecuencia solicitada y de los servicios adicionales (extras) que pida el cliente. El proceso principal va desde la solicitud de cotización hasta la ejecución del servicio, el registro de incidencias y la facturación.

## 3. Contexto del negocio

Cada solicitud de servicio maneja esta información:

| Elemento | Descripción |
|---|---|
| Ubicación del inmueble | Dirección donde se realizará el servicio de limpieza. |
| Superficie del inmueble | Tamaño del inmueble, utilizado para estimar la duración y el personal necesario. |
| Tipo de inmueble | Residencial o empresarial; afecta el cálculo del servicio. |
| Frecuencia | Indica si el servicio es único o recurrente. |
| Extras | Servicios adicionales solicitados además de la limpieza estándar. |
| Cuadrilla asignada | Grupo de personal de limpieza asignado para ejecutar el servicio. |
| Supervisor | Responsable de registrar el inicio, la terminación y las incidencias del servicio. |

El cliente solicita una cotización indicando la ubicación, la superficie, el tipo de inmueble, la frecuencia y los extras. El coordinador estima la duración, el personal necesario y el precio. Una vez que el cliente acepta la cotización, se programa el servicio y se asigna una cuadrilla. Durante la ejecución, el supervisor registra el inicio y la terminación del servicio y documenta las incidencias.

La fórmula de cotización, los plazos de reprogramación, las políticas de cancelación y el manejo de excepciones se obtuvieron en la entrevista simulada al stakeholder, porque el caso indica que deben descubrirse durante el levantamiento de requerimientos.

## 4. Problema actual

| ID | Problema | Descripción |
|---|---|---|
| PA-01 | Cambios no llegan a administración | Los cambios o incidencias registrados durante el servicio no llegan de forma consistente a administración. |
| PA-02 | Problemas de facturación | Se presentan errores en la facturación de los servicios prestados. |
| PA-03 | Asignaciones manuales | La asignación de cuadrillas se hace a mano, lo que genera errores o ineficiencias. |
| PA-04 | Poca evidencia de incidencias y extras | Hay poca evidencia documentada de las incidencias y de los servicios adicionales solicitados durante la ejecución. |

Estos problemas provocan pérdida de información, errores en el cobro, ineficiencia en la asignación de personal y dificultad para dar seguimiento a los servicios con incidencias.

## 5. Oportunidad de mejora

| Elemento | Oportunidad de mejora |
|---|---|
| Cotizaciones | Centralizar y estandarizar el cálculo con base en el inmueble, la frecuencia y los extras. |
| Programación de servicios | Controlar fecha, horario, cuadrilla y supervisor asignado. |
| Asignación de cuadrillas | Reducir la asignación manual para disminuir errores. |
| Registro de incidencias | Digitalizar el registro de incidencias y servicios adicionales para contar con evidencia trazable. |
| Facturación | Vincular la factura con el servicio ejecutado y sus incidencias. |
| Reportes | Generar reportes para que administración y coordinación den seguimiento a los servicios. |

## 6. Stakeholders

| Stakeholder | Participación |
|---|---|
| Cliente | Solicita la cotización, la acepta o rechaza, y recibe el servicio y la factura. |
| Coordinador | Estima el servicio, envía la cotización, programa el servicio y asigna la cuadrilla. |
| Cuadrilla | Ejecuta el servicio de limpieza en el inmueble del cliente. |
| Supervisor | Registra el inicio y la terminación del servicio, y documenta incidencias o cambios. |
| Administración | Recibe notificaciones de incidencias, registra el servicio y gestiona la facturación. |

## 7. Alcance

| ID | Elemento | Descripción |
|---|---|---|
| ALC-01 | Registro y consulta de cotizaciones | Generar, consultar y dar seguimiento a las cotizaciones. |
| ALC-02 | Estimación del servicio | Calcular la duración, el personal necesario y el precio. |
| ALC-03 | Aceptación de la cotización | Registrar la decisión del cliente de aceptar o rechazar la cotización. |
| ALC-04 | Programación de servicios | Programar el servicio una vez aceptada la cotización. |
| ALC-05 | Asignación de cuadrillas | Asignar y consultar la cuadrilla responsable de cada servicio. |
| ALC-06 | Registro de ejecución | Registrar el inicio y la terminación del servicio. |
| ALC-07 | Registro de incidencias y cambios | Documentar incidencias, cambios o servicios adicionales durante la ejecución. |
| ALC-08 | Notificación a administración | Notificar a administración las incidencias o cambios registrados. |
| ALC-09 | Facturación del servicio | Registrar y consultar la facturación de cada servicio. |
| ALC-10 | Reportes administrativos | Generar información para el seguimiento de servicios, incidencias y facturación. |

## 8. Fuera del alcance

| ID | Elemento | Descripción |
|---|---|---|
| FAL-01 | Nómina del personal | No se administran sueldos ni nómina. |
| FAL-02 | Contratación de personal | No se incluye el reclutamiento de cuadrillas ni supervisores. |
| FAL-03 | Contabilidad general | No se contempla la contabilidad general de la empresa. |
| FAL-04 | Compra de materiales e insumos | No se incluye la adquisición de productos de limpieza. |
| FAL-05 | Otros procesos administrativos | No se contemplan procesos no relacionados con cotización, programación, ejecución y facturación. |
| FAL-06 *(PIA)* | Autenticación de usuarios | No hay inicio de sesión. El rol de quien opera se indica en cada solicitud a la API (ver H-13). |
| FAL-07 *(PIA)* | Envío real de mensajes | Las notificaciones al cliente y a administración se registran en el sistema y se consultan por la API; no se envían correos ni SMS. |
| FAL-08 *(PIA)* | Cobro en línea | Administración registra el pago de la factura; no hay pasarela de pago. |

## 9. Necesidades del negocio

| ID | Necesidad |
|---|---|
| BN-01 | Gestionar la solicitud y el cálculo de cotizaciones. |
| BN-02 | Registrar la aceptación o rechazo de la cotización por parte del cliente. |
| BN-03 | Programar los servicios aceptados y asignar una cuadrilla. |
| BN-04 | Registrar el inicio y la terminación de cada servicio. |
| BN-05 | Registrar incidencias y cambios ocurridos durante el servicio. |
| BN-06 | Notificar oportunamente a administración sobre incidencias y cambios. |
| BN-07 | Registrar y dar seguimiento a la facturación de cada servicio. |
| BN-08 | Mantener evidencia trazable de incidencias y servicios adicionales. |
| BN-09 | Reducir la asignación manual de cuadrillas. |
| BN-10 | Generar reportes para administración sobre el estado de los servicios. |

## 10. Reglas de negocio

| Regla | Descripción |
|---|---|
| **RB-01** Cotización previa | El coordinador debe estimar y enviar una cotización al cliente antes de programar cualquier servicio. |
| **RB-02** Aceptación del cliente | El servicio solo se programa si el cliente acepta la cotización enviada. |
| **RB-03** Cálculo de la cotización | El precio es la tarifa base según el tipo de inmueble y su superficie ($12 MXN por m² residencial y $15 MXN por m² empresarial) más un cargo fijo por cada extra solicitado. La frecuencia recurrente (semanal, quincenal o mensual) recibe un descuento del 10 % sobre el precio base. |
| **RB-04** Asignación de cuadrilla | Todo servicio programado debe tener una cuadrilla asignada antes de su ejecución. |
| **RB-05** Registro de ejecución | El supervisor registra el inicio y la terminación de cada servicio. |
| **RB-06** Registro de incidencias | Cualquier incidencia o cambio durante el servicio debe quedar documentado y notificado a administración. |
| **RB-07** Facturación posterior al servicio | El servicio debe quedar registrado como terminado antes de generar la factura. |
| **RB-08** Vigencia de la cotización | La cotización tiene una vigencia de 5 días hábiles a partir de su envío. Si no se acepta en ese plazo, el coordinador debe generar una nueva. |
| **RB-09** Reprogramación de última hora | El cliente puede reprogramar sin costo hasta con 2 horas de anticipación. Con menor anticipación puede generarse un cargo por reprogramación, sujeto a la disponibilidad de cuadrilla. |
| **RB-10** Empleado ausente | Si un integrante de la cuadrilla falta, el coordinador debe reasignar personal antes de la hora programada. Si no es posible completar la cuadrilla, el servicio se reprograma y se notifica al cliente con al menos 1 hora de anticipación. |
| **RB-11** Cliente no permite acceso | Si el cliente no permite el acceso, el supervisor registra la incidencia y espera hasta 15 minutos. Después de ese tiempo, el servicio se considera no realizado y se factura un cargo de cancelación del 50 % del valor del servicio. |
| **RB-12** Servicio adicional en sitio | Un servicio adicional solicitado durante la ejecución debe autorizarlo el coordinador antes de realizarse. El supervisor lo cotiza con el catálogo de extras y lo registra como incidencia. |
| **RB-13** Inmueble mayor a lo reportado | Si la superficie real excede en más de 15 % a la reportada, el supervisor notifica al coordinador para recalcular el precio antes de continuar con el servicio. |
| **RB-14** Material especial requerido | Si el servicio requiere material especial fuera del catálogo estándar, el supervisor registra la incidencia y el coordinador debe autorizar el cargo adicional antes de facturar. |
| **RB-15** Roles de autorización | El coordinador es el único rol que modifica una cotización, aprueba cargos adicionales y autoriza reprogramaciones. Administración no interviene en la operación diaria, solo en el registro financiero y en los reportes. |

## 11. Restricciones

| ID | Restricción | Descripción |
|---|---|---|
| RES-01 | Disponibilidad de cuadrillas | El servicio no puede programarse sin una cuadrilla disponible para la fecha solicitada. |
| RES-02 | Aceptación previa del cliente | Ningún servicio se programa sin que el cliente haya aceptado la cotización. |
| RES-03 | Registro de incidencias | Las incidencias deben quedar documentadas antes de registrar la terminación del servicio. |
| RES-04 | Trazabilidad de la facturación | La factura debe estar vinculada al servicio y a sus incidencias para evitar errores de cobro. |
| RES-05 | Vigencia de la cotización | La cotización debe aceptarse dentro de los 5 días hábiles siguientes a su envío; si no, se genera una nueva. |
| RES-06 | Tiempo de espera en sitio | La cuadrilla espera un máximo de 15 minutos si el cliente no permite el acceso. |

## 12. Supuestos

| ID | Supuesto | Descripción |
|---|---|---|
| SUP-01 | Una cuadrilla por servicio | Cada servicio programado tiene exactamente una cuadrilla. |
| SUP-02 | Un supervisor por servicio | Cada servicio tiene un supervisor responsable de registrar su ejecución. |
| SUP-03 | Incidencia asociada a un servicio | Cada incidencia corresponde a un único servicio. |
| SUP-04 | Facturación única por servicio | La factura se genera después de que el servicio termina, y solo existe una factura por servicio. |
| SUP-05 | Proceso único para todo tipo de cliente | Clientes residenciales y empresariales siguen el mismo proceso. |
| SUP-06 | Catálogo de extras | CleanPro tiene un catálogo predefinido de extras con precios de referencia, que también usa el supervisor para cotizar servicios adicionales en sitio. |

## 13. Situaciones excepcionales

| Situación | Acción |
|---|---|
| Empleado ausente | El coordinador reasigna personal antes de la hora programada (RB-10). Si no se completa la cuadrilla, se reprograma y se notifica al cliente con al menos 1 hora de anticipación. |
| Cliente no permite acceso | El supervisor registra la incidencia y espera hasta 15 minutos; después, se factura un cargo de cancelación del 50 % (RB-11). |
| Servicio adicional en sitio | El coordinador lo autoriza, el supervisor lo cotiza con el catálogo de extras y lo registra como incidencia (RB-12). |
| Inmueble mayor a lo reportado | Si la diferencia supera el 15 %, el supervisor notifica al coordinador para recalcular el precio (RB-13). |
| Material especial requerido | El supervisor registra la incidencia y el coordinador autoriza el cargo antes de facturar (RB-14). |
| Reprogramación de última hora | Sin costo con 2 horas o más de anticipación (RB-09); con menos, puede generar un cargo, sujeto a disponibilidad de cuadrilla. |

## 14. Información y datos principales

| Dato | Información |
|---|---|
| Cliente | Datos de contacto, ubicación del inmueble, historial de servicios. |
| Cotización | Ubicación, superficie, tipo de inmueble, frecuencia, extras, duración estimada, personal necesario, precio y estado. |
| Servicio | Cotización asociada, fecha y hora, cuadrilla, supervisor y estado. |
| Incidencia | Servicio asociado, tipo, descripción, fecha y hora, y persona que la registra. |
| Factura | Servicio asociado, monto, fecha de emisión y estado de pago. |

Los estados se refinaron en la sección 18 (H-02, H-03).

## 15. Reportes requeridos

| ID | Reporte | Descripción |
|---|---|---|
| REP-01 | Cotizaciones por estado | Cotizaciones pendientes, aceptadas, rechazadas y vencidas. |
| REP-02 | Servicios programados | Servicios programados con su cuadrilla y supervisor. |
| REP-03 | Incidencias registradas | Incidencias documentadas por servicio. |
| REP-04 | Facturación por servicio | Estado de facturación y pago de cada servicio. |
| REP-05 | Servicios por cuadrilla | Carga de trabajo de cada cuadrilla. |

## 16. Prioridades del negocio

| Prioridad | Necesidades asociadas |
|---|---|
| Alta | Reducir errores de facturación. Mejorar la trazabilidad de incidencias y servicios adicionales. Reducir la asignación manual de cuadrillas. |
| Media | Mejorar el seguimiento de reprogramaciones y cambios. Facilitar el acceso de administración a los reportes. |

## 17. Criterios de éxito

| ID | Criterio | Descripción |
|---|---|---|
| CE-01 | Reducción de errores de facturación | Disminuir los errores en la facturación de los servicios. |
| CE-02 | Trazabilidad de incidencias | Evidencia documentada de todas las incidencias y servicios adicionales. |
| CE-03 | Reducción de asignación manual | Disminuir la dependencia de la asignación manual de cuadrillas. |
| CE-04 | Comunicación oportuna de cambios | Los cambios e incidencias llegan oportunamente a administración. |
| CE-05 | Visibilidad del estado del servicio | Consultar rápidamente el estado de cualquier servicio (cotizado, programado, ejecutado, facturado). |

---

## 18. Refinamiento para el PIA

Al convertir el análisis en software aparecieron huecos y contradicciones. **No se agregan reglas nuevas**: cada ajuste aclara una regla existente o registra un supuesto aceptado por el equipo. Los hallazgos H-01 a H-06 vienen de la Unidad 3; H-07 a H-15 se identificaron al implementar.

| ID | Hallazgo | Regla | Decisión del equipo |
|---|---|---|---|
| H-01 | RB-07 solo factura servicios terminados, pero RB-11 factura el 50 % de un servicio **no realizado**. | RB-07, RB-11 | Un servicio es facturable si está **Terminado** o **No realizado**. |
| H-02 | Los estados del servicio no incluían "no realizado". | RB-11 | Estados del servicio: **Programado → En ejecución → Terminado**, o **Programado → No realizado**. |
| H-03 | Los estados de la cotización no incluían "vencida" ni el momento anterior al envío. | RB-08, US-22 | Estados de la cotización: **Solicitada → Pendiente → Aceptada / Rechazada / Vencida**. |
| H-04 | US-06 pide calcular duración y personal, pero el BRD solo da la fórmula del precio. | RB-03 | El coordinador captura la duración (horas) y el personal; el sistema calcula el precio. |
| H-05 | No es claro si el 10 % se descuenta también de los extras. | RB-03 | El descuento se aplica solo a superficie × tarifa; los extras no se descuentan. |
| H-06 | No se define si una cotización recurrente genera varios servicios. | RB-03, SUP-01 | Cada programación crea un solo servicio. La generación automática de servicios recurrentes queda fuera del alcance. |
| H-07 | RB-09 no fija el monto del cargo por reprogramación de última hora. | RB-09, RB-15 | Con 2 h o más de anticipación, la reprogramación es sin costo. Con menos de 2 h, solo el coordinador la autoriza y captura el monto del cargo (puede ser 0), que se agrega a la factura. |
| H-08 | RB-10 no dice qué pasa si la reprogramación por ausencia se avisa con menos de 1 h. | RB-10 | El sistema permite reprogramar, pero registra una incidencia de **aviso tardío** para que administración la vea. |
| H-09 | RB-13 dice "más de 15 %". | RB-13 | Una diferencia de exactamente 15 % no obliga a recalcular. Mientras haya un recálculo pendiente, el servicio no puede registrar su terminación. El recálculo usa la fórmula de RB-03 con la superficie real. |
| H-10 | RB-12 y RB-14 generan cargos de origen distinto. | RB-12, RB-14 | Servicio adicional en sitio: el monto se toma del **catálogo de extras**. Material especial: el supervisor captura el monto porque no está en el catálogo. En ambos casos el cargo nace **pendiente** y solo el coordinador lo autoriza. |
| H-11 | SUP-06 no define el contenido del catálogo de extras. | SUP-06 | Catálogo de ejemplo (caso ficticio): ventanas $250, refrigerador $180, alfombra $300, horno $200 y muebles tapizados $350. |
| H-12 | RB-08 no define "día hábil". | RB-08 | Días hábiles = lunes a viernes, sin considerar días festivos. La cotización vence al terminar el 5.º día hábil después del envío. |
| H-13 | RB-15 exige roles, pero no hay sistema de usuarios. | RB-15, FAL-06 | Cada operación de la API indica el rol que la realiza (encabezado `X-Rol`) y el dominio valida el permiso. |
| H-14 | El BRD menciona el estado de pago, pero no sus valores. | Datos de factura | Estado de pago: **Pendiente → Pagada**. Solo administración registra el pago. |
| H-15 | RES-01 no define cuándo una cuadrilla está "disponible". | RES-01, SUP-01 | Una cuadrilla está ocupada durante la duración estimada de cada servicio programado. Si el horario de un servicio nuevo se cruza con otro de la misma cuadrilla, la cuadrilla no está disponible. |

### Relación con el paquete de datos del PIA

El paquete de datos entregado por el docente propone un modelo genérico (estados SOLICITADO → PROGRAMADO → EN_PROCESO → COMPLETADO / CANCELADO y una regla de beneficio por referencia). Ese modelo se usó en la Actividad 5 para practicar Specification y pruebas. El PIA implementa el **BRD del equipo**, como indica el documento del PIA, y solo toma del paquete los 40 clientes de ejemplo (con la bandera `activo`) para cargar datos de demostración. Un cliente inactivo no puede solicitar cotizaciones; esta precondición se tomó del paquete y no contradice ninguna regla del BRD.
