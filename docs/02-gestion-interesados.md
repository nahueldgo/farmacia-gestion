# Gestión de Interesados (Stakeholders)

**Proyecto:** Sistema de Gestión de Ventas y Cobertura para Farmacia de Pueblo
**Equipo:** Esper, Amira · Dugo, Nahuel

## Clasificación de interesados

### Stakeholders internos

| Stakeholder | Rol | Interés |
|---|---|---|
| Amira Esper | Equipo de desarrollo | Cumplir con los módulos asignados en tiempo y forma |
| Nahuel Dugo | Equipo de desarrollo | Cumplir con los módulos asignados en tiempo y forma |
| Santiago Fonzo | Tutor | Evaluar la viabilidad y el avance del proyecto en cada entrega |

### Stakeholders externos: usuarios finales

| Stakeholder | Rol | Interés |
|---|---|---|
| Auxiliar de Farmacia / Cajero / Personal de mostrador | Usa el sistema para vender de forma ágil medicamentos de venta libre, perfumería, elementos de cuidado personal y medicamentos sin cobertura, registrar ventas con cobertura de obra social y controlar el stock | Facilidad de uso, rapidez en la carga de ventas |
| Dt. Farmacéutico/a (titular) | Supervisa y es responsable legal de las dispensaciones, configura las reglas de cobertura por obra social, controla stock y vencimientos, y realiza los pedidos a proveedores en base al stock | Que el cálculo de copago sea correcto y confiable |
| Dueño/a o gerente | Supervisa el negocio | Visibilidad de caja diaria consolidada, historial de ventas y métricas |
| Cliente con obra social local/gremial | Beneficiario indirecto | Ser atendido sin que la farmacia evite la venta por complejidad administrativa |

### Stakeholders externos: validación y evaluación

| Stakeholder | Rol | Interés |
|---|---|---|
| Farmacéutica/bioquímica consultada | Validadora informal del problema y las reglas de negocio: confirmó la problemática que motiva el proyecto | Que el sistema resuelva realmente la fricción de las ventas con obra social local/gremial |
| Farmacéutico que trabaja con un sistema comercial de gestión | Consultado informalmente. Detalló las funcionalidades clave que utiliza a diario: actualización de precios, actualización de descuentos por obra social, validación de cobertura con respuesta inmediata por producto, control de stock, estadísticas filtrables por producto/período y usuario individual por empleado. Confirmó como crítica la respuesta inmediata de la validación de cobertura | Que el sistema cubra las funcionalidades que un sistema de gestión debe ofrecer en el uso diario |
| Farmacias y su personal (farmacéuticos, auxiliares) | Destinatarios de la encuesta sobre gestión y cobertura (ver [README](../README.md#impacto-estimado-y-validación)) | Aportar datos medidos para validar (o ajustar) las estimaciones de impacto del proyecto |
| Comité de Trabajo Final Integrador (UTN) | Evaluador académico | Que el proyecto cumpla los objetivos pedagógicos de la carrera |

## Estrategias de gestión

- **Comunicación con el tutor:** seguimiento mediante mensajería del campus virtual y reuniones sincrónicas cuando se convoquen, según la modalidad de la cátedra.
- **Comunicación con los profesionales consultados:** se prevén consultas adicionales durante el desarrollo para ajustar reglas de cobertura y validar decisiones de alcance a medida que se avanza (ver [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md)).
- **Gestión de expectativas:** el alcance del proyecto queda documentado explícitamente en el [README](../README.md#alcance) (secciones "Incluye" / "No incluye") y en [Gestión del Alcance](./03-gestion-alcance.md), para evitar interpretaciones ambiguas entre el equipo y el tutor sobre qué se va a entregar.
- **Seguimiento interno del equipo:** tablero de tareas en Trello, para coordinar el trabajo entre ambos integrantes.

## Relación con el alcance del proyecto

Los intereses de los stakeholders externos (especialmente el auxiliar de farmacia y el farmacéutico/a) fueron el criterio principal para decidir qué queda dentro del alcance de esta primera versión: se priorizó lo que resuelve la fricción real que describió la farmacéutica consultada (ventas de mostrador ágiles, cálculo automático de copago, cierre de caja, trazabilidad de stock) por sobre funcionalidades que suenan atractivas pero no fueron validadas como prioritarias (tienda online, hardware específico, validadores externos formales). La consulta al farmacéutico con sistema comercial permitió, además, ajustar el alcance a necesidades reales del rubro.
