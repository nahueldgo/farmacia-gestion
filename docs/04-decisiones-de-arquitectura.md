# Decisiones de Arquitectura y Respuesta a la Primera Revisión

Equipo: Esper, Amira Yasmin Elizabeth · Dugo, Nahuel | Tutor: Fonzo, Santiago

Este documento registra las decisiones técnicas y arquitectónicas tomadas a lo largo del desarrollo de la aplicación, junto con la justificación de cada una y las alternativas que se descartaron, y deja constancia de cómo se resolvió cada punto de la primera revisión del tutor. El contexto del problema, el alcance y el plan de trabajo están en el [README](../README.md); el análisis de viabilidad y los riesgos, en [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md); las decisiones de modelado de la base de datos, en [Diseño de la Base de Datos](./05-diseno-de-base-de-datos.md). Acá no se repite ese contenido.

Nota: no incluye instructivos de configuración de entorno, el foco es exclusivamente el diseño del sistema: qué se decidió, qué alternativas se evaluaron y por qué.

## Correcciones solicitadas en la primera entrega

Tras la primera entrega, el tutor señaló nueve puntos a revisar. Cada uno se resolvió en el README o en la documentación de gestión de `/docs` y, cuando implicó una decisión con alternativas, se desarrolla más abajo en este documento:

| # | Punto señalado | Dónde se resuelve |
|---|---|---|
| 1 | Qué pasa con el sistema si la farmacia pierde conectividad, dado que backend y base de datos están en la nube | [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md) (Riesgos); decisión y alternativas en la sección "Conectividad y arquitectura cloud" |
| 2 | Para qué se usa Docker Compose, si frontend y backend corren en entornos distintos | README (Tecnologías) |
| 3 | Detallar las etapas del cronograma diferenciando qué se desarrolla en cada una (backend, frontend, conexión) y con qué duración | README (Plan de trabajo): fecha de inicio y de fin por etapa, con la separación Backend / Frontend / Conexión. Las duraciones son estimaciones aproximadas que se ajustarán a medida que avance el desarrollo |
| 4 | Cuantificar los impactos del problema (pérdida de ventas, errores de caja), hoy solo enunciados | README (Impacto estimado y validación); la encuesta se describe más abajo |
| 5 | Los objetivos específicos duplicaban casi textualmente el alcance | README (Objetivos y Alcance): se reescribieron como conceptos distintos |
| 6 | Explicitar el análisis de viabilidad en sus tres ejes | [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md) (Análisis de viabilidad): eje temporal, técnico y de dominio/conocimiento |
| 7 | Separar la comparación con la competencia, sumando a la planilla manual como competidor directo | README (Análisis de competencia) |
| 8 | Agregar un análisis de riesgos y mitigaciones concreto | [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md) (Riesgos identificados), con la precisión del riesgo del motor de reglas y la mitigación ante atrasos |
| 9 | Agregar horas estimadas por tarea y fecha de inicio al cronograma | README (Plan de trabajo): se agregó la fecha de inicio; la estimación de horas por tarea se irá ajustando a medida que avance el desarrollo |

## Cuantificación de impactos y encuesta (punto 4)

Las cifras de impacto, la encuesta y el compromiso de reportar sus resultados tal como salgan están en el [README](../README.md#impacto-estimado-y-validación). Acá se deja el detalle de lo que la encuesta cubre. Sus 18 preguntas se agrupan en: caracterización de la farmacia (localidad, tamaño, personal, conectividad), sistema de gestión y validadores de cobertura que usan hoy (si usan alguno), qué pasos del cálculo de copago hacen a mano y cuánto tiempo les lleva, volumen de ventas con cobertura y ticket promedio, ventas resignadas por la complejidad del trámite, diferencias de caja por errores de cálculo, y una pregunta de cierre sobre qué funcionalidad valorarían en un sistema de gestión que no tengan hoy.

## Conectividad y arquitectura cloud (punto 1)

Se evaluaron distintas alternativas de arquitectura durante el diseño: en un momento se consideró una aplicación de escritorio completamente autónoma (backend y base de datos también locales), dado que el modelo de negocio apunta a localidades pequeñas donde puede haber problemas de conectividad. Se descartó esa opción por dos motivos: la consigna académica exige al menos un componente en la nube, y resolver el manejo real de desconexiones era un proyecto demasiado grande para un equipo de dos personas en los tiempos disponibles.

La resolución adoptada fue documentar la dependencia de conectividad como un **riesgo mitigado y aceptado**, no ignorado. La mitigación concreta (reintentos automáticos y conexión de respaldo) está en [Análisis de Riesgos, Supuestos y Restricciones](./01-analisis-riesgos-supuestos-restricciones.md).

**Implementación completamente local en producción.** Para este TFI, el backend y la base de datos se mantienen en la nube porque es un requisito obligatorio de la consigna académica. En una implementación real, la forma correcta de eliminar por completo el riesgo de conectividad sería que la aplicación fuera 100% local: una base de datos embebida en la propia máquina de la farmacia (por ejemplo SQLite, o una instancia local de PostgreSQL), con el backend corriendo también localmente o integrado directamente en la app de escritorio. La sincronización con la nube pasaría a ser un proceso secundario y periódico (backups, reportes centralizados entre sucursales), no una dependencia para operar. Esta migración es viable sin rediseñar el resto del sistema, porque la lógica de negocio ya está separada de la capa de persistencia.

## Por qué aplicación de escritorio y por qué Electron

A pedido del tutor, se deja por escrito la justificación de dos decisiones tecnológicas que ya estaban tomadas pero no fundamentadas.

**Por qué aplicación de escritorio.** La idea inicial del proyecto era una aplicación casi completamente local, con la nube pensada solo como respaldo y no como parte central de la operación. Esa decisión fue previa a la de infraestructura: lo que se evaluó después fue dónde alojar el backend y la base de datos (ver "Conectividad y arquitectura cloud"). Que el cliente fuera de escritorio y no una versión web surge de dos cosas: por un lado, los sistemas comerciales del rubro relevados como referencia (GEMA, NOVA EVO) son aplicaciones de escritorio; por otro, el sistema está pensado para uso interno de la farmacia y no para exponerse a clientes externos, y para ese uso resulta más simple de manejar desde un puesto fijo de trabajo como el mostrador, con una ventana propia y estable, en vez de depender de un navegador. Al no estar expuesta a clientes externos, tampoco necesita las ventajas de distribución de una versión web.

**Por qué Electron.** Dentro de la decisión ya tomada de que el cliente fuera de escritorio, Electron se eligió puntualmente porque reutiliza el mismo frontend React ya definido para el proyecto. Se descartaron dos alternativas: un framework de interfaz nativo distinto (como C#/.NET), que obligaría a rehacer el frontend, y un lenguaje nuevo (como Rust, que requeriría una alternativa como Tauri), que sumaría una curva de aprendizaje adicional a un cronograma que ya no tiene margen.

## Diseño extensible: patrón Strategy y extensiones futuras

El cálculo de cobertura se construye detrás de una interfaz (patrón *Strategy*), de modo que el motor de reglas manual pueda convivir a futuro con validadores externos reales (ValidaCOFA, u otros propios de obras sociales grandes como Swiss Medical o Sancor Salud) sin rediseñar el resto del sistema. Esa integración requeriría que la farmacia esté homologada por cada entidad, y queda fuera del alcance de este TFI (ver [Gestión del Alcance](./03-gestion-alcance.md)). A nivel de base de datos, el gancho de esta extensibilidad es la columna `tipo_validacion` de `ObraSocial` (ver [Diseño de la Base de Datos](./05-diseno-de-base-de-datos.md)).

La misma separación entre lógica de negocio y persistencia deja abiertas otras dos extensiones, ninguna de las cuales forma parte del alcance de este TFI:

- **Asistente basado en IA.** A partir del historial de ventas y el stock con trazabilidad de vencimientos, informaría o sugeriría compras a droguerías, y alertaría cuando los medicamentos ingresados en un período determinado estén próximos a vencer (para gestionar a tiempo su devolución al proveedor o su descarte correcto según los protocolos de residuos farmacéuticos). No automatizaría la compra ni reemplazaría la decisión del farmacéutico/a.
- **Frontend web para clientes.** Permitiría hacer compras online reutilizando el mismo backend.
