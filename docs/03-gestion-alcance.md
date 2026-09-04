# Gestión del Alcance

**Proyecto:** Sistema de Gestión de Ventas y Cobertura para Farmacia de Pueblo
**Equipo:** Esper, Amira · Dugo, Nahuel

> Nota: el detalle de "Incluye" / "No incluye" ya está documentado en el [README](../README.md#alcance). Este documento profundiza en los **criterios de aceptación** de los módulos principales, usando el formato Given/When/Then.

## Criterios de aceptación por módulo

### Registro de venta de mostrador

**Dado que** el auxiliar de farmacia (cajero/personal de mostrador) selecciona uno o más medicamentos de venta libre
**Cuando** confirma la venta con un medio de pago válido (efectivo, tarjeta de crédito, tarjeta de débito, transferencia o QR)
**Entonces** el sistema registra la venta, descuenta el stock correspondiente y la incluye en el cierre de caja del día

### Cálculo automático de copago

**Dado que** existe una regla de cobertura configurada para la obra social/entidad del cliente
**Cuando** se registra una venta asociada a esa entidad
**Entonces** el sistema calcula automáticamente el copago según el porcentaje configurado (ej. PMO 100%, crónicos 70%, ambulatorios 40%) y lo refleja en el total a cobrar

### Configuración de reglas de cobertura

**Dado que** el Dt. farmacéutico/a necesita dar de alta una nueva obra social local/gremial
**Cuando** carga el nombre de la entidad y el porcentaje de cobertura correspondiente
**Entonces** esa regla queda disponible para ser aplicada en futuras ventas sin necesidad de cálculo manual

### Trazabilidad de lotes y vencimientos

**Dado que** un producto tiene múltiples lotes con distintas fechas de vencimiento
**Cuando** se registra una venta de ese producto
**Entonces** el sistema descuenta stock priorizando el lote más próximo a vencer, y genera una alerta si queda stock próximo a caducar

### Cierre de caja diario

**Dado que** finalizó la jornada de ventas
**Cuando** el dueño/a o gerente solicita el cierre de caja
**Entonces** el sistema muestra el consolidado de ventas por tipo (mostrador / con cobertura) y por medio de pago (efectivo, tarjeta de crédito, tarjeta de débito, transferencia y QR), sin necesidad de cruzar planillas manualmente

## Criterio de éxito del proyecto

El proyecto se considera exitoso si, al finalizar el desarrollo, el sistema permite completar el circuito completo descripto en el problema (desde la venta de mostrador o con cobertura, hasta el cierre de caja) sin recurrir a cálculo manual de copagos ni a planillas, respetando el alcance definido y las restricciones de tiempo establecidas por la cátedra (ver [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md)).
