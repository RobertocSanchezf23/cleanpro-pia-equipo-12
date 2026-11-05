# User Stories y criterios de aceptación (Gherkin) — CleanPro

Versión 2.0 (PIA). Las 22 historias y sus criterios originales son los de la Unidad 2. Los escenarios marcados **(PIA)** se agregaron al refinar el análisis: cubren los casos de error y los límites que se aclararon en la sección 18 del [BRD](../BRD.md). Ninguno agrega reglas nuevas.

En la [matriz de trazabilidad](../trazabilidad.md) cada escenario se relaciona con su regla, su endpoint, su código y su prueba.

## Historias

| ID | Rol | Historia | Reglas |
|---|---|---|---|
| US-01 | Cliente | Quiero solicitar una cotización indicando la ubicación, superficie, tipo de inmueble, frecuencia y extras, para conocer el costo y la duración estimada del servicio. | RB-01, SUP-06 |
| US-02 | Cliente | Quiero aceptar o rechazar la cotización recibida, para confirmar si deseo contratar el servicio. | RB-02, RB-08 |
| US-03 | Cliente | Quiero recibir confirmación de la programación de mi servicio, para saber la fecha y hora en que se realizará. | RB-02 |
| US-04 | Cliente | Quiero solicitar una reprogramación de mi servicio, para ajustar la fecha u hora si tengo un inconveniente. | RB-09, RB-15 |
| US-05 | Cliente | Quiero recibir mi factura al finalizar el servicio, para conocer el monto a pagar. | RB-07, RES-04 |
| US-06 | Coordinador | Quiero estimar la duración, el personal necesario y el precio de un servicio solicitado, para generar la cotización. | RB-03, RB-15 |
| US-07 | Coordinador | Quiero enviar la cotización al cliente, para que pueda aceptarla o rechazarla. | RB-01, RB-08 |
| US-08 | Coordinador | Quiero programar el servicio una vez aceptada la cotización, para asignar la fecha y hora de ejecución. | RB-02, RES-02 |
| US-09 | Coordinador | Quiero asignar una cuadrilla disponible a cada servicio programado, para asegurar su ejecución. | RB-04, RES-01, SUP-01 |
| US-10 | Coordinador | Quiero reasignar personal a una cuadrilla cuando un integrante esté ausente, para no afectar el servicio programado. | RB-10 |
| US-11 | Coordinador | Quiero autorizar servicios adicionales solicitados en sitio, para que puedan cotizarse y realizarse durante el servicio. | RB-12, RB-15 |
| US-12 | Coordinador | Quiero recalcular la cotización cuando el inmueble sea mayor a lo reportado, para reflejar el precio correcto. | RB-13, RB-03 |
| US-13 | Supervisor | Quiero registrar el inicio del servicio, para dejar evidencia de que la cuadrilla comenzó a trabajar. | RB-05 |
| US-14 | Supervisor | Quiero registrar la terminación del servicio, para dejar evidencia de que el servicio fue completado. | RB-05, RES-03 |
| US-15 | Supervisor | Quiero registrar incidencias o cambios ocurridos durante el servicio, para mantener evidencia de lo sucedido. | RB-06, SUP-03 |
| US-16 | Supervisor | Quiero registrar cuando un cliente no permite el acceso al inmueble, para documentar la incidencia y aplicar el cargo. | RB-11, RES-06 |
| US-17 | Integrante de cuadrilla | Quiero consultar los servicios que tengo asignados, para saber en qué inmuebles debo realizar la limpieza. | REP-05 |
| US-18 | Integrante de cuadrilla | Quiero ejecutar el servicio de limpieza asignado, para cumplir con lo solicitado por el cliente. | RB-05 |
| US-19 | Administración | Quiero recibir notificación de las incidencias registradas por el supervisor, para darles seguimiento oportuno. | RB-06 |
| US-20 | Administración | Quiero registrar la facturación de cada servicio terminado, para llevar el control de los cobros. | RB-07, RB-14, SUP-04 |
| US-21 | Administración | Quiero consultar reportes del estado de los servicios, las incidencias y la facturación, para dar seguimiento a la operación. | REP-01 a REP-05 |
| US-22 | Coordinador | Quiero que las cotizaciones no aceptadas después de 5 días hábiles queden marcadas como vencidas, para saber cuáles requieren una nueva estimación. | RB-08, RES-05 |

## Criterios de aceptación

### US-01 — Solicitar cotización
```gherkin
Feature: Solicitar cotización

  Scenario: US-01 E1 · Registrar la solicitud
    Given que el cliente proporciona la ubicación, superficie, tipo de inmueble, frecuencia y extras
    When solicita una cotización
    Then el sistema debe registrar la solicitud y ponerla disponible para que el coordinador la estime

  Scenario: US-01 E2 (PIA) · Extra fuera del catálogo
    Given que el cliente pide un extra que no existe en el catálogo de extras
    When solicita una cotización
    Then el sistema rechaza la solicitud indicando que el extra no está en el catálogo

  Scenario: US-01 E3 (PIA) · Cliente inactivo
    Given que el cliente está marcado como inactivo
    When solicita una cotización
    Then el sistema rechaza la solicitud
```

### US-02 — Aceptar o rechazar cotización
```gherkin
Feature: Responder cotización

  Scenario: US-02 E1 · Aceptar o rechazar
    Given que el cliente recibió una cotización con estado pendiente
    When acepta o rechaza la cotización
    Then el sistema debe actualizar el estado de la cotización a "aceptada" o "rechazada" según corresponda

  Scenario: US-02 E2 (PIA) · Responder una cotización que no está pendiente
    Given que la cotización ya fue aceptada, rechazada o todavía no se envía
    When el cliente intenta responderla
    Then el sistema rechaza la operación y la cotización conserva su estado
```

### US-03 — Confirmación de programación
```gherkin
Feature: Confirmación de programación

  Scenario: US-03 E1 · Notificar al cliente
    Given que la cotización fue aceptada por el cliente
    When el coordinador programa el servicio
    Then el cliente debe recibir la fecha, hora y cuadrilla asignada al servicio
```

### US-04 — Solicitar reprogramación
```gherkin
Feature: Reprogramar servicio

  Scenario: US-04 E1 · Con al menos 2 horas de anticipación
    Given que el cliente tiene un servicio programado
    When solicita una reprogramación con al menos 2 horas de anticipación
    Then el servicio debe reprogramarse sin costo adicional

  Scenario: US-04 E2 · Con menos de 2 horas de anticipación
    Given que el cliente solicita la reprogramación con menos de 2 horas de anticipación
    When el coordinador evalúa la solicitud
    Then el sistema debe indicar que puede aplicar un cargo por reprogramación, sujeto a disponibilidad de cuadrilla

  Scenario: US-04 E3 (PIA) · Solo el coordinador autoriza la reprogramación de última hora
    Given que la reprogramación se solicita con menos de 2 horas de anticipación
    When un rol distinto al coordinador intenta autorizarla
    Then el sistema rechaza la operación

  Scenario: US-04 E4 (PIA) · Nueva fecha sin cuadrilla disponible
    Given que la cuadrilla ya tiene otro servicio en el nuevo horario
    When se intenta reprogramar
    Then el sistema rechaza la reprogramación
```

### US-05 — Recibir factura
```gherkin
Feature: Recibir factura

  Scenario: US-05 E1 · Monto del servicio y sus incidencias
    Given que el servicio fue registrado como terminado
    When administración genera la factura
    Then el cliente debe recibir el monto correspondiente al servicio y a las incidencias registradas
```

### US-06 — Estimar servicio
```gherkin
Feature: Estimar servicio

  Scenario: US-06 E1 · Calcular el precio
    Given que existe una solicitud de cotización con ubicación, superficie, tipo de inmueble, frecuencia y extras
    When el coordinador estima el servicio
    Then el sistema debe calcular la duración, el personal necesario y el precio con base en la tarifa por tipo de inmueble, la frecuencia y los extras

  Scenario: US-06 E2 (PIA) · Inmueble residencial con frecuencia única
    Given una solicitud residencial de 100 m², frecuencia única y el extra "ventanas"
    When el coordinador estima el servicio
    Then el precio es 100 × $12 + $250 = $1,450.00

  Scenario: US-06 E3 (PIA) · Inmueble empresarial recurrente
    Given una solicitud empresarial de 200 m², frecuencia semanal y el extra "alfombra"
    When el coordinador estima el servicio
    Then el precio es 200 × $15 × 0.90 + $300 = $3,000.00

  Scenario: US-06 E4 (PIA) · Solo el coordinador estima
    Given una solicitud de cotización
    When un rol distinto al coordinador intenta estimarla
    Then el sistema rechaza la operación
```

### US-07 — Enviar cotización
```gherkin
Feature: Enviar cotización

  Scenario: US-07 E1 · Queda pendiente
    Given que el coordinador terminó de estimar el servicio
    When envía la cotización al cliente
    Then la cotización debe quedar con estado "pendiente" hasta que el cliente responda

  Scenario: US-07 E2 (PIA) · No se envía sin estimar
    Given una cotización que todavía no tiene precio calculado
    When el coordinador intenta enviarla
    Then el sistema rechaza el envío
```

### US-08 — Programar servicio
```gherkin
Feature: Programar servicio

  Scenario: US-08 E1 · Cotización aceptada
    Given que el cliente aceptó la cotización
    When el coordinador programa el servicio
    Then debe registrarse la fecha y hora del servicio con estado "programado"

  Scenario: US-08 E2 (PIA) · Cotización no aceptada
    Given una cotización pendiente, rechazada o vencida
    When el coordinador intenta programar el servicio
    Then el sistema rechaza la programación

  Scenario: US-08 E3 (PIA) · Una cotización solo genera un servicio
    Given una cotización aceptada que ya tiene un servicio programado
    When el coordinador intenta programarla otra vez
    Then el sistema rechaza la programación
```

### US-09 — Asignar cuadrilla
```gherkin
Feature: Asignar cuadrilla

  Scenario: US-09 E1 · Cuadrilla disponible
    Given que un servicio está programado
    When el coordinador asigna una cuadrilla disponible
    Then el servicio debe quedar vinculado a esa cuadrilla antes de la fecha de ejecución

  Scenario: US-09 E2 (PIA) · Cuadrilla ocupada
    Given que la cuadrilla tiene otro servicio cuyo horario se cruza con el nuevo
    When el coordinador intenta asignarla
    Then el sistema rechaza la asignación
```

### US-10 — Reasignar personal por ausencia
```gherkin
Feature: Reasignar personal por ausencia

  Scenario: US-10 E1 · Se completa la cuadrilla
    Given que un integrante de la cuadrilla está ausente el día del servicio
    When el coordinador reasigna personal disponible antes de la hora programada
    Then el servicio debe poder ejecutarse con la cuadrilla completa

  Scenario: US-10 E2 · No se completa la cuadrilla
    Given que no es posible completar la cuadrilla
    When el coordinador no logra reasignar personal
    Then el servicio debe reprogramarse y el cliente debe ser notificado con al menos 1 hora de anticipación

  Scenario: US-10 E3 (PIA) · Aviso con menos de 1 hora
    Given que faltan menos de 60 minutos para el servicio
    When el coordinador lo reprograma por falta de personal
    Then el servicio se reprograma y queda registrada una incidencia de aviso tardío
```

### US-11 — Autorizar servicio adicional en sitio
```gherkin
Feature: Autorizar servicio adicional en sitio

  Scenario: US-11 E1 · Autorización del coordinador
    Given que la cuadrilla solicita un servicio adicional durante la ejecución
    When el coordinador autoriza el servicio adicional
    Then el supervisor debe poder cotizarlo con el catálogo de extras y registrarlo como incidencia

  Scenario: US-11 E2 (PIA) · Solo el coordinador autoriza
    Given un cargo adicional pendiente
    When el supervisor o administración intentan autorizarlo
    Then el sistema rechaza la operación y el cargo sigue pendiente
```

### US-12 — Recalcular cotización por inmueble mayor
```gherkin
Feature: Recalcular por inmueble mayor

  Scenario: US-12 E1 · Más de 15 % de diferencia
    Given que la superficie real del inmueble excede en más de 15% a la reportada
    When el supervisor notifica al coordinador
    Then el coordinador debe recalcular el precio del servicio antes de continuar

  Scenario: US-12 E2 (PIA) · Exactamente 15 %
    Given una cotización de 100 m²
    When el supervisor reporta una superficie real de 115 m²
    Then no se exige recalcular el precio

  Scenario: US-12 E3 (PIA) · No se termina con recálculo pendiente
    Given un servicio con un recálculo de precio pendiente
    When el supervisor intenta registrar la terminación
    Then el sistema rechaza la terminación
```

### US-13 — Registrar inicio del servicio
```gherkin
Feature: Registrar inicio

  Scenario: US-13 E1 · Inicio
    Given que la cuadrilla asignada llegó al inmueble
    When el supervisor registra el inicio del servicio
    Then el estado del servicio debe cambiar a "en ejecución"

  Scenario: US-13 E2 (PIA) · Solo desde programado
    Given un servicio que no está programado
    When el supervisor intenta registrar el inicio
    Then el sistema rechaza la transición
```

### US-14 — Registrar terminación del servicio
```gherkin
Feature: Registrar terminación

  Scenario: US-14 E1 · Terminación
    Given que el servicio está en ejecución
    When el supervisor registra la terminación
    Then el estado del servicio debe cambiar a "terminado" y debe habilitarse la facturación

  Scenario: US-14 E2 (PIA) · Solo desde en ejecución
    Given un servicio programado que no ha iniciado
    When el supervisor intenta registrar la terminación
    Then el sistema rechaza la transición
```

### US-15 — Registrar incidencias
```gherkin
Feature: Registrar incidencias

  Scenario: US-15 E1 · Incidencia asociada y notificada
    Given que ocurre un cambio o incidencia durante el servicio
    When el supervisor la registra
    Then la incidencia debe quedar asociada al servicio y notificarse a administración
```

### US-16 — Cliente no permite acceso
```gherkin
Feature: Cliente no permite acceso

  Scenario: US-16 E1 · Después de 15 minutos
    Given que el cliente no permite el acceso al inmueble en la hora programada
    When el supervisor espera hasta 15 minutos sin obtener acceso
    Then el servicio debe marcarse como no realizado y facturarse un cargo de cancelación del 50%

  Scenario: US-16 E2 (PIA) · Antes de 15 minutos
    Given que el supervisor ha esperado 14 minutos
    When intenta marcar el servicio como no realizado
    Then el sistema rechaza la operación y el servicio sigue programado
```

### US-17 — Consultar servicios asignados
```gherkin
Feature: Consultar servicios asignados

  Scenario: US-17 E1 · Lista de la cuadrilla
    Given que la cuadrilla tiene servicios asignados
    When consulta su lista de servicios
    Then debe visualizar los servicios programados con fecha, hora y ubicación del inmueble
```

### US-18 — Ejecutar servicio de limpieza
```gherkin
Feature: Ejecutar servicio

  Scenario: US-18 E1 · Terminar al finalizar
    Given que el servicio fue registrado como iniciado
    When la cuadrilla realiza la limpieza del inmueble
    Then el servicio debe poder marcarse como terminado por el supervisor al finalizar
```

### US-19 — Notificación de incidencias a administración
```gherkin
Feature: Notificar incidencias

  Scenario: US-19 E1 · Notificación al guardar
    Given que el supervisor registró una incidencia
    When se guarda el registro
    Then administración debe recibir la notificación correspondiente
```

### US-20 — Registrar facturación
```gherkin
Feature: Registrar facturación

  Scenario: US-20 E1 · Factura vinculada
    Given que el servicio fue registrado como terminado
    When administración registra la facturación
    Then la factura debe quedar vinculada al servicio y a sus incidencias, con su estado de pago

  Scenario: US-20 E2 (PIA) · Servicio no terminado
    Given un servicio programado o en ejecución
    When administración intenta facturarlo
    Then el sistema rechaza la factura

  Scenario: US-20 E3 (PIA) · Cargos sin autorizar
    Given un servicio terminado con un cargo adicional pendiente de autorizar
    When administración intenta facturarlo
    Then el sistema rechaza la factura

  Scenario: US-20 E4 (PIA) · Una sola factura por servicio
    Given un servicio que ya tiene factura
    When administración intenta facturarlo de nuevo
    Then el sistema rechaza la segunda factura

  Scenario: US-20 E5 (PIA) · Registrar el pago
    Given una factura con estado de pago pendiente
    When administración registra el pago
    Then el estado de pago cambia a "pagada"
```

### US-21 — Consultar reportes
```gherkin
Feature: Consultar reportes

  Scenario: US-21 E1 · Estado de la operación
    Given que existen servicios, incidencias y facturas registradas
    When administración consulta los reportes
    Then debe poder visualizar el estado de los servicios, las incidencias y la facturación
```

### US-22 — Cotización vencida
```gherkin
Feature: Cotización vencida

  Scenario: US-22 E1 · Más de 5 días hábiles
    Given que una cotización lleva más de 5 días hábiles sin ser aceptada
    When el coordinador la consulta
    Then el sistema debe marcarla como vencida y permitir generar una nueva

  Scenario: US-22 E2 (PIA) · Fin de semana
    Given una cotización enviada un viernes
    When el cliente la acepta el jueves siguiente
    Then la cotización sigue vigente, porque solo han pasado 4 días hábiles
```

## Relación entre necesidades e historias

| Necesidad | User Stories |
|---|---|
| BN-01 Gestionar la solicitud y el cálculo de cotizaciones | US-01, US-06, US-07, US-22 |
| BN-02 Registrar la aceptación o rechazo de la cotización | US-02 |
| BN-03 Programar los servicios aceptados y asignar cuadrilla | US-03, US-04, US-08, US-09 |
| BN-04 Registrar el inicio y la terminación del servicio | US-13, US-14, US-17, US-18 |
| BN-05 Registrar incidencias y cambios durante el servicio | US-11, US-12, US-15, US-16 |
| BN-06 Notificar oportunamente a administración | US-19 |
| BN-07 Registrar y dar seguimiento a la facturación | US-05, US-20 |
| BN-08 Mantener evidencia trazable de incidencias y extras | US-11, US-15 |
| BN-09 Reducir la asignación manual de cuadrillas | US-09, US-10 |
| BN-10 Generar reportes para administración | US-21 |
