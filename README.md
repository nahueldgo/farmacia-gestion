# Sistema de Gestión de Ventas y Cobertura para Farmacia de Pueblo

**Repositorio:** https://github.com/nahueldgo/farmacia-gestion

**Tablero de gestión (Trello):** https://trello.com/b/xqg3934a/sistema-gestion-farmacia-tfi

**Integrantes:**
- Esper, Amira Yasmin Elizabeth
- Dugo, Nahuel Lucas

**Tutor:** Fonzo, Santiago

---

## Descripción del problema

Una farmacia de un pueblo pequeño no cuenta con un sistema propio de gestión de ventas. La mayoría de sus operaciones son ventas de mostrador (medicamentos de venta libre, perfumería, elementos de cuidado personal, y venta de medicamentos sin cobertura), pero una porción corresponde a pacientes con cobertura de obras sociales locales, mutuales o gremios que no están integradas a validadores formales (IMED, el sistema de validación de Farmalink, COFA), por no ser económicamente viable para entidades de ese tamaño.

Hoy esa validación se resuelve manualmente: por conocimiento directo de las reglas de cada entidad, consulta telefónica o planillas a mano para calcular descuento y copago, incluyendo el registro de pagos con tarjeta de crédito, tarjeta de débito, transferencia o QR. Este proceso es tan engorroso que en la práctica muchas farmacias terminan evitando la venta con obra social (ofreciendo en su lugar medicamentos sin descuento o genéricos), lo que en varios casos termina llevando a que el cliente compre en otra farmacia. Esto no es una decisión comercial libre, sino consecuencia de no contar con una herramienta que simplifique ese circuito. Al cierre del día, además, la caja se arma manualmente cruzando ventas, descuentos y medios de pago.

Esto genera pérdida de ventas evitables, errores de cálculo en descuentos/copagos que derivan en diferencias de caja, falta de trazabilidad histórica de ventas y rotación de productos, y doble carga administrativa al cierre. El impacto aproximado de cada uno de estos problemas se resume en la sección siguiente.

La propuesta surge de un relevamiento informal con una profesional farmacéutica y bioquímica en actividad, quien confirmó esta problemática, y de la consulta a un farmacéutico que trabaja con un sistema comercial de gestión (ver [Gestión de Interesados](./docs/02-gestion-interesados.md)).

---

## Impacto estimado y validación

Para dimensionar el problema se estimó su costo en cuatro frentes:

| Impacto | Estimación | Cómo se calcula |
|---|---|---|
| Ventas con obra social resignadas | $180.000 a $400.000 mensuales en ventas evitadas | 3 a 5 ventas semanales, con ticket promedio de $15.000 a $20.000, durante 4 semanas |
| Tiempo de cálculo de copagos | 5 a 10 minutos por venta con cobertura | Cálculo manual, por consulta telefónica o planilla |
| Cierre manual de caja (doble carga administrativa) | 13 a 26 horas mensuales | 30 a 60 minutos por día, durante 26 días de atención |
| Diferencias de caja por errores de cálculo | $4.000 a $20.000 mensuales | 2 a 4 veces por mes, por $2.000 a $5.000 cada una |

**Sobre estas cifras.** Todas las estimaciones de esta sección son ilustrativas: parten de supuestos razonables, no de datos medidos. Para validarlas se armó una encuesta de 18 preguntas dirigida a farmacias y a su personal ([Gestión y Cobertura en Farmacias](https://forms.gle/Rsm4E5Cpv6dL2kDcA)), cuyos resultados se reportarán tal como salgan, sean o no favorables a la propuesta: al ser un proyecto académico, lo que se busca es validar la necesidad con criterio, no confirmar la hipótesis inicial. Si los resultados no respaldan las estimaciones, se ajustarán y se documentará cómo afectan al alcance del proyecto. Los temas que cubre la encuesta están en [Decisiones de Arquitectura](./docs/04-decisiones-de-arquitectura.md#cuantificación-de-impactos-y-encuesta-punto-4).

---

## Análisis de competencia

| Alternativa | Qué resuelve | Por qué no cubre el problema actual |
|---|---|---|
| **Planilla manual** (competidor directo actual) | Es lo que usa hoy la farmacia: cálculo de copago a mano, cruce manual de ventas al cierre | Es lenta, propensa a errores, sin trazabilidad histórica y sin visibilidad en tiempo real (es la causa raíz del problema que motiva este proyecto) |
| **NOVA EVO / GEMA** (sistemas comerciales de gestión) | Gestión integral de farmacia (mostrador, stock, recetas electrónicas), con el validador de cobertura vendido como producto aparte o complementario (ej. Cloud RP de NOVA, o integración con IMED/Farmalink) | Ese validador aparte está pensado para integrarse con obras sociales/prepagas grandes (PAMI y similares); no cubre coberturas de una mutual o gremio local chico, que no tiene convenio con esos validadores |
| **Sistema propio (esta propuesta)** | Cubre el segmento que las otras dos opciones no resuelven: coberturas de entidades chicas, con reglas configurables en vez de integración formal costosa | N/A |

La planilla manual es, en la práctica, el competidor más relevante a superar: no porque sea una solución de software, sino porque es lo que efectivamente compite con este proyecto en el día a día de la farmacia.

---

## Descripción de la solución

Aplicación de escritorio para uso interno de la farmacia, con backend y base de datos alojados en la nube. La usan tres perfiles: el auxiliar de farmacia/cajero/personal de mostrador, el Dt. farmacéutico/a y el dueño/a o gerente (sus necesidades están en [Gestión de Interesados](./docs/02-gestion-interesados.md)). Centraliza el registro de ventas de mostrador y con cobertura de obras sociales locales/gremiales y automatiza el cálculo de copagos mediante reglas de cobertura configurables, definidas una vez por la farmacéutica según lo que cada entidad informa, sobre la base de los pisos mínimos del PMO (40% ambulatorios, 70% crónicos, 100% categorías especiales; el detalle está en [Gestión del Alcance](./docs/03-gestion-alcance.md)). El cierre de caja diario y la trazabilidad de lotes/vencimientos de stock completan el sistema. No incluye una tienda online para clientes finales: es el software de gestión interna de la farmacia.

A diferencia de sistemas comerciales como NOVA EVO o GEMA, esta propuesta no reemplaza la validación formal cuando existe, sino que cubre el segmento de coberturas que hoy se resuelven completamente a mano, calculando el copago automáticamente e integrándolo al registro de venta, stock y caja. Como el cálculo es completamente local, la respuesta al empleado es inmediata, sin tiempos de espera de red ni riesgo de caída de un servicio de terceros (una necesidad confirmada como crítica en la consulta con el farmacéutico que usa un sistema comercial de gestión).

La aplicación es de escritorio y no web porque el sistema se usa desde un puesto fijo de trabajo, el mostrador, donde una ventana propia y estable resulta más simple de operar que una pestaña de navegador, y porque es la forma en que operan los sistemas comerciales del rubro relevados como referencia (NOVA EVO y GEMA). El razonamiento completo está en [Decisiones de Arquitectura](./docs/04-decisiones-de-arquitectura.md).

**Diseño extensible.** El cálculo de cobertura se construye detrás de una interfaz (patrón *Strategy*), de modo que el motor de reglas manual pueda convivir a futuro con validadores externos reales sin rediseñar el resto del sistema. Esa arquitectura deja abiertas también otras extensiones (un asistente basado en IA para sugerir compras y alertar vencimientos, y un frontend web para clientes), ninguna dentro del alcance de este TFI. El detalle está en [Decisiones de Arquitectura](./docs/04-decisiones-de-arquitectura.md#diseño-extensible-patrón-strategy-y-extensiones-futuras).

---

## Objetivos

**Objetivo general:** desarrollar una aplicación de escritorio que centralice el registro de ventas de una farmacia (mostrador y con cobertura de obras sociales locales/gremiales), automatizando el cálculo de copagos mediante reglas configurables y el cierre de caja, para reducir la fricción administrativa que hoy lleva a evitar este tipo de ventas.

**Objetivos específicos:**
- Reducir el tiempo de atención en el mostrador para cualquier tipo de venta.
- Aumentar la proporción de ventas con obra social local/gremial efectivamente atendidas, hoy resignadas por la complejidad administrativa.
- Reducir a cero las diferencias de caja originadas en errores de cálculo manual de copagos.
- Eliminar la doble carga de trabajo administrativa al cierre del día.
- Dar visibilidad y trazabilidad al dueño/gerente sobre el desempeño real del negocio.
- Sostener la responsabilidad individual de cada operación de venta, identificando qué empleado la realizó.

---

## Viabilidad y riesgos

El análisis completo, con sus tres ejes y la tabla de riesgos con su mitigación, está en [Análisis de Riesgos, Supuestos y Restricciones](./docs/01-analisis-riesgos-supuestos-restricciones.md). En resumen:

- **Eje temporal:** 10 semanas (07/09 al 14/11), en paralelo con otras 5 materias y sin margen extra en el cronograma.
- **Eje técnico:** el stack elegido coincide en gran parte con lo que se está viendo en la cursada; solo Electron y Docker se aprenden de forma autodidacta.
- **Eje de dominio:** el equipo no tiene experiencia directa en el rubro, por lo que la validación depende de consultas externas y de la encuesta.
- **Riesgos principales:** la lógica de negocio del motor de reglas de cobertura, el cronograma sin margen (ante un atraso se recorta primero el detalle de Reportes y después el Cierre de Caja) y la dependencia de conexión a internet, ya que no hay modo offline (mitigada con reintentos automáticos y una conexión de respaldo; la alternativa 100% local para producción está en [Decisiones de Arquitectura](./docs/04-decisiones-de-arquitectura.md#conectividad-y-arquitectura-cloud-punto-1)).

---

## Alcance

**Incluye:**
- Registro de ventas de mostrador (medicamentos de venta libre, perfumería, elementos de cuidado personal y medicamentos sin cobertura).
- Actualización de precios y catálogo de productos.
- Módulo de configuración de reglas de cobertura por obra social/entidad.
- Cálculo automático de copago al momento de la venta, con respuesta inmediata.
- Registro de medios de pago (efectivo, tarjeta de crédito, tarjeta de débito, transferencia y QR).
- Cierre de caja diario automatizado (consolidado por tipo de venta y medio de pago).
- Control de stock con trazabilidad de lotes y vencimientos (alertas de stock por vencer).
- Reportes y estadísticas históricas: cantidad de tickets por producto, porcentajes de facturación, filtrables por día, mes y período.
- Gestión de usuarios con roles (auxiliar de farmacia/cajero/personal de mostrador, Dt. farmacéutico/a titular, dueño/gerente) e identificador único por empleado, vinculado a cada venta registrada.

**No incluye:**
- Integración real con validadores formales de obras sociales (IMED, el sistema de validación de Farmalink, COFA, u otros propios de obras sociales grandes): el diseño queda preparado para incorporarlo a futuro, pero no se implementa en este TFI. La justificación completa de lo que queda fuera está en [Gestión del Alcance](./docs/03-gestion-alcance.md).
- Tienda online / venta a clientes por web (extensión futura posible, ver [Decisiones de Arquitectura](./docs/04-decisiones-de-arquitectura.md#diseño-extensible-patrón-strategy-y-extensiones-futuras)).
- Modo offline (ver [Análisis de Riesgos, Supuestos y Restricciones](./docs/01-analisis-riesgos-supuestos-restricciones.md)).
- Integración con hardware específico (lector de código de barras, impresora térmica).
- Facturación electrónica / integración con AFIP.
- Gestión de compras a proveedores o reposición automática de stock.
- Aplicación móvil nativa.
- Trazabilidad detallada de ajustes manuales de stock y reversión automática al anular una venta: se permite corregir el stock manualmente y anular ventas, pero sin registro histórico de los ajustes ni reintegro automático del stock a los lotes de origen. Queda como extensión futura posible, ver [Gestión del Alcance](./docs/03-gestion-alcance.md).

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| Frontend | React + TypeScript + Vite + Tailwind |
| Empaquetamiento escritorio | Electron |
| Backend | Python + FastAPI |
| Base de datos | PostgreSQL |
| Autenticación | JWT |
| Contenedores | Docker + Docker Compose |
| Despliegue backend | Render / Railway |
| Despliegue base de datos | Supabase / Railway |
| Control de versiones | Git / GitHub |
| Gestión del proyecto | Trello |
| Otras herramientas | Postman, Draw.io, UML |

Para empaquetar el frontend como aplicación de escritorio se eligió Electron porque permite reutilizar el mismo frontend en React ya definido (las alternativas descartadas están en [Decisiones de Arquitectura](./docs/04-decisiones-de-arquitectura.md)). Como Electron no forma parte de lo visto en la carrera, se lo incorpora de forma autodidacta durante el desarrollo (ver el eje técnico en [Análisis de Riesgos, Supuestos y Restricciones](./docs/01-analisis-riesgos-supuestos-restricciones.md)).

Docker Compose se usa exclusivamente para levantar el backend y la base de datos en el entorno de desarrollo local del equipo, evitando instalar PostgreSQL manualmente en cada máquina. El frontend/desktop no entra en ese mismo `docker-compose.yml`: corre en la máquina del cliente final (la farmacia) una vez empaquetado con Electron, y en producción el backend se despliega por separado en Render/Railway.

---

## Plan de trabajo

**Inicio:** 07/09/2026. **Fin:** 14/11/2026.

La división por Backend / Frontend / Conexión de cada etapa ya está armada en el [tablero de Trello](https://trello.com/b/xqg3934a/sistema-gestion-farmacia-tfi), donde cada módulo tiene sus tareas separadas y con fecha límite cargada. Las duraciones de abajo son estimaciones aproximadas (recién estamos arrancando y no tenemos tiempos reales medidos por tarea) que se van a ir ajustando a medida que avancemos.

| Etapa | Fechas | Backend | Frontend | Conexión |
|---|---|---|---|---|
| **1. Setup + modelado de BD** | 07/09 - 13/09 | Config. FastAPI + Docker Compose + conexión a BD; diseño de esquema con diagramas UML y DDL inicial | Setup Vite + React + Tailwind, estructura de carpetas | Config. inicial de Electron apuntando al build de Vite |
| **2. Usuarios y roles** | 14/09 - 27/09 | Endpoints login/JWT, modelo de usuario y roles | Pantalla de login, layout con navegación según rol | Login end-to-end probado |
| **3. Ventas + catálogo/stock** | 28/09 - 11/10 | CRUD productos/lotes, lógica FEFO, endpoint de venta | Pantallas de stock/alertas, pantalla de venta de mostrador | Integración completa del flujo de venta |
| **4. Motor de reglas de cobertura** | 12/10 - 25/10 | Modelo obra social + reglas, patrón Strategy, cálculo de copago | Configuración de obras sociales, integración en pantalla de venta | Testing incremental del cálculo, caso por caso |
| **5. Cierre de caja** | 26/10 - 01/11 | Apertura/cierre, movimientos manuales, diferencias de arqueo | Pantalla de arqueo por medio de pago | N/A |
| **6. Reportes** | 02/11 - 08/11 | Endpoints de estadísticas históricas | Pantallas de reportes | N/A |
| **7. Testing, ajustes y documentación final** | 09/11 - 14/11 | Pruebas end-to-end, corrección de bugs, documentación final e informe | | |

---

## Documentación

Este README es un resumen del proyecto. El detalle está en la documentación de `/docs`, donde cada tema tiene su lugar:

- [Análisis de Riesgos, Supuestos y Restricciones](./docs/01-analisis-riesgos-supuestos-restricciones.md): análisis de viabilidad (tiempo, técnica, dominio), riesgos con su mitigación, supuestos y restricciones.
- [Gestión de Interesados (Stakeholders)](./docs/02-gestion-interesados.md): quiénes usan el sistema, quiénes validaron el problema y cómo se gestiona la comunicación con cada uno.
- [Gestión del Alcance y Criterios de Aceptación](./docs/03-gestion-alcance.md): pisos del PMO, criterios de aceptación por módulo y justificación de lo que queda fuera.
- [Decisiones de Arquitectura y Respuesta a la Primera Revisión](./docs/04-decisiones-de-arquitectura.md): decisiones técnicas con sus alternativas, la encuesta, el diseño extensible y cómo se resolvió cada punto de la primera revisión del tutor.
- [Diseño de la Base de Datos: Decisiones y Justificaciones](./docs/05-diseno-de-base-de-datos.md): modelo relacional, DER y justificación de cada entidad.

---

## Estructura del repositorio

```
/
├── frontend/          # Aplicación React + TypeScript + Vite (UI)
├── desktop/           # Empaquetado Electron (main process, builder config)
├── backend/           # API en FastAPI (Python)
├── database/          # Scripts DDL/DML, migraciones, esquemas PostgreSQL
├── docs/              # Documentación e informes de avance
├── docker-compose.yml # Orquestación de contenedores (backend, BD)
└── README.md
```

---

## Instalación y ejecución

**Requisitos previos:**
- Node.js v18+
- Python 3.11+
- Docker y Docker Compose
- PostgreSQL (o usar el contenedor incluido, no es necesario instalarlo manualmente)

### Backend + Base de datos (con Docker, opción recomendada)

```bash
git clone https://github.com/nahueldgo/farmacia-gestion
cd farmacia-gestion
cp .env.example .env    # en Windows: copy .env.example .env
docker-compose up --build
```

Editá el `.env` y reemplazá `SECRET_KEY` por una clave propia (por ejemplo, generada con `python -c "import secrets; print(secrets.token_hex(32))"`). El `.env` no se sube al repositorio.

Con el backend corriendo, cargá los usuarios de prueba en otra terminal:

```bash
docker-compose exec backend python seed.py
```

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin1234 | farmaceutico |
| auxiliar | auxiliar1234 | auxiliar |
| dueno | dueno1234 | dueno |

Son solo para desarrollo. La API se puede probar en http://localhost:8000/docs.

### Frontend (modo desarrollo, en navegador)

```bash
cd frontend
npm install
npm run dev
```

### Aplicación de escritorio (Electron)

```bash
cd desktop
npm install
npm run electron:dev    # ejecuta la app de escritorio en modo desarrollo
npm run electron:build  # genera el instalador (.exe / .dmg / .AppImage)
```

### Backend manual (sin Docker)

```bash
cp .env.example .env    # variables de entorno (desde la raíz del repositorio)
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Sin Docker, el backend lee `DATABASE_URL` y `SECRET_KEY` de las variables de entorno del sistema (con Docker las define el `docker-compose.yml` a partir del `.env`), por lo que hay que definirlas antes de ejecutar `uvicorn`.

---

## Despliegue

- **Aplicación de escritorio:** distribución mediante instalador descargable (generado con Electron Builder); no requiere despliegue en la nube, se conecta al backend remoto.
- **Backend / API:** se desplegará en Render o Railway (ver Tecnologías). La plataforma definitiva y la URL de producción se documentarán acá al momento de desplegar.
- **Base de datos:** PostgreSQL alojado en Supabase o Railway (ver Tecnologías). La plataforma definitiva y la forma de conexión se documentarán acá al momento de desplegar.
