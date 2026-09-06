# Sistema de Gestión de Ventas y Cobertura para Farmacia de Pueblo

**Repositorio:** https://github.com/nahueldgo/farmacia-gestion

**Tablero de gestión (Trello):** https://trello.com/b/xqg3934a/sistema-gestion-farmacia-tfi

**Integrantes:**
- Esper, Amira Yasmin Elizabeth
- Dugo, Nahuel Lucas

**Tutor:** Fonzo, Santiago

---

## Descripción del problema

Una farmacia de un pueblo pequeño no cuenta con un sistema propio de gestión de ventas. La mayoría de sus operaciones son ventas de mostrador (medicamentos de venta libre, perfumería, elementos de cuidado personal, y venta de medicamentos sin cobertura), pero una porción corresponde a pacientes con cobertura de obras sociales locales, mutuales o gremios que no están integradas a validadores formales (IMED —el sistema de validación de Farmalink—, COFA), por no ser económicamente viable para entidades de ese tamaño.

Hoy esa validación se resuelve manualmente: por conocimiento directo de las reglas de cada entidad, consulta telefónica o planillas a mano para calcular descuento y copago, incluyendo el registro de pagos con tarjeta de crédito, tarjeta de débito, transferencia o QR. Este proceso es tan engorroso que en la práctica muchas farmacias terminan evitando la venta con obra social (ofreciendo en su lugar medicamentos sin descuento o genéricos), lo que en varios casos termina llevando a que el cliente compre en otra farmacia. Esto no es una decisión comercial libre, sino consecuencia de no contar con una herramienta que simplifique ese circuito. Al cierre del día, además, la caja se arma manualmente cruzando ventas, descuentos y medios de pago.

Esto genera pérdida de ventas evitables, errores de cálculo en descuentos/copagos que derivan en diferencias de caja, falta de trazabilidad histórica de ventas y rotación de productos, y doble carga administrativa al cierre. Como aproximación al impacto (a validar con los profesionales consultados, no es un dato medido): si se resignan en promedio 3 a 5 ventas semanales con obra social por la complejidad administrativa, con un ticket promedio de $15.000–$20.000, esto representaría entre $45.000 y $100.000 mensuales en ventas evitadas.

La propuesta surge de un relevamiento informal con una profesional farmacéutica y bioquímica en actividad, quien confirmó esta problemática. Adicionalmente, se consultó a un farmacéutico que trabaja con un sistema comercial de gestión, quien detalló las funcionalidades clave que utiliza a diario: actualización de precios, actualización de descuentos por obra social, validación de cobertura con respuesta inmediata por producto, control de stock, estadísticas filtrables por producto/período, y usuario individual por empleado. Esta segunda consulta permitió ajustar el alcance del proyecto a necesidades reales del rubro. Se prevén consultas adicionales durante el desarrollo.

---

## Actores involucrados

| Actor | Necesidad |
|---|---|
| **Auxiliar de Farmacia / Cajero / Personal de mostrador** | Vender de forma ágil medicamentos de venta libre, perfumería, elementos de cuidado personal y medicamentos sin cobertura, registrar ventas con cobertura de obra social, y controlar el stock. |
| **Dt. Farmacéutico/a (titular)** | Supervisar y ser responsable legal de las dispensaciones, configurar las reglas de cobertura por obra social, y realizar los pedidos a proveedores en base al stock. |
| **Dueño/a o gerente** | Visualizar la caja diaria consolidada, historial de ventas y métricas del negocio. |
| **Cliente con obra social local/gremial** | Ser atendido sin que la farmacia evite la venta por la complejidad administrativa. |

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

Aplicación de escritorio para uso interno de la farmacia (auxiliar de farmacia/cajero, Dt. farmacéutico/a, dueño/gerente), con backend y base de datos alojados en la nube. Centraliza el registro de ventas de mostrador y con cobertura de obras sociales locales/gremiales, automatiza el cálculo de copagos mediante reglas de cobertura configurables, definidas una vez por la farmacéutica según lo que cada entidad informa. El PMO argentino fija pisos mínimos legales que toda entidad debe cumplir (y puede igualar o mejorar): 40% para medicamentos ambulatorios en general, 70% para enfermedades crónicas prevalentes (hipertensión, diabetes en comprimidos), y 100% para categorías específicas como oncológicos, insulina, anticonceptivos (Ley 25.673), HIV y discapacidad (Ley 24.901). El sistema permite configurar estos porcentajes por categoría de medicamento y por entidad, ya que en la práctica varían según lo que cada obra social/mutual local decida ofrecer por encima del piso legal. El cierre de caja diario y la trazabilidad de lotes/vencimientos de stock completan el sistema. No incluye una tienda online para clientes finales: es el software de gestión interna de la farmacia.

A diferencia de sistemas comerciales como NOVA EVO o GEMA, esta propuesta no reemplaza la validación formal cuando existe, sino que cubre el segmento de coberturas que hoy se resuelven completamente a mano, calculando el copago automáticamente e integrándolo al registro de venta, stock y caja. Como el cálculo es completamente local, la respuesta al empleado es inmediata, sin tiempos de espera de red ni riesgo de caída de un servicio de terceros (una necesidad confirmada como crítica en la consulta con el farmacéutico que usa un sistema comercial de gestión).

**Diseño extensible.** El cálculo de cobertura se construye detrás de una interfaz (patrón *Strategy*), de modo que el motor de reglas manual pueda convivir a futuro con validadores externos reales (ValidaCOFA, u otros propios de obras sociales grandes como Swiss Medical o Sancor Salud) sin rediseñar el resto del sistema (esa integración requeriría que la farmacia esté homologada por cada entidad, y queda fuera del alcance de este TFI). La misma separación entre lógica de negocio y persistencia deja abiertas otras extensiones: un asistente basado en IA que, a partir del historial de ventas y el stock con trazabilidad de vencimientos, informe o sugiera compras a droguerías, y alerte cuando los medicamentos ingresados en un período determinado estén próximos a vencer (para gestionar a tiempo su devolución al proveedor o su descarte correcto según los protocolos de residuos farmacéuticos), sin automatizar la compra ni reemplazar la decisión del farmacéutico/a; y un frontend web para que los clientes hagan compras online reutilizando el mismo backend. Ninguna de las dos forma parte del alcance de este TFI.

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

## Análisis de viabilidad

**Eje temporal.** El proyecto se desarrolla en un plazo de 10 semanas (07/09 al 14/11), en paralelo con la cursada de otras 5 materias por parte de los integrantes del grupo, lo que reduce significativamente las horas semanales disponibles respecto a un desarrollo a tiempo completo. El plan de trabajo distribuye el desarrollo en 7 etapas, priorizando el núcleo funcional del proyecto al principio y dejando funcionalidades de menor criticidad hacia el final. El cronograma está comprimido al máximo dentro del límite fijo del 14/11, sin margen extra (el detalle de qué hacer ante un atraso se desarrolla en Riesgos y mitigaciones).

**Eje técnico.** El equipo cuenta con conocimientos previos de Python, HTML/CSS/JavaScript/TypeScript, programación orientada a objetos en Java, y modelado relacional con SQL, adquiridos durante la cursada. El stack elegido (FastAPI, SQLModel, PostgreSQL, React, TypeScript y Tailwind) coincide en gran parte con contenidos que se están viendo actualmente en la cursada, en paralelo al desarrollo del proyecto: relaciones de datos, consumo de APIs y autenticación JWT, entre otros. Esto reduce sustancialmente el riesgo de aprendizaje, ya que la mayor parte del stack no es autodidacta sino currícula formal en curso. Las únicas herramientas específicas no cubiertas por la cursada actual son Electron y Docker, que el equipo va a aprender de forma autodidacta durante el desarrollo. Se prioriza tecnología con documentación oficial extensa y gran comunidad de soporte, reservando un período de aprendizaje inicial antes de encarar la lógica de negocio más compleja.

**Eje de dominio y conocimiento.** El equipo no cuenta con experiencia directa en el rubro farmacéutico, por lo que la validación del problema y de la solución se apoyó en consultas externas a dos profesionales del sector: una farmacéutica y bioquímica en actividad, y un farmacéutico que trabaja con un sistema comercial de gestión (ver Descripción del problema). Ambas consultas fueron informales, no un relevamiento estructurado ni con múltiples farmacias, por lo que algunos datos (como la estimación de impacto económico) se presentan como aproximaciones a validar, no como datos medidos. Se prevén consultas adicionales durante el desarrollo.

---

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El motor de reglas de cobertura no es complejo a nivel algorítmico (el cálculo del copago es una multiplicación simple sobre el precio), pero sí lo es en su lógica de negocio: debe clasificar correctamente cada venta según varias categorías (PMO ambulatorio, crónico, oncológico, y casos específicos como anticonceptivos o insulina con porcentajes propios por ley) y cruzarlas con la regla de cada obra social. Un error de clasificación ahí afecta directamente el dinero cobrado en cada venta con cobertura | Alto | Se ubica en la primera mitad del cronograma (Etapa 4, no al final) y se testea de forma incremental, caso por caso |
| El cronograma no tiene margen extra (ver Análisis de viabilidad, eje temporal) | Alto | Ante un atraso, se recorta primero el detalle de Reportes (Etapa 6, dejando solo el consolidado que ya genera Caja); si persiste, se simplifica Cierre de Caja (Etapa 5) a un registro manual asistido, sin cálculo automático de diferencias. El motor de cobertura y el registro de ventas no se recortan, por ser el núcleo del proyecto |
| Dependencia de conexión a internet: al no incluir modo offline, si la farmacia pierde conectividad el sistema no puede operar (el backend y la base de datos están en la nube, requisito obligatorio de la consigna) | Alto | De nuestro lado, reintentos automáticos ante cortes breves de conexión (el caso más frecuente en zonas con señal inestable); como recomendación operativa, que la farmacia cuente con una conexión de respaldo (datos móviles) para cortes más prolongados |

**Sobre una implementación completamente local.** Para este TFI, el backend y la base de datos se mantienen en la nube porque es un requisito obligatorio de la consigna académica. En una implementación real de producción, la forma correcta de eliminar por completo el riesgo de conectividad sería que la aplicación fuera 100% local: una base de datos embebida en la propia máquina de la farmacia (por ejemplo SQLite, o una instancia local de PostgreSQL), con el backend corriendo también localmente o integrado directamente en la app de escritorio. La sincronización con la nube pasaría a ser un proceso secundario y periódico (backups, reportes centralizados entre sucursales), no una dependencia para operar. Esta migración es viable sin rediseñar el resto del sistema, porque la lógica de negocio ya está separada de la capa de persistencia.

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
- Integración real con validadores formales de obras sociales (IMED —el sistema de validación de Farmalink—, COFA, u otros propios de obras sociales grandes): el diseño queda preparado para incorporarlo a futuro (ver Diseño extensible), pero no se implementa en este TFI.
- Tienda online / venta a clientes por web (extensión futura posible, ver Diseño extensible).
- Modo offline (ver Riesgos y mitigaciones).
- Integración con hardware específico (lector de código de barras, impresora térmica).
- Facturación electrónica / integración con AFIP.
- Gestión de compras a proveedores o reposición automática de stock.
- Aplicación móvil nativa.

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

Docker Compose se usa exclusivamente para levantar el backend y la base de datos en el entorno de desarrollo local del equipo, evitando instalar PostgreSQL manualmente en cada máquina. El frontend/desktop no entra en ese mismo `docker-compose.yml`: corre en la máquina del cliente final (la farmacia) una vez empaquetado con Electron, y en producción el backend se despliega por separado en Render/Railway.

---

## Plan de trabajo

**Inicio:** 07/09/2026. **Fin:** 14/11/2026.

La división por Backend / Frontend / Conexión de cada etapa ya está armada en el [tablero de Trello](https://trello.com/b/xqg3934a/sistema-gestion-farmacia-tfi), donde cada módulo tiene sus tareas separadas y con fecha límite cargada. Las duraciones de abajo son estimaciones aproximadas (recién estamos arrancando y no tenemos tiempos reales medidos por tarea) que se van a ir ajustando a medida que avancemos.

| Etapa | Fechas | Backend | Frontend | Conexión |
|---|---|---|---|---|
| **1. Setup + modelado de BD** | 07/09 – 13/09 | Config. FastAPI + Docker Compose + conexión a BD; diseño de esquema con diagramas UML y DDL inicial | Setup Vite + React + Tailwind, estructura de carpetas | Config. inicial de Electron apuntando al build de Vite |
| **2. Usuarios y roles** | 14/09 – 27/09 | Endpoints login/JWT, modelo de usuario y roles | Pantalla de login, layout con navegación según rol | Login end-to-end probado |
| **3. Ventas + catálogo/stock** | 28/09 – 11/10 | CRUD productos/lotes, lógica FEFO, endpoint de venta | Pantallas de stock/alertas, pantalla de venta de mostrador | Integración completa del flujo de venta |
| **4. Motor de reglas de cobertura** | 12/10 – 25/10 | Modelo obra social + reglas, patrón Strategy, cálculo de copago | Configuración de obras sociales, integración en pantalla de venta | Testing incremental del cálculo, caso por caso |
| **5. Cierre de caja** | 26/10 – 01/11 | Apertura/cierre, movimientos manuales, diferencias de arqueo | Pantalla de arqueo por medio de pago | N/A |
| **6. Reportes** | 02/11 – 08/11 | Endpoints de estadísticas históricas | Pantallas de reportes | N/A |
| **7. Testing, ajustes y documentación final** | 09/11 – 14/11 | Pruebas end-to-end, corrección de bugs, documentación final e informe | | |

---

## Documentación

Además de este README, el proyecto cuenta con documentación de gestión aplicada específicamente a este caso, disponible en `/docs`:

- [Análisis de Riesgos, Supuestos y Restricciones](./docs/01-analisis-riesgos-supuestos-restricciones.md)
- [Gestión de Interesados (Stakeholders)](./docs/02-gestion-interesados.md)
- [Gestión del Alcance y Criterios de Aceptación](./docs/03-gestion-alcance.md)

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
docker-compose up --build
```

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
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Variables de entorno
cp .env.example .env
```

---

## Despliegue

- **Aplicación de escritorio:** distribución mediante instalador descargable (generado con Electron Builder); no requiere despliegue en la nube, se conecta al backend remoto.
- **Backend / API:** *(pendiente de definir; se completará al desplegar)*
- **Base de datos:** *(pendiente de definir; se completará al desplegar)*
