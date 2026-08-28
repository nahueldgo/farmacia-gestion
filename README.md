# Sistema de Gestión de Ventas y Cobertura para Farmacia de Pueblo

**Repositorio:** https://github.com/nahueldgo/farmacia-gestion
**Tablero de gestión (Trello):** https://trello.com/b/xqg3934a/sistema-gestion-farmacia-tfi

**Integrantes:**
- Esper, Amira Yasmin Elizabeth
- Dugo, Nahuel Lucas

**Tutor:** Fonzo, Santiago

---

## Descripción del problema

Una farmacia de un pueblo pequeño no cuenta con un sistema propio de gestión de ventas. La mayoría de sus operaciones son ventas de mostrador (venta libre y perfumería), pero una porción corresponde a pacientes con cobertura de obras sociales locales, mutuales o gremios que no están integradas a validadores formales (IMED, Farmalink, COFA), por no ser económicamente viable para entidades de ese tamaño.

Hoy esa validación se resuelve manualmente: por conocimiento directo de las reglas de cada entidad, consulta telefónica o planillas a mano para calcular descuento y copago, incluyendo el registro de pagos con tarjeta. Este proceso es tan engorroso que en la práctica muchas farmacias terminan evitando activamente las ventas con obra social y priorizando genéricos, no por decisión comercial sino por falta de una herramienta adecuada. Al cierre del día, además, la caja se arma manualmente cruzando ventas, descuentos y medios de pago.

Esto genera:

- Pérdida de ventas evitables.
- Errores de cálculo en descuentos/copagos (diferencias de caja).
- Falta de trazabilidad histórica de ventas y rotación de productos.
- Doble carga administrativa al cierre.

**Validación:** la propuesta surge de un relevamiento informal con una profesional farmacéutica y bioquímica en actividad, quien confirmó esta problemática. Adicionalmente, se consultó a un farmacéutico que trabaja con un sistema comercial de gestión, quien detalló las funcionalidades clave que utiliza a diario (actualización de precios, actualización de descuentos por obra social, validación de cobertura con respuesta inmediata por producto, control de stock, estadísticas filtrables por producto/período, y usuario individual por empleado). Esta segunda consulta permitió ajustar el alcance del proyecto a necesidades reales del rubro. Se prevén consultas adicionales durante el desarrollo para seguir ajustando el alcance a la realidad operativa.

---

## Actores involucrados

| Actor | Necesidad |
|---|---|
| **Empleado de mostrador** | Vender de forma ágil productos genéricos, de venta libre y perfumería. |
| **Farmacéutico/a** | Calcular coberturas de obras sociales locales/gremiales, controlar stock y, en base a ese control, realizar los pedidos a proveedores. |
| **Dueño/a o gerente** | Visualizar la caja diaria consolidada, historial de ventas y métricas del negocio. |
| **Cliente con obra social local/gremial** | Ser atendido sin que la farmacia evite la venta por la complejidad administrativa. |

---

## Descripción de la solución

Aplicación de escritorio para uso interno de la farmacia (mostrador, farmacéutico/a, dueño/gerente), con backend y base de datos alojados en la nube. Centraliza el registro de ventas (mostrador y con cobertura de obras sociales locales/gremiales), automatiza el cálculo de copagos mediante reglas de cobertura configurables (definidas una vez por la farmacéutica según lo que cada entidad informa, ej. PMO al 100%, crónicas al 80%, resto al 40%), el cierre de caja diario y la trazabilidad de lotes/vencimientos de stock. No incluye una tienda online para clientes finales — es el software de gestión interna de la farmacia.

A diferencia de sistemas comerciales como Farmalink o Nubimed —pensados para grandes prepagas y obras sociales, con convenios no viables para entidades pequeñas—, esta propuesta no reemplaza la validación formal cuando existe, sino que cubre el segmento de coberturas que hoy se resuelven completamente a mano, calculando el copago automáticamente e integrándose al registro de venta, stock y caja, sin depender de una integración externa costosa.

Como el cálculo de cobertura es completamente local (no depende de un validador externo), la respuesta al empleado es inmediata por diseño, sin tiempos de espera de red ni riesgo de caída de un servicio de terceros — una necesidad que se confirmó como crítica al consultar con un farmacéutico que usa un sistema comercial de gestión.

**Nota de arquitectura (extensibilidad futura):** el cálculo de cobertura se diseña detrás de una interfaz (patrón *Strategy*), de modo que el motor de reglas manual pueda convivir a futuro con validadores externos reales (ValidaCOFA, u otros propios de obras sociales grandes como Swiss Medical, Sancor Salud, etc.), sin rediseñar el resto del sistema. Esa integración real requeriría que la farmacia esté homologada por cada entidad y queda fuera del alcance de este TFI, pero el diseño no bloquea esa posibilidad.

También se deja planteada como posible extensión futura la incorporación de un asistente basado en IA que, a partir del historial de ventas y el stock con trazabilidad de vencimientos, sugiera al farmacéutico/a qué reponer y en qué cantidad (sin automatizar la compra ni reemplazar su decisión). No forma parte del alcance de este TFI.

Por último, dado que el backend expone una API REST independiente de la interfaz de escritorio, queda abierta la posibilidad de sumar a futuro un frontend web para que los clientes realicen compras online (consultando stock y coordinando el pago/retiro), reutilizando el mismo backend sin rediseñar. Tampoco forma parte del alcance de este TFI.

---

## Objetivos

**Objetivo general:** desarrollar una aplicación de escritorio que centralice el registro de ventas de una farmacia (mostrador y con cobertura de obras sociales locales/gremiales), automatizando el cálculo de copagos mediante reglas configurables y el cierre de caja, para reducir la fricción administrativa que hoy lleva a evitar este tipo de ventas.

**Objetivos específicos:**
- Permitir el registro ágil de ventas de mostrador (venta libre y perfumería) sin fricciones.
- Permitir configurar reglas de cobertura por obra social/entidad y calcular automáticamente el copago al momento de la venta, con respuesta inmediata.
- Automatizar el cierre de caja diario, consolidando ventas por tipo y medio de pago.
- Mantener actualizado el catálogo de productos y precios.
- Brindar visibilidad histórica mediante reportes y estadísticas filtrables por producto y por período (día, mes).
- Identificar de forma individual a cada empleado en el sistema, asociando cada venta a su usuario.

---

## Alcance

**Incluye:**
- Registro de ventas de mostrador (venta libre y perfumería).
- Actualización de precios y catálogo de productos.
- Módulo de configuración de reglas de cobertura por obra social/entidad.
- Cálculo automático de copago al momento de la venta, con respuesta inmediata (sin dependencia de validadores externos).
- Registro de medios de pago (efectivo, tarjeta).
- Cierre de caja diario automatizado (consolidado por tipo de venta y medio de pago).
- Control de stock con trazabilidad de lotes y vencimientos (alertas de stock por vencer).
- Reportes y estadísticas históricas: cantidad de tickets por producto, porcentajes de facturación, filtrables por día, mes y período.
- Gestión de usuarios con roles (empleado de mostrador, farmacéutico/a, dueño/gerente) e identificador único por empleado, vinculado a cada venta registrada.

**No incluye:**
- Integración real con validadores formales de obras sociales (IMED, Farmalink, COFA, u otros propios de obras sociales grandes) — el diseño queda preparado para incorporarlo a futuro, pero no se implementa en este TFI.
- Tienda online / venta a clientes por web (queda como extensión futura posible — ver nota de arquitectura más arriba).
- Modo offline (la aplicación requiere conexión a internet para operar, ya que el backend y la base de datos están en la nube).
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
| Otras herramientas | Postman, Draw.io |

---

## Plan de trabajo (Fecha limite de entrega 14/11)

| Etapa | Duración estimada |
|---|---|
| Setup del proyecto + modelado de base de datos | 2 semanas |
| Autenticación y gestión de usuarios/roles | 2 semanas |
| Ventas de mostrador + catálogo/precios/stock | 2 semanas |
| Motor de reglas de cobertura (cálculo de copagos) | 2 semanas |
| Cierre de caja diario | 1 semana |
| Reportes y estadísticas | 1 semana |
| Testing, ajustes y documentación final | 1 semana |

> El motor de reglas de cobertura es la etapa de mayor riesgo por su complejidad de lógica de negocio, por lo que se prioriza y se documenta y testea de forma incremental a medida que avanza el desarrollo, en lugar de dejarlo concentrado en la última semana.

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
- PostgreSQL (o usar el contenedor incluido — no es necesario instalarlo manualmente)

### Backend + Base de datos (con Docker — opción recomendada)

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

- **Aplicación de escritorio:** distribución mediante instalador descargable (generado con Electron Builder) — no requiere despliegue en la nube, se conecta al backend remoto.
- **Backend / API:** *(pendiente de definir — se completará al desplegar)*
- **Base de datos:** *(pendiente de definir — se completará al desplegar)*
