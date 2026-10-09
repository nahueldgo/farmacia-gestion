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

## Convenciones de la API

**Nombres de los campos.** Todo usa `snake_case`, igual que las columnas de la base. La única excepción es el login (`nombreUsuario` y `debeCambiarContrasena`), que se definió primero junto con el frontend. Cambiarlo cuando ya funcionaba rompería lo que está andando, así que la unificación queda planificada antes del despliegue y en tres pasos: el backend acepta las dos versiones, el frontend pasa a los nombres con guion bajo y después se eliminan los viejos.

## Autenticación y control de acceso (Módulo 1)

Decisiones tomadas al construir el login, la gestión de empleados y los permisos por rol, con la alternativa que se descartó en cada caso.

**Token JWT en lugar de sesiones en el servidor.** El cliente es una aplicación de escritorio que consume una API separada alojada en la nube, por lo que un token firmado que el cliente presenta en cada pedido resulta más simple que mantener sesiones guardadas en el servidor. El costo aceptado es que un token ya emitido no se puede revocar antes de que venza; se compensa con una duración corta (60 minutos) y con el mecanismo de renovación descripto abajo.

**Renovación simple del token.** El endpoint de renovación recibe un token vigente y devuelve uno nuevo, consultando en la base de datos el rol y el estado del usuario en ese momento, de modo que un cambio de rol o una baja se aplican en la siguiente renovación. Se descartó un refresh token separado y de larga duración porque suma piezas (almacenamiento, rotación, revocación) que exceden el alcance del TFI.

**Baja lógica de empleados y usuarios.** Se marcan como inactivos (`activo`) en lugar de borrarlos, porque las ventas y los movimientos de caja los referencian y deben conservar la trazabilidad de quién los realizó. El login y la renovación del token rechazan a los inactivos. La baja desactiva a la vez al empleado y a su usuario: alcanzaría con uno solo para bloquear el login, pero conceptualmente ninguno de los dos sigue vigente cuando la persona deja de trabajar.

**Alta de empleado y usuario en una sola transacción.** El endpoint que crea un empleado también crea su usuario, y las dos inserciones se confirman juntas (`flush` para obtener el ID del empleado sin cerrar la transacción, y un único `commit`). Si algo falla en el medio, no queda ni el empleado ni el usuario a medio crear.

**Permisos por rol aplicados en el backend.** La restricción por rol se verifica en la API. El menú del frontend que oculta opciones según el rol es solo una ayuda visual: un usuario podría escribir una dirección a mano, por lo que la protección real tiene que estar donde están los datos.

**Mismo mensaje de error ante usuario inexistente y contraseña incorrecta.** Se evita así revelar qué nombres de usuario existen en el sistema.

**CORS abierto durante el desarrollo.** La API acepta pedidos de cualquier origen para facilitar las pruebas locales. Es un riesgo aceptado y temporal: debe restringirse a los orígenes reales antes del despliegue.

**Edición de empleados con límites.** El dueño puede corregir nombre, apellido, rol, email, matrícula y fecha de ingreso, enviando solo lo que cambia. No se pueden editar el DNI ni el nombre de usuario: identifican a la persona y a su acceso, y las ventas y los movimientos de caja los referencian, así que cambiarlos rompería la trazabilidad de quién hizo cada operación. El email vive en el usuario y no puede repetirse con el de otro.

**Matrícula obligatoria para el farmacéutico.** Un empleado con rol farmacéutico necesita matrícula profesional, porque en una farmacia es el profesional responsable: dirige el establecimiento como director técnico, está presente en el despacho de los medicamentos que requieren receta, y firma y archiva la documentación de los productos de venta controlada (recetas de estupefacientes y psicotrópicos, libro recetario y pedidos). Para el auxiliar y el dueño la matrícula es opcional: no ejercen como profesional responsable de la farmacia, así que no tienen una matrícula que cargar. El sistema no cubre el recetario ni los libros de control, que quedan fuera del alcance de este TFI. La regla se controla sobre el resultado final y no solo sobre lo que se envía: cambiar un rol a farmacéutico sin matrícula se rechaza, y también quitarle la matrícula a quien ya lo es.

**Varios dueños, con protección.** Puede haber más de un dueño, y un dueño puede crear a otro. Nadie puede darse de baja ni cambiarse el rol a sí mismo, y nunca puede quedar el sistema sin un dueño activo. Se descartó permitir la baja propia: un solo clic dejaría al sistema sin quien administre a los empleados, y desde el propio sistema no habría forma de recuperarlo. La última regla cubre además el caso de un token todavía vigente de un dueño ya dado de baja.

**Reglas de contraseña.** Mínimo de 8 caracteres en el alta, en el reseteo y en el cambio propio. El cambio propio pide la contraseña actual, para que no pueda cambiarla alguien que encuentre la sesión abierta, y exige que la nueva sea distinta, para que el cambio forzado no se pueda cumplir repitiendo la misma. No hay recuperación de contraseña por mail: requeriría un servicio de envío de correo y códigos con vencimiento, y queda como mejora futura; si alguien la olvida, el dueño se la resetea.

**Cambio forzado en el primer ingreso.** Los empleados que da de alta el dueño, y los que este resetea, usan una contraseña que eligió otra persona, así que deben cambiarla al entrar. Una columna en el usuario (`debe_cambiar_contrasena`) lo marca; el token lleva esa marca, y mientras esté activa el backend responde 403 en todo salvo en la consulta de la sesión y en el cambio de contraseña, que devuelve un token nuevo ya habilitado. Se descartó confiar solo en la pantalla del frontend: el bloqueo real tiene que estar donde están los datos. El costo es una columna nueva en la base, que obliga a recrearla o a agregarla a mano. Los usuarios de prueba no tienen la marca.

**Primer dueño real con un script.** Para no depender de los usuarios de prueba en producción, `crear_dueno.py` pide los datos por consola y crea al primer dueño. La contraseña se escribe sin que se vea y no queda en ningún archivo ni en el repositorio, y el propio dueño la elige en ese momento, por eso no se le fuerza el cambio. Se descartó dejar un dueño con contraseña fija en el `seed.py`, que quedaría conocida por cualquiera que lea el repositorio.

**Permisos del módulo.** La gestión de empleados (alta, edición, baja, reactivación y reseteo de la contraseña de otros) es solo del dueño, porque es quien administra al personal. El cambio de la contraseña propia lo usan los tres roles.

## Productos, lotes y stock (Módulo 2)

Decisiones tomadas al construir el catálogo, los lotes y el stock, con la alternativa que se descartó en cada caso.

**El stock se calcula a partir de los lotes.** El stock de un producto es la suma de las cantidades de sus lotes que todavía no vencieron; no se guarda como un número aparte, así que no puede quedar desfasado respecto de los lotes. Se descartó una columna `stock` en el producto, que habría que mantener sincronizada con cada alta, ajuste y venta. Un lote vencido no cuenta como stock vendible, y uno que vence hoy sí cuenta durante todo el día.

**Un lote por producto y número de lote.** Cada llegada de mercadería se carga como un lote (número, vencimiento y cantidad) del producto ya cargado en el catálogo. El número no se repite dentro del mismo producto, y no se carga un lote ya vencido; al corregirlo sí se acepta cualquier fecha, para poder arreglar un error de tipeo. No se registra el pedido ni el remito a la droguería, que queda fuera del alcance.

**Ajuste y retiro sin borrar.** La cantidad de un lote se corrige indicando la que queda (no la diferencia) y el retiro la deja en 0. El lote nunca se borra, porque las ventas lo referencian. No hay tabla de movimientos de stock: el histórico es aproximado, como se decidió al diseñar la base.

**FEFO como función reutilizable.** La elección del lote a descontar (primero el que vence antes, ignorando los vencidos y los agotados) es una función que no confirma la transacción, para que la venta la use dentro de la suya y se guarde todo junto o nada. Bloquea las filas de los lotes elegidos mientras dura la transacción, para que dos ventas simultáneas no descuenten el mismo stock. Se descartó un endpoint de descuento aparte, que dejaría la venta y el stock en operaciones separadas.

**Alertas calculadas al consultarlas.** El stock bajo (por debajo del mínimo) y los vencimientos (lotes vencidos o que vencen en los próximos N días, 30 por defecto) se calculan en cada consulta. Se descartó una tabla de alertas guardadas, que habría que mantener actualizada.

**La fecha de "hoy" se calcula en hora de Argentina.** Las reglas que dependen de la fecha (rechazar el alta de un lote vencido, contar el stock vendible, elegir lotes por FEFO y marcar alertas) usan una función `hoy()` basada en la zona `America/Argentina/Buenos_Aires`. Los servidores trabajan en UTC, 3 horas adelantados: entre las 21:00 y las 24:00 de Argentina ya marcarían el día siguiente y tratarían como vencido un lote que todavía se puede vender ese día. Se descartó cambiar la zona del contenedor, porque no se aplicaría en la nube, y sumar 3 horas fijas, que deja un número escrito a mano. Como Windows no trae la base de zonas horarias, se agrega el paquete `tzdata` a `requirements.txt`.

**Un único precio vigente por producto.** El precio vive en el producto y se cambia con la edición, producto por producto, solo por el farmacéutico y siempre mayor a 0. Las ventas ya hechas no cambian, porque el detalle de cada venta guarda el precio del momento; los reportes de facturación se calculan con ese precio y no con el actual. Se descartó una tabla de historial de precios, que queda como extensión futura, igual que la actualización masiva por porcentaje, por laboratorio o por tipo de producto.

**Medicamento como especialización del producto, con reglas propias.** Los datos de medicamento (principio activo, concentración, forma farmacéutica, si requiere receta, categoría de cobertura y clases terapéuticas) se cargan aparte del producto y solo para productos de tipo medicamento. Un medicamento exige laboratorio, y un producto que ya tiene datos de medicamento no puede cambiar de tipo, para no dejar datos huérfanos. Las clases terapéuticas se reemplazan como lista completa al editar, en lugar de agregarse o quitarse de a una, para que el resultado sea siempre el que mandó la pantalla.

**Baja lógica de productos y laboratorios.** Igual que con los empleados, se marcan como inactivos en lugar de borrarlos, porque las ventas los referencian. Un laboratorio dado de baja deja de ofrecerse y no se usa en productos nuevos, pero los productos que ya lo tenían lo conservan. El farmacéutico puede listar también los productos dados de baja (`?incluir_inactivos=true`) para poder reactivarlos.

**Carga de catálogos.** Los laboratorios y los principios activos se dan de alta desde el sistema, y pueden hacerlo los tres roles porque cualquiera puede encontrarse con uno nuevo al cargar mercadería. Como al cargar rápido se puede escribir mal un nombre, el farmacéutico puede renombrar un principio activo y borrarlo. A diferencia de los laboratorios, que se dan de baja, el principio activo se borra de verdad, pero solo si ningún medicamento lo usa (si lo usa alguno, el sistema lo rechaza): uno cargado por error no deja rastro, y no hace falta agregar una columna de baja a la base. Las 18 clases terapéuticas, las condiciones de IVA, las formas farmacéuticas y las categorías del PMO vienen precargadas en los datos iniciales y no tienen alta.

**Permisos del módulo.** Ver catálogos, productos, medicamentos y stock: los tres roles. Cargar productos, datos de medicamento y lotes: farmacéutico y auxiliar, porque el auxiliar recibe la mercadería de la droguería. Corregir o editar lo ya cargado (incluido el precio), dar de baja, ajustar o retirar lotes, ver las alertas y los productos dados de baja: solo el farmacéutico, porque es el profesional responsable de la farmacia y esas acciones modifican el stock y el catálogo de los que responde; por ejemplo, retirar un lote vencido para que no se venda. El dueño solo consulta.
