# Gestión del Alcance

**Proyecto:** Sistema de Gestión de Ventas y Cobertura para Farmacia de Pueblo
**Equipo:** Esper, Amira · Dugo, Nahuel

> Nota: el detalle de "Incluye" / "No incluye" ya está documentado en el [README](../README.md#alcance). Este documento profundiza en el marco de referencia de las reglas de cobertura, en los **criterios de aceptación** de los módulos principales (usando el formato Given/When/Then) y en la justificación de lo que queda fuera.

## Marco de referencia: pisos del PMO

El PMO (Programa Médico Obligatorio) argentino fija pisos mínimos legales de cobertura que toda entidad debe cumplir, y que puede igualar o mejorar:

- **40%** para medicamentos ambulatorios en general.
- **70%** para enfermedades crónicas prevalentes (por ejemplo, hipertensión).
- **100%** para categorías específicas como oncológicos, diabetes (medicamentos e insulina, Ley 23.753), anticonceptivos (Ley 25.673), HIV y discapacidad (Ley 24.901).

El sistema permite configurar estos porcentajes por categoría de medicamento y por entidad, ya que en la práctica varían según lo que cada obra social o mutual local decida ofrecer por encima del piso legal. Cómo se modela esto en la base de datos está en [Diseño de la Base de Datos](./05-diseno-de-base-de-datos.md) (`CategoriaCoberturaObraSocial` y `ReglaCobertura`).

## Criterios de aceptación por módulo

### Registro de venta de mostrador

**Dado que** el auxiliar de farmacia (cajero/personal de mostrador) selecciona uno o más medicamentos de venta libre
**Cuando** confirma la venta con un medio de pago válido (efectivo, tarjeta de crédito, tarjeta de débito, transferencia o QR)
**Entonces** el sistema registra la venta, descuenta el stock correspondiente y la incluye en el cierre de caja del día

### Integridad transaccional del registro de una venta

**Dado que** un empleado confirma una venta con una o más líneas de producto
**Cuando** el sistema registra la operación
**Entonces** la venta, sus líneas de detalle y el descuento de stock correspondiente se guardan como una única operación atómica; si cualquier paso falla, no queda ningún registro parcial

### Cálculo automático de copago

**Dado que** existe una regla de cobertura configurada para la obra social/entidad del cliente
**Cuando** se registra una venta asociada a esa entidad
**Entonces** el sistema calcula automáticamente el copago según el porcentaje configurado (ej. PMO 100%, crónicos 70%, ambulatorios 40%) y lo refleja en el total a cobrar, con respuesta inmediata

### Configuración de reglas de cobertura

**Dado que** el Dt. farmacéutico/a necesita dar de alta una nueva obra social local/gremial
**Cuando** carga el nombre de la entidad y, para cada categoría de medicamento que la entidad decide cubrir (ambulatorio, crónico, oncológico, etc.), el porcentaje de cobertura correspondiente
**Entonces** esas reglas quedan disponibles para ser aplicadas en futuras ventas sin necesidad de cálculo manual

### Trazabilidad de lotes y vencimientos

**Dado que** un producto tiene múltiples lotes con distintas fechas de vencimiento
**Cuando** se registra una venta de ese producto
**Entonces** el sistema descuenta stock priorizando el lote más próximo a vencer, y genera una alerta si queda stock próximo a caducar

### Descuento de stock al vender

**Dado que** un producto tiene lotes con distintas fechas de vencimiento y cantidades
**Cuando** se confirma una venta de una cantidad determinada de ese producto
**Entonces** el sistema descuenta primero del lote que vence antes, y si ese lote no alcanza, completa con el siguiente, los lotes vencidos y los agotados no se tienen en cuenta, y un lote que vence hoy se puede vender durante todo el día

**Dado que** la suma de los lotes vendibles de un producto es menor a la cantidad pedida
**Cuando** se intenta confirmar la venta
**Entonces** el sistema rechaza la operación, informa que no hay stock suficiente y no descuenta nada de ningún lote

**Dado que** dos ventas simultáneas piden el mismo producto
**Cuando** ambas se confirman al mismo tiempo
**Entonces** el sistema procesa el descuento de forma que ninguna unidad se venda dos veces

### Quién registra las ventas y quién solo las consulta

**Dado que** el auxiliar de farmacia, el Dt. farmacéutico/a y el dueño/gerente tienen cada uno su usuario
**Cuando** intentan registrar o anular una venta
**Entonces** el sistema se lo permite al auxiliar y al farmacéutico y se lo rechaza al dueño, que solo puede consultar el listado y el detalle de las ventas

### Reintento de una venta sin duplicarla

**Dado que** la pantalla vuelve a enviar un pedido de venta porque se cortó la conexión antes de recibir la respuesta
**Cuando** el pedido llega con la misma clave de operación que una venta ya registrada
**Entonces** el sistema devuelve esa venta y no crea otra ni descuenta el stock por segunda vez, incluso si los dos pedidos llegan al mismo tiempo

### Venta con la caja abierta

**Dado que** no hay una caja abierta
**Cuando** se intenta registrar una venta
**Entonces** el sistema la rechaza sin descontar stock y pide abrir la caja primero; solo puede haber una caja abierta a la vez

### Consulta del historial de ventas

**Dado que** existen ventas registradas en distintos días
**Cuando** cualquiera de los tres roles pide el listado sin fechas, con un día o con un rango de fechas, y opcionalmente solo las confirmadas o solo las anuladas
**Entonces** el sistema muestra las ventas de ese período, de la más reciente a la más antigua y con el día cortado en hora de Argentina, y permite abrir el detalle de cada una con sus líneas, lotes y precios

### Anulación de una venta

**Dado que** una venta confirmada se cargó por error o el cliente se arrepiente, el mismo día o en otra fecha
**Cuando** el auxiliar de farmacia o el Dt. farmacéutico/a la anula
**Entonces** la venta pasa a anulada y queda registrado quién la anuló y cuándo, sin borrarla del historial; el stock no se reintegra automáticamente, la venta no puede anularse de nuevo y deja de contarse en el cierre de caja

### Cierre de caja diario

**Dado que** finalizó la jornada de ventas
**Cuando** el empleado que cierra la caja declara el monto contado físicamente
**Entonces** el sistema calcula el monto esperado (ventas de la jornada y movimientos manuales de ingreso o retiro), muestra la diferencia entre el monto declarado y el calculado, y presenta el consolidado de ventas por tipo (mostrador / con cobertura) y por medio de pago (efectivo, tarjeta de crédito, tarjeta de débito, transferencia y QR), sin necesidad de cruzar planillas manualmente

### Reportes históricos

**Dado que** existen ventas registradas en distintos períodos
**Cuando** el dueño/a o gerente filtra por día, mes o período
**Entonces** el sistema muestra la cantidad de tickets por producto y los porcentajes de facturación correspondientes

### Inicio de sesión y acceso al sistema

**Dado que** un empleado tiene un usuario activo con su contraseña
**Cuando** inicia sesión con su nombre de usuario y su contraseña
**Entonces** el sistema le da acceso con un token de 60 minutos y las funciones de su rol, si el usuario no existe o la contraseña es incorrecta, responde con el mismo mensaje de error para no revelar qué usuarios existen, y si el empleado fue dado de baja, no lo deja ingresar

**Dado que** el empleado ingresa con una contraseña que eligió otra persona (alta nueva o reseteo hecho por el dueño)
**Cuando** inicia sesión
**Entonces** el sistema le exige cambiarla antes de usar cualquier otra función, y la nueva contraseña debe tener al menos 8 caracteres y ser distinta de la anterior

### Usuarios, roles y responsabilidad individual

**Dado que** cada empleado tiene un usuario propio con un rol asignado (auxiliar de farmacia/cajero/personal de mostrador, Dt. farmacéutico/a o dueño/gerente)
**Cuando** registra una venta
**Entonces** la venta queda vinculada a ese empleado, y el sistema limita las funciones disponibles según su rol

## Justificación de lo que queda fuera de esta versión

- **Integración con validadores formales de obras sociales (IMED, COFA, y los propios de obras sociales grandes).** Requeriría que la farmacia esté homologada por cada entidad, y las entidades locales o gremiales que motivan este proyecto no están integradas a esos validadores. Además, no existe una API pública y gratuita para validar coberturas de obras sociales locales/gremiales: se investigó activamente y se descartó esa posibilidad (ver supuestos en [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md)). El diseño queda preparado para incorporar validadores a futuro (ver [Decisiones de Arquitectura](./04-decisiones-de-arquitectura.md#diseño-extensible-patrón-strategy-y-extensiones-futuras)).
- **Tienda online y aplicación móvil.** El sistema es el software de gestión interna de la farmacia, no una herramienta de venta a clientes finales. La tienda online queda como extensión futura posible sobre el mismo backend (ver Decisiones de Arquitectura).
- **Modo offline.** Se documenta como riesgo aceptado y como extensión futura (ver Análisis de Riesgos, Supuestos y Restricciones, y Decisiones de Arquitectura).
- **Facturación electrónica / integración con AFIP.** Ver la restricción legal/normativa en Análisis de Riesgos, Supuestos y Restricciones.
- **Integración con hardware específico y gestión de compras a proveedores.** Quedan fuera como parte de la reducción activa del alcance para llegar a los plazos de la cátedra (ver Análisis de Riesgos, Supuestos y Restricciones).
- **Trazabilidad detallada de ajustes manuales de stock.** Se permite corregir directamente la cantidad de un lote desde la pantalla de stock (por ejemplo, ante rotura o error de carga), pero sin un registro histórico dedicado de quién hizo el ajuste, cuándo y por qué motivo. Queda como extensión futura posible.
- **Reversión automática de stock al anular una venta.** Una venta puede pasar a estado "anulada", pero el reintegro del stock descontado al lote o los lotes de origen no se automatiza en esta versión. Queda como extensión futura posible.

## Criterio de éxito del proyecto

El proyecto se considera exitoso si, al finalizar el desarrollo, el sistema permite completar el circuito completo descripto en el problema (desde la venta de mostrador o con cobertura, hasta el cierre de caja) sin recurrir a cálculo manual de copagos ni a planillas, respetando el alcance definido y las restricciones de tiempo establecidas por la cátedra (ver [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md)).
