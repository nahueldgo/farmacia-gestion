# Análisis de Riesgos, Supuestos y Restricciones

**Proyecto:** Sistema de Gestión de Ventas y Cobertura para Farmacia de Pueblo
**Equipo:** Esper, Amira · Dugo, Nahuel

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Estrategia de mitigación |
|---|---|---|---|
| Curva de aprendizaje de Electron para el empaquetado de escritorio, sin experiencia previa del equipo | Media | Medio | Se mantiene el mismo frontend React que el equipo ya está aprendiendo; Electron solo agrega la capa de empaquetado, no lógica de UI nueva |
| Equipo de 2 personas con plazos ajustados (30/08, 27/09, 14/11) frente a un alcance con varios módulos (ventas, cobertura, stock, caja) | Alta | Alto | Se definió explícitamente qué queda fuera de esta versión (ver "No incluye" en el README) para evitar scope creep; posibles extensiones quedaron documentadas pero no comprometidas |
| Nunca se integró frontend y backend en un proyecto real previo del equipo | Alta | Alto | Todo el stack elegido (FastAPI, SQLModel, PostgreSQL, React, TypeScript, Tailwind, JWT) se está viendo actualmente en la cursada, en paralelo al desarrollo del TFI, lo que reduce el riesgo de aprenderlo mientras se integra frontend y backend por primera vez. Solo Electron y Docker quedan fuera de la cursada actual |
| Dependencia de servicios gratuitos de despliegue (Render/Railway/Supabase) que pueden cambiar condiciones o tener límites de uso | Baja | Medio | Se eligieron por ser las opciones recomendadas por la cátedra; se evaluará migrar si hay problemas de disponibilidad |
| Reglas de cobertura definidas con una sola fuente de validación (una farmacéutica consultada informalmente) pueden no representar todos los casos reales | Media | Medio | Se prevén consultas adicionales durante el desarrollo, según lo indicado en la validación del problema |
| Falta de tiempo para pulir la app de escritorio si se agregan funcionalidades no planificadas | Media | Alto | Alcance cerrado por escrito en el README; cualquier adición se evalúa contra el cronograma antes de aceptarla |
| El motor de reglas de cobertura (Etapa 4 del plan de trabajo) no es complejo a nivel algorítmico (el cálculo del copago es una multiplicación simple sobre el precio), pero sí lo es en su lógica de negocio: debe clasificar correctamente cada venta según varias categorías (PMO ambulatorio, crónico, oncológico, y casos específicos como anticonceptivos o insulina con porcentajes propios por ley) y cruzarlas con la regla de cada obra social | Alta | Alto | Se ubica en la primera mitad del cronograma (no al final) y se testea de forma incremental. **Si el cronograma se atrasa:** primero se recorta el detalle de Reportes (Etapa 6), dejando solo el consolidado básico; si el atraso persiste, se simplifica Cierre de Caja (Etapa 5) a un registro manual asistido sin cálculo automático de diferencias. El motor de cobertura y el registro de ventas no se recortan, por ser el núcleo del valor del proyecto |
| Dependencia total de conexión a internet: al no incluir modo offline, si la farmacia pierde conectividad o tiene bajo rendimiento de red, el sistema no puede utilizarse | Media | Alto | Se documenta como riesgo aceptado dado el tamaño del equipo y los plazos (ver Restricciones). **Mitigación recomendada:** que la farmacia cuente con una conexión de respaldo (ej. datos móviles/hotspot) para continuidad ante cortes del proveedor principal. El modo offline queda documentado como extensión futura posible, no como algo resuelto en esta versión |

## Supuestos

- El relevamiento informal con la farmacéutica y bioquímica consultada es representativo del problema en general, aunque no es un relevamiento formal con múltiples farmacias.
- Las reglas de cobertura pueden modelarse con un esquema de porcentajes configurables por categoría de medicamento (PMO: 100% oncológicos/especiales, 70% crónicos, 40% ambulatorios; pisos mínimos legales que cada entidad puede igualar o mejorar) sin necesidad de lógica más compleja para la primera versión.
- El equipo podrá dedicar el tiempo necesario al proyecto en paralelo con el resto de las materias cursadas.
- Los servicios en la nube elegidos (Render/Railway, Supabase) se mantendrán disponibles en su capa gratuita durante todo el desarrollo del TFI.
- No existe, y no va a aparecer durante el desarrollo, una API pública y gratuita para validar coberturas de obras sociales locales/gremiales (se investigó activamente y se descartó esa posibilidad; ver justificación del alcance en el README).

## Restricciones

| Tipo | Restricción |
|---|---|
| **Tiempo** | Fechas fijas de la cátedra: Propuesta (30/08), Diseño y Módulos (27/09), Informe Final (14/11) |
| **Recursos** | Equipo de 2 personas, sin roles previamente definidos de especialización |
| **Técnicas** | Frontend en React + TypeScript + Tailwind y backend en Python + FastAPI, ambos cubiertos por contenidos que se están viendo actualmente en la cursada (se apoya además en base previa de JS/TS/HTML/CSS y SQL vistos anteriormente); despliegue con al menos un componente en la nube (requisito de la cátedra) |
| **Presupuesto** | Cero presupuesto: se descartó cualquier integración que requiera suscripción paga (ej. base de datos de medicamentos de Alfabeta.net) a favor de fuentes públicas y gratuitas (ANMAT/Datos Abiertos) |
| **Legales/Normativas** | El sistema no reemplaza la validación formal de obras sociales grandes (PAMI, prepagas) donde esta ya existe; no gestiona facturación electrónica ni integración con AFIP en esta versión |

## Relación entre riesgos, supuestos y restricciones (aplicado al proyecto)

Un ejemplo concreto del proyecto: se **asume** que dos personas pueden cubrir todo el alcance definido en los plazos de la cátedra (supuesto). Si ese supuesto no se cumple, se convierte en el **riesgo** más alto identificado (no llegar a tiempo). Ese riesgo está agravado por la **restricción** de tiempo fija impuesta por la cátedra, que no se puede negociar. La mitigación elegida fue reducir el alcance activamente (dejando fuera hardware, offline, integraciones externas) en lugar de intentar abarcar todo con el mismo plazo.
