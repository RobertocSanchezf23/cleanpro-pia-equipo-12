# Matriz de trazabilidad — análisis → arquitectura → código → pruebas

Cada regla del [BRD](BRD.md) y cada escenario Gherkin de las [User Stories](analisis/user-stories.md) se puede seguir hasta el código que la implementa y la prueba que la verifica. Las pruebas llevan en su nombre el escenario que cubren (por ejemplo, `test_us06_e2_...` cubre "US-06 E2").

La prueba `tests/test_trazabilidad.py` revisa automáticamente que **todos** los escenarios de las User Stories aparezcan en esta matriz y que **todas** las pruebas mencionadas aquí existan. Si alguien agrega un escenario sin prueba, el pipeline falla.

## 1. Problemas del negocio → solución

| Problema (BRD) | Cómo lo resuelve el sistema | Criterio de éxito |
|---|---|---|
| PA-01 Cambios no llegan a administración | Evento `IncidenciaRegistrada` → aviso a administración guardado en la misma transacción (ADR-010); `GET /notificaciones` | CE-04 |
| PA-02 Problemas de facturación | Precio en un solo lugar (`CalculadoraDePrecio`), `Dinero` con `Decimal`, `SERVICIO_FACTURABLE`, una factura por servicio | CE-01 |
| PA-03 Asignaciones manuales | `CuadrillaDisponible` y `CuadrillaActiva` impiden asignar una cuadrilla ocupada o inactiva; REP-05 muestra la carga | CE-03 |
| PA-04 Poca evidencia de incidencias y extras | Incidencias inmutables dentro del servicio; cada cargo referenciado en la factura (RES-04); REP-03 | CE-02 |
| CE-05 Visibilidad del estado | Máquinas de estados + `GET /servicios`, `/cotizaciones`, `/reportes/resumen` | CE-05 |

## 2. Reglas de negocio → código → pruebas

| Regla | Dónde se implementa | Pruebas principales |
|---|---|---|
| RB-01 Cotización previa | `Cotizacion.enviar()` + `TienePrecio` | `test_us07_e2_no_se_envia_sin_estimar`, `test_us07_e2_enviar_sin_estimar_responde_422` |
| RB-02 Aceptación del cliente | `CotizacionAceptada` en `PUEDE_PROGRAMARSE` | `test_us08_e2_cotizacion_no_aceptada_no_se_programa`, `test_bpmn_cotizacion_rechazada_no_genera_servicio` |
| RB-03 Cálculo de la cotización | `CalculadoraDePrecio` (`src/domain/precio.py`) | `test_us06_e2_residencial_100m2_unica_con_ventanas_cuesta_1450`, `test_us06_e3_empresarial_200m2_semanal_con_alfombra_cuesta_3000`, `test_h05_el_descuento_recurrente_no_se_aplica_a_los_extras` |
| RB-04 Asignación de cuadrilla | `CuadrillaActiva` + cuadrilla obligatoria en `Servicio.programar()` | `test_rb04_cuadrilla_inactiva_no_se_asigna`, `test_us09_e2_cuadrilla_ocupada_y_rb04_cuadrilla_inactiva` |
| RB-05 Registro de ejecución | `registrar_inicio()`, `registrar_terminacion()` (solo supervisor) | `test_rb05_solo_el_supervisor_registra_inicio_y_terminacion`, `test_us13_e1_registrar_inicio_cambia_a_en_ejecucion` |
| RB-06 Registro de incidencias | `Servicio.registrar_incidencia()` + evento + aviso | `test_us15_e1_la_incidencia_queda_asociada_y_genera_evento_para_administracion`, `test_us19_e1_incidencia_avisa_a_administracion` |
| RB-07 Facturación posterior | `EstaTerminado` / `EstaNoRealizado` en `SERVICIO_FACTURABLE` | `test_us20_e2_servicio_no_terminado_no_se_factura`, `test_us20_us05_facturar_y_pagar` |
| RB-08 Vigencia | `Vigencia` (5 días hábiles), `EstaVigente`, `actualizar_vencimiento()` | `test_us22_e1_pendiente_despues_de_5_dias_habiles_queda_vencida`, `test_rb08_aceptar_fuera_de_vigencia_se_rechaza`, `test_us22_aceptar_despues_de_5_dias_habiles_la_deja_vencida` |
| RB-09 Reprogramación de última hora | `Servicio.reprogramar()` (2 h, cargo, rol) | `test_us04_e1_exactamente_2_horas_antes_sigue_siendo_sin_costo`, `test_us04_e2_con_menos_de_2_horas_el_coordinador_aplica_cargo`, `test_rb09_con_2_horas_o_mas_no_se_puede_cobrar_cargo` |
| RB-10 Empleado ausente | `Servicio.registrar_ausencia()` (reasignar o reprogramar, aviso tardío) | `test_us10_e1_se_reasigna_personal_y_el_servicio_sigue_igual`, `test_us10_e3_con_menos_de_1_hora_queda_incidencia_de_aviso_tardio`, `test_rb10_sin_reemplazo_hay_que_dar_nueva_fecha` |
| RB-11 Cliente no permite acceso | `registrar_acceso_denegado()` (15 min) + concepto `CANCELACION` 50 % | `test_us16_e1_tras_15_minutos_el_servicio_queda_no_realizado`, `test_us16_e2_con_14_minutos_todavia_no_se_puede_cancelar`, `test_us16_e1_y_h01_servicio_no_realizado_factura_solo_el_50_por_ciento` |
| RB-12 Servicio adicional en sitio | Incidencia `SERVICIO_ADICIONAL` → cargo con precio del catálogo | `test_us11_e1_servicio_adicional_se_cotiza_con_el_catalogo_y_queda_pendiente`, `test_rb12_servicio_adicional_sin_extra_del_catalogo_se_rechaza` |
| RB-13 Inmueble mayor a lo reportado | `excede_superficie()` (>15 %), `recalcular_precio()`, bloqueo de terminación | `test_us12_e1_mas_de_15_por_ciento_exige_recalcular_antes_de_terminar`, `test_us12_e2_exactamente_15_por_ciento_no_exige_recalcular`, `test_us12_e3_no_se_termina_con_recalculo_pendiente` |
| RB-14 Material especial / cargos antes de facturar | Incidencia `MATERIAL_ESPECIAL`; `TieneCargosPendientes` en `SERVICIO_FACTURABLE` | `test_rb14_material_especial_genera_cargo_con_el_monto_capturado`, `test_us20_e3_cargos_sin_autorizar_bloquean_la_factura`, `test_us20_e3_basta_un_centavo_sin_autorizar_para_bloquear` |
| RB-15 Roles de autorización | `exigir_rol()` en cada operación del dominio; encabezado `X-Rol` (ADR-009) | `test_us11_e2_solo_el_coordinador_autoriza_cargos`, `test_us06_e4_solo_el_coordinador_estima`, `test_us04_e3_con_menos_de_2_horas_el_cliente_no_puede_reprogramar_solo` |
| RES-01 Disponibilidad de cuadrillas | `CuadrillaDisponible`, `Programacion.se_traslapa_con()`, `ocupaciones_de_cuadrilla()` | `test_us09_e2_cuadrilla_ocupada_en_ese_horario_se_rechaza`, `test_us09_e1_cuadrilla_con_servicio_que_termina_justo_antes_si_esta_disponible`, `test_res01_ocupaciones_solo_cuentan_servicios_activos_de_esa_cuadrilla` |
| RES-02 Aceptación previa | Igual que RB-02 | `test_us08_e2_programar_cotizacion_no_aceptada_responde_422` |
| RES-03 Incidencias antes de terminar | Las incidencias solo se registran en `EN_EJECUCION` | `test_res03_despues_de_terminar_ya_no_se_registran_incidencias` |
| RES-04 Trazabilidad de la facturación | `ConceptoFacturado.referencia` (id del cargo o de la incidencia) | `test_us05_e1_el_monto_incluye_los_cargos_de_las_incidencias` |
| RES-05 Vigencia | Igual que RB-08 | `test_us22_e2_enviada_en_viernes_sigue_vigente_el_jueves_siguiente` |
| RES-06 Tiempo de espera | Igual que RB-11 | `test_us16_acceso_denegado` |
| SUP-02 Supervisor por servicio | `Servicio.programar()` exige supervisor | `test_sup02_el_servicio_necesita_supervisor` |
| SUP-03 Incidencia asociada | `Incidencia` dentro de `Servicio` (ADR-003) | `test_servicio_ida_y_vuelta_con_incidencias_y_cargos` |
| SUP-04 Una factura por servicio | `YaFacturado` + restricción única en `facturas.servicio_id` | `test_us20_e4_una_sola_factura_por_servicio`, `test_sup04_la_base_rechaza_dos_facturas_para_el_mismo_servicio` |
| SUP-06 Catálogo de extras | `resolver_extras()`, tabla `extras_catalogo` | `test_us01_e2_extra_fuera_del_catalogo_se_rechaza`, `test_us15_extra_en_sitio_fuera_del_catalogo` |
| H-06 Un servicio por cotización | `CotizacionSinServicio` + restricción única en `servicios.cotizacion_id` | `test_us08_e3_una_cotizacion_solo_genera_un_servicio`, `test_h06_la_base_rechaza_dos_servicios_para_la_misma_cotizacion` |
| H-12 Días hábiles | `sumar_dias_habiles()` | `test_h12_los_fines_de_semana_no_cuentan_como_dias_habiles` |
| H-14 Estado de pago | `Factura.registrar_pago()` | `test_us20_e5_registrar_pago`, `test_h14_solo_administracion_registra_pagos` |
| H-15 Cuadrilla ocupada | `Programacion` con duración | `test_h15_programaciones_que_se_cruzan_y_que_solo_se_tocan` |

## 3. User Stories → endpoint → caso de uso → pruebas

| Escenario | Endpoint | Caso de uso / dominio | Prueba |
|---|---|---|---|
| US-01 E1 | `POST /cotizaciones` | `ServicioDeCotizaciones.solicitar` → `Cotizacion.solicitar` | `test_us01_e1_la_solicitud_queda_registrada_para_estimar`, `test_us01_us06_us07_solicitar_estimar_y_enviar` |
| US-01 E2 | `POST /cotizaciones` | `resolver_extras` | `test_us01_e2_extra_fuera_del_catalogo_se_rechaza`, `test_us01_e2_extra_inexistente_responde_422_con_la_regla` |
| US-01 E3 | `POST /cotizaciones` | `ClienteActivo` | `test_us01_e3_cliente_inactivo_no_puede_solicitar`, `test_us01_e3_cliente_inactivo_responde_422` |
| US-02 E1 | `POST /cotizaciones/{id}/aceptacion`, `/rechazo` | `Cotizacion.aceptar` / `rechazar` | `test_us02_e1_el_cliente_acepta_dentro_de_la_vigencia`, `test_us02_e1_el_cliente_rechaza`, `test_us02_aceptar_y_rechazar` |
| US-02 E2 | `POST /cotizaciones/{id}/aceptacion` | `EstaPendiente` | `test_us02_e2_no_se_responde_una_cotizacion_que_no_esta_pendiente`, `test_us02_e2_no_se_acepta_antes_de_enviarse` |
| US-03 E1 | `POST /servicios` → `GET /notificaciones` | Evento `ServicioProgramado` | `test_us03_e1_al_programar_se_genera_el_evento_para_avisar_al_cliente`, `test_us03_e1_servicio_programado_avisa_al_cliente_con_fecha_y_cuadrilla`, `test_us08_us09_us03_programar_y_avisar_al_cliente` |
| US-04 E1 | `POST /servicios/{id}/reprogramacion` | `Servicio.reprogramar` | `test_us04_e1_con_2_horas_o_mas_el_cliente_reprograma_sin_costo`, `test_us04_reprogramar_sin_costo_y_de_ultima_hora` |
| US-04 E2 | `POST /servicios/{id}/reprogramacion` | `Servicio.reprogramar` (cargo) | `test_us04_e2_con_menos_de_2_horas_el_coordinador_aplica_cargo`, `test_us04_e2_el_coordinador_puede_no_cobrar_cargo` |
| US-04 E3 | `POST /servicios/{id}/reprogramacion` | `exigir_rol` (RB-09/RB-15) | `test_us04_e3_con_menos_de_2_horas_el_cliente_no_puede_reprogramar_solo` |
| US-04 E4 | `POST /servicios/{id}/reprogramacion` | `_mover_a` (RES-01) | `test_us04_e4_nueva_fecha_sin_cuadrilla_disponible_se_rechaza` |
| US-05 E1 | `POST /facturas`, `GET /facturas/{id}` | `GeneradorDeFactura` | `test_us05_e1_el_monto_incluye_los_cargos_de_las_incidencias`, `test_us20_us05_facturar_y_pagar` |
| US-06 E1 | `POST /cotizaciones/{id}/estimacion` | `Cotizacion.estimar` | `test_us06_e1_estimar_guarda_duracion_personal_y_precio` |
| US-06 E2 | `POST /cotizaciones/{id}/estimacion` | `CalculadoraDePrecio` | `test_us06_e2_residencial_100m2_unica_con_ventanas_cuesta_1450` |
| US-06 E3 | `POST /cotizaciones/{id}/estimacion` | `CalculadoraDePrecio` | `test_us06_e3_empresarial_200m2_semanal_con_alfombra_cuesta_3000`, `test_bpmn_servicio_completado_y_facturado` |
| US-06 E4 | `POST /cotizaciones/{id}/estimacion` | `exigir_rol` | `test_us06_e4_solo_el_coordinador_estima`, `test_us06_e4_estimar_con_otro_rol_responde_403` |
| US-07 E1 | `POST /cotizaciones/{id}/envio` | `Cotizacion.enviar` | `test_us07_e1_al_enviar_queda_pendiente_con_vigencia` |
| US-07 E2 | `POST /cotizaciones/{id}/envio` | `TienePrecio` | `test_us07_e2_no_se_envia_sin_estimar`, `test_us07_e2_enviar_sin_estimar_responde_422` |
| US-08 E1 | `POST /servicios` | `Servicio.programar` | `test_us08_e1_cotizacion_aceptada_queda_programada_con_fecha_y_cuadrilla` |
| US-08 E2 | `POST /servicios` | `CotizacionAceptada` | `test_us08_e2_cotizacion_no_aceptada_no_se_programa`, `test_us08_e2_programar_cotizacion_no_aceptada_responde_422` |
| US-08 E3 | `POST /servicios` | `CotizacionSinServicio` | `test_us08_e3_una_cotizacion_solo_genera_un_servicio`, `test_us08_e3_segunda_programacion_de_la_misma_cotizacion` |
| US-09 E1 | `POST /servicios` | `CuadrillaDisponible` | `test_us09_e1_cuadrilla_con_servicio_que_termina_justo_antes_si_esta_disponible` |
| US-09 E2 | `POST /servicios` | `CuadrillaDisponible` | `test_us09_e2_cuadrilla_ocupada_en_ese_horario_se_rechaza`, `test_us09_e2_cuadrilla_ocupada_y_rb04_cuadrilla_inactiva` |
| US-10 E1 | `POST /servicios/{id}/ausencia` | `Servicio.registrar_ausencia` | `test_us10_e1_se_reasigna_personal_y_el_servicio_sigue_igual` |
| US-10 E2 | `POST /servicios/{id}/ausencia` | `Servicio.registrar_ausencia` | `test_us10_e2_sin_reemplazo_se_reprograma_y_se_avisa_al_cliente`, `test_us10_e2_con_exactamente_1_hora_no_hay_aviso_tardio` |
| US-10 E3 | `POST /servicios/{id}/ausencia` | `TipoIncidencia.AVISO_TARDIO` | `test_us10_e3_con_menos_de_1_hora_queda_incidencia_de_aviso_tardio`, `test_us10_ausencia_sin_reemplazo_con_aviso_tardio` |
| US-11 E1 | `POST /servicios/{id}/incidencias`, `/cargos/{id}/autorizacion` | `registrar_incidencia`, `autorizar_cargo` | `test_us11_e1_servicio_adicional_se_cotiza_con_el_catalogo_y_queda_pendiente`, `test_us11_e1_el_coordinador_autoriza_el_cargo` |
| US-11 E2 | `POST /servicios/{id}/cargos/{id}/autorizacion` | `exigir_rol` | `test_us11_e2_solo_el_coordinador_autoriza_cargos`, `test_us13_us15_us11_us14_ejecucion_con_cargo_autorizado` |
| US-12 E1 | `POST /servicios/{id}/incidencias`, `/recalculo` | `excede_superficie`, `recalcular_precio` | `test_us12_e1_mas_de_15_por_ciento_exige_recalcular_antes_de_terminar`, `test_us12_e1_el_coordinador_recalcula_con_la_formula_de_rb03` |
| US-12 E2 | `POST /servicios/{id}/incidencias` | `excede_superficie` | `test_us12_e2_exactamente_15_por_ciento_no_exige_recalcular` |
| US-12 E3 | `POST /servicios/{id}/terminacion` | `registrar_terminacion` | `test_us12_e3_no_se_termina_con_recalculo_pendiente`, `test_us12_inmueble_mayor_bloquea_terminacion_hasta_recalcular` |
| US-13 E1 | `POST /servicios/{id}/inicio` | `registrar_inicio` | `test_us13_e1_registrar_inicio_cambia_a_en_ejecucion` |
| US-13 E2 | `POST /servicios/{id}/inicio` | `_exigir_estado` | `test_us13_e2_no_se_inicia_un_servicio_que_no_esta_programado` |
| US-14 E1 | `POST /servicios/{id}/terminacion` | `registrar_terminacion` | `test_us14_e1_y_us18_e1_terminar_habilita_la_facturacion` |
| US-14 E2 | `POST /servicios/{id}/terminacion` | `_exigir_estado` | `test_us14_e2_no_se_termina_un_servicio_que_no_ha_iniciado`, `test_transicion_invalida_responde_409` |
| US-15 E1 | `POST /servicios/{id}/incidencias` | `registrar_incidencia` | `test_us15_e1_la_incidencia_queda_asociada_y_genera_evento_para_administracion` |
| US-16 E1 | `POST /servicios/{id}/acceso-denegado` | `registrar_acceso_denegado` | `test_us16_e1_tras_15_minutos_el_servicio_queda_no_realizado`, `test_us16_factura_del_servicio_no_realizado_es_el_50_por_ciento` |
| US-16 E2 | `POST /servicios/{id}/acceso-denegado` | `registrar_acceso_denegado` | `test_us16_e2_con_14_minutos_todavia_no_se_puede_cancelar`, `test_us16_acceso_denegado` |
| US-17 E1 | `GET /cuadrillas/{id}/servicios` | `LectorSql.servicios_de_cuadrilla` | `test_us17_us19_us21_reportes` |
| US-18 E1 | `POST /servicios/{id}/terminacion` | `registrar_terminacion` | `test_us14_e1_y_us18_e1_terminar_habilita_la_facturacion` |
| US-19 E1 | `GET /notificaciones?destinatario=ADMINISTRACION` | `notificaciones_para` | `test_us19_e1_incidencia_avisa_a_administracion`, `test_us17_us19_us21_reportes` |
| US-20 E1 | `POST /facturas` | `GeneradorDeFactura.generar` | `test_us20_e1_factura_de_servicio_terminado_queda_vinculada_y_pendiente_de_pago` |
| US-20 E2 | `POST /facturas` | `SERVICIO_FACTURABLE` | `test_us20_e2_servicio_no_terminado_no_se_factura` |
| US-20 E3 | `POST /facturas` | `TieneCargosPendientes` | `test_us20_e3_cargos_sin_autorizar_bloquean_la_factura`, `test_us20_e3_factura_con_cargo_pendiente` |
| US-20 E4 | `POST /facturas` | `YaFacturado` | `test_us20_e4_una_sola_factura_por_servicio` |
| US-20 E5 | `POST /facturas/{id}/pago` | `Factura.registrar_pago` | `test_us20_e5_registrar_pago` |
| US-21 E1 | `GET /reportes/resumen`, `/reportes/*` | `ServicioDeConsultas.resumen` | `test_us17_us19_us21_reportes` |
| US-22 E1 | `GET /cotizaciones/{id}`, `POST /cotizaciones/{id}/renovacion` | `actualizar_vencimiento`, `renovar` | `test_us22_e1_pendiente_despues_de_5_dias_habiles_queda_vencida`, `test_us22_e1_consultar_marca_vencida_y_renovar_crea_una_nueva` |
| US-22 E2 | `POST /cotizaciones/{id}/aceptacion` | `Vigencia` | `test_us22_e2_enviada_en_viernes_sigue_vigente_el_jueves_siguiente` |

## 4. Casos de uso → BPMN → código

| Caso de uso | Tareas del BPMN | Clase de aplicación | Aggregate |
|---|---|---|---|
| CU-01 Generar y enviar cotización | Solicitar cotización, Estimar servicio, Enviar cotización | `ServicioDeCotizaciones` | `Cotizacion` |
| CU-02 Responder cotización | ¿Cliente acepta la cotización? | `ServicioDeCotizaciones` | `Cotizacion` |
| CU-03 Programar servicio y asignar cuadrilla | Programar servicio, Asignar cuadrilla, Reprogramar, Reasignar personal | `ProgramacionDeServicios` | `Servicio` |
| CU-04 Registrar incidencias en la ejecución | ¿Cliente permite el acceso?, Registrar inicio, ¿Hubo incidencia?, Registrar terminación | `EjecucionDeServicios` | `Servicio` |
| CU-05 Facturar servicio | Registrar cargo de cancelación, Registrar servicio / facturación | `FacturacionDeServicios` | `Factura` |
