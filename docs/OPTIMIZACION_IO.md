# FinaGotchi · Optimización con Investigación de Operaciones

Documento técnico de la **optimización de metas de ahorro** implementada en el
backend con programación lineal. Describe el problema, el modelo matemático, las
fuentes de datos, el contrato de la API y los criterios de aceptación.

| Dato | Valor |
|---|---|
| Versión del documento | 1.0 |
| Fecha de corte | 2026-11-05 |
| Rama de referencia | `michelle` |
| Módulos | `backend/finance_engine.py`, `backend/optimization.py` |
| Endpoints | `GET /api/v1/goals/plan`, `POST /api/v1/goals/plan/simulate` |
| Estado | Implementado y probado |

> **Regla de oro.** La optimización **solo propone**. Nunca crea transacciones,
> nunca mueve saldos, nunca modifica metas y nunca sustituye la confirmación
> humana. El plan se calcula en cada petición y no se persiste como estado
> maestro.

---

## 1. Alcance y decisión

### 1.1 Decisión

Se implementa **solo la opción 1** de la propuesta de Investigación de
Operaciones: **optimización de presupuesto y metas de ahorro con programación
lineal**.

Quedan **fuera de alcance por ahora**:

- EOQ y modelos de inventario.
- Reposición de efectivo y gastos hormiga.
- Pronósticos estocásticos de gasto.
- Persistencia de planes y alertas.
- Cambios de esquema o migraciones.

### 1.2 Qué resuelve

Un usuario tiene varias metas de ahorro con montos, prioridades y fechas límite
distintas, pero su capacidad mensual de ahorro es limitada. El planificador
calcula **cuánto asignar a cada meta en cada mes** para maximizar el
cumplimiento ponderado por prioridad, sin exceder la capacidad ni asignar dinero
después de una fecha límite.

### 1.3 Qué devuelve

- Capacidad mensual de ahorro estimada.
- Asignación mensual por meta.
- Cumplimiento esperado y faltante proyectado.
- Restricciones activas.
- Diagnóstico legible y recomendaciones.

### 1.4 Estado de implementación

| Componente | Estado |
|---|---|
| `finance_engine.monthly_capacity` | Implementado |
| `optimization.plan_goals` con HiGHS | Implementado |
| Redondeo entero COP | Implementado |
| Fallback greedy sin SciPy | Implementado |
| `GET /goals/plan` | Implementado |
| `POST /goals/plan/simulate` | Implementado |
| `GET /home?incluir_plan=1` | Implementado |
| Pantalla `[P]` del simulador | Implementado |
| EOQ, inventarios y gastos hormiga | Futuro |
| Persistencia de planes | Futuro |

---

## 2. Ubicación en la arquitectura

```text
backend/
  finance_engine.py     # cálculo puro: ingreso, gasto, colchón, capacidad
  optimization.py       # modelo LP, solver, redondeo, fallback y diagnóstico
  services.py           # orquestación y helpers de metas
  server.py             # endpoints de solo lectura
tests/
  test_finance_engine.py
  test_optimization.py
  test_api_optimization.py
```

Reglas de diseño:

1. Toda función de cálculo recibe `conn`, `usuario_id`, `as_of` y parámetros.
2. Ninguna función usa `date('now')` de forma interna: la fecha se pasa desde
   el endpoint.
3. Las funciones devuelven diccionarios serializables.
4. Los módulos de cálculo **no escriben** en la base.
5. Los endpoints son de solo lectura y requieren `Authorization: Bearer`.

---

## 3. Entradas y fuentes de datos

### 3.1 Metas

Fuente: `v_metas_progreso` y `metas`.

| Campo | Origen | Uso |
|---|---|---|
| `meta_id` | `metas.id` | Identificador |
| `nombre` | `metas.nombre` | Presentación |
| `monto_meta` | `metas.monto_meta` | Objetivo `M_i` |
| `ahorrado` | `v_metas_progreso.ahorrado` | Ahorro actual `S_i` |
| `fecha_limite` | `metas.fecha_limite` | Plazo `d_i` |
| `prioridad` | `metas.prioridad` | Peso `p_i`, validado entre 1 y 5 |
| `estado` | `metas.estado` | Se incluyen solo metas activas |

Solo se planean metas con `estado = 'activa'`, `is_deleted = 0` y
`monto_meta > ahorrado`. Las metas ya cumplidas o vencidas se informan aparte y
no consumen capacidad.

### 3.2 Ingreso

Fuentes:

- **Declarado:** `perfil_financiero.ingreso_total_mensual`, columna generada.
- **Observado:** ingresos confirmados de los últimos 90 días proyectados a 30
  días. Es conservador cuando hay pocos datos.

```text
ingreso_observado = round(Σ ingresos de 90 días × 30 / 90)
```

Si no hay ingresos en la ventana, la fuente observada es `None`.

Criterio conservador por defecto:

```text
ingreso_estimado = min(ingreso_declarado, ingreso_observado)
```

- Si solo existe una fuente, se usa esa.
- Si no existe ninguna, el ingreso estimado es 0 y se devuelve diagnóstico
  `PERFIL_INCOMPLETO`.
- La simulación puede sobrescribir el ingreso.

### 3.3 Gasto planificado

Para evitar doble conteo entre el presupuesto diario y los gastos fijos:

```text
gasto_planificado_t =
    suma de límites mensuales aprobados       si existe presupuesto aprobado vigente
    presupuesto_diario × días_del_mes         en caso contrario
```

Si tampoco hay presupuesto diario, se usa 0 y se reporta menor confianza.

### 3.4 Colchón de liquidez

```text
colchon_t = colchon_pct × ingreso_estimado_t
```

`colchon_pct` se expresa en porcentaje (0–50) y por defecto es 10 %.

### 3.5 Capacidad mensual

```text
C_t = max(0, ingreso_estimado_t − gasto_planificado_t − colchon_t)
```

El primer mes se prorratea por los días restantes:

```text
C_1 = max(0, C_1 × dias_restantes / dias_del_mes)
```

---

## 4. Modelo matemático

### 4.1 Conjuntos y parámetros

| Símbolo | Significado |
|---|---|
| `I` | Metas activas |
| `T = {1..H}` | Meses del horizonte |
| `M_i` | Monto objetivo |
| `S_i` | Ahorrado actual |
| `p_i` | Prioridad (1–5) |
| `T_i` | Meses disponibles hasta la fecha límite |
| `C_t` | Capacidad de ahorro del mes `t` |

### 4.2 Variables

```text
x_{i,t} ≥ 0    dinero asignado a la meta i en el mes t
y_i ∈ [0, 1]   fracción de cumplimiento de la meta i
```

### 4.3 Función objetivo

```text
max Z = Σ_i p_i · y_i − ε · Σ_i Σ_t (t / H) · x_{i,t}
```

El segundo término desempata a favor de asignar antes, sin cambiar el
cumplimiento. `ε` es un valor pequeño y positivo.

### 4.4 Restricciones

```text
1) Σ_i x_{i,t} ≤ C_t                        para todo t
2) S_i + Σ_{t=1..T_i} x_{i,t} ≥ M_i · y_i   para toda meta i
3) 0 ≤ y_i ≤ 1
4) x_{i,t} = 0 si t > T_i
```

### 4.5 Equivalencia en forma estándar

El solver trabaja con `linprog` en forma de minimización:

- `c = [−p_i para y_i, ε·t/H para x_{i,t}]`.
- Restricciones de capacidad como `A_ub x ≤ b_ub`.
- Restricciones de cumplimiento como `−S_i − Σ x_{i,t} + M_i·y_i ≤ 0`.
- Cotas `x ≥ 0`, `0 ≤ y ≤ 1`.
- Las variables fuera del plazo se fijan en 0 con cota superior 0.

---

## 5. Solver, redondeo y fallback

### 5.1 Solver

- `scipy.optimize.linprog(method="highs")`.
- Si SciPy no está disponible, se usa un **fallback greedy** determinista:
  ordena metas por prioridad descendente y fecha límite ascendente, y asigna
  mes a mes hasta agotar la capacidad.
- El fallback siempre devuelve un plan válido, aunque no sea óptimo.

### 5.2 Redondeo

Los montos son enteros COP. El LP devuelve flotantes:

1. Redondear hacia abajo.
2. Repartir el remanente por mayor parte fraccionaria.
3. Verificar que ninguna suma mensual supere `C_t`.
4. Devolver enteros.

### 5.3 Determinismo

Mismos datos de entrada producen exactamente el mismo plan. El orden de metas y
el desempate son estables.

---

## 6. Contrato de la API

Todas las respuestas usan el sobre habitual:

```json
{"ok": true, "data": {...}}
```

Los errores usan:

```json
{"ok": false, "error": {"codigo": "...", "mensaje": "...", "detalles": {}}}
```

### 6.1 `GET /api/v1/goals/plan`

Parámetros de consulta:

| Parámetro | Tipo | Obligatorio | Rango | Descripción |
|---|---|---|---|---|
| `meses` | entero | No | 1–24 | Horizonte; por defecto 12 |
| `fecha` | fecha | No | `YYYY-MM-DD` | Fecha de cálculo; por defecto hoy en Bogotá |
| `colchon_pct` | número | No | 0–50 | Colchón sobre el ingreso; por defecto 10 |

Respuesta `data`:

```json
{
  "as_of": "2026-11-05",
  "horizonte_meses": 12,
  "moneda": "COP",
  "simulacion": false,
  "factible": true,
  "solver": "highs",
  "confianza": "alta",
  "entradas": {
    "ingreso_declarado": 1500000,
    "ingreso_observado": 1200000,
    "ingreso_estimado": 1200000,
    "gasto_planificado_mensual": 800000,
    "colchon_pct": 10.0,
    "colchon_mensual": 120000,
    "fuente_ingreso": "minimo_declarado_observado",
    "fuente_presupuesto": "presupuesto_mensual"
  },
  "capacidad_mensual": [
    {
      "indice": 1,
      "mes": "2026-11",
      "dias_mes": 30,
      "dias_disponibles": 26,
      "ingreso_estimado": 1040000,
      "gasto_planificado": 693333,
      "colchon": 104000,
      "capacidad": 242667
    }
  ],
  "metas": [
    {
      "meta_id": 3,
      "nombre": "Fondo de emergencia",
      "prioridad": 5,
      "monto_meta": 1000000,
      "ahorrado_actual": 200000,
      "faltante_inicial": 800000,
      "fecha_limite": "2027-06-30",
      "meses_disponibles": 8,
      "asignacion_mensual": [30000, 30000, 30000, 30000, 30000, 30000, 30000, 30000],
      "total_asignado": 240000,
      "saldo_proyectado": 440000,
      "cumplimiento": 0.44,
      "faltante_proyectado": 560000,
      "mes_estimado_cumplimiento": null,
      "estado": "parcial"
    }
  ],
  "resumen": {
    "capacidad_total": 2912004,
    "total_asignado": 500000,
    "metas_totales": 3,
    "metas_completadas": 0,
    "metas_parciales": 3,
    "metas_sin_asignacion": 0,
    "cumplimiento_ponderado": 0.52
  },
  "restricciones_activas": ["capacidad_mes_1"],
  "diagnostico": {
    "nivel": "info",
    "codigo": "CAPACIDAD_LIMITADA",
    "mensaje": "La capacidad alcanza para el 52 % del plan ponderado.",
    "recomendaciones": [
      "Prioriza la meta de mayor prioridad o reduce gastos variables."
    ]
  }
}
```

Valores de `estado` por meta:

| Estado | Significado |
|---|---|
| `completada` | `saldo_proyectado ≥ monto_meta` |
| `parcial` | Recibió asignación, pero no alcanza el monto |
| `sin_asignacion` | Capacidad insuficiente o plazo vencido |

`mes_estimado_cumplimiento` es `0` cuando la meta ya estaba completa antes del
plan; es `null` cuando no se alcanza dentro del horizonte.

Los montos de `asignacion_mensual` son enteros COP y su suma por mes nunca
supera la capacidad de ese mes.

Valores de `confianza`:

| Valor | Condición |
|---|---|
| `alta` | Ingreso declarado y observado disponibles y consistentes |
| `media` | Solo una fuente de ingreso o presupuesto estimado |
| `baja` | Sin ingreso o sin presupuesto |

Casos especiales:

- Sin metas: `metas = []`, `factible = true`, diagnóstico `SIN_METAS`.
- Sin ingreso: capacidad 0, diagnóstico `PERFIL_INCOMPLETO`.
- Sin capacidad pero con metas: plan vacío, diagnóstico `SIN_CAPACIDAD`.
- Meta vencida: no recibe asignación, estado `sin_asignacion`.

### 6.2 `POST /api/v1/goals/plan/simulate`

Cuerpo JSON (todos los campos son opcionales salvo que se indique):

```json
{
  "meses": 12,
  "fecha": "2026-11-05",
  "ingreso_mensual": 1500000,
  "gasto_mensual": 800000,
  "colchon_pct": 10,
  "capacidad_mensual": 300000,
  "prioridades": {"3": 5, "4": 2},
  "incluir_metas": [3, 4]
}
```

| Campo | Tipo | Rango | Efecto |
|---|---|---|---|
| `meses` | entero | 1–24 | Horizonte |
| `fecha` | fecha | `YYYY-MM-DD` | Fecha base |
| `ingreso_mensual` | entero | ≥ 0 | Sobrescribe el ingreso estimado |
| `gasto_mensual` | entero | ≥ 0 | Sobrescribe el gasto planificado |
| `colchon_pct` | número | 0–50 | Sobrescribe el colchón |
| `capacidad_mensual` | entero | ≥ 0 | Fija la capacidad de todos los meses |
| `prioridades` | objeto | 1–5 | Sobrescribe prioridades por `meta_id` |
| `incluir_metas` | arreglo | — | Limita el plan a esas metas |

La respuesta tiene la misma estructura que `GET`, con `"simulacion": true` y un
objeto `"overrides"` que repite los valores aplicados.

Errores de validación:

| Código | Situación |
|---|---|
| `PARAMETRO_INVALIDO` | Tipo, rango o fecha inválidos |
| `META_INEXISTENTE` | `incluir_metas` o `prioridades` con id ajeno o inexistente |

### 6.3 Integración opcional en `/home`

`GET /api/v1/home?incluir_plan=1` agrega `data.plan_ahorro` con un resumen
compacto:

```json
{
  "horizonte_meses": 12,
  "factible": true,
  "solver": "highs",
  "confianza": "media",
  "capacidad_mes_actual": 250000,
  "metas": [
    {
      "meta_id": 3,
      "nombre": "Fondo de emergencia",
      "prioridad": 5,
      "asignacion_mes_actual": 30000,
      "total_asignado": 240000,
      "cumplimiento": 0.44,
      "estado": "parcial",
      "mes_estimado_cumplimiento": null
    }
  ],
  "resumen": {
    "capacidad_total": 2912004,
    "total_asignado": 500000,
    "metas_totales": 1,
    "metas_completadas": 0,
    "metas_parciales": 1,
    "metas_sin_asignacion": 0,
    "cumplimiento_ponderado": 0.44
  },
  "diagnostico": {
    "nivel": "info",
    "codigo": "CAPACIDAD_LIMITADA",
    "mensaje": "La capacidad alcanza para el 44 % del plan ponderado.",
    "recomendaciones": ["Prioriza la meta de mayor prioridad o reduce gastos variables."]
  }
}
```

Sin la bandera, `/home` no ejecuta el LP. El resumen no incluye la matriz
completa de asignaciones para mantener liviana la pantalla de inicio.

---

## 7. Aplicación en FinaGotchi

- **Pantalla de metas:** muestra la asignación mensual recomendada y el mes
  estimado de cumplimiento.
- **Mascota:** usa el diagnóstico para cambiar el diálogo; por ejemplo,
  `CAPACIDAD_LIMITADA` produce un consejo de repriorización.
- **Simulador:** la opción `[P]` del menú consulta `GET /goals/plan` y muestra
  capacidad del mes, metas y cumplimiento. Para probar escenarios se usa
  `POST /goals/plan/simulate`; ninguno de los dos modifica la base.
- **Dispositivo:** consume el resumen de solo lectura; el cálculo queda en el
  backend. El firmware aún no implementa la pantalla.
- **Cierre del día:** no depende del plan. La IO nunca bloquea operaciones.

---

## 8. Supuestos y limitaciones

1. El presupuesto diario representa el gasto total del mes; si hay presupuesto
   mensual aprobado, se usa ese para evitar doble conteo.
2. La prioridad es un peso ordinal; no representa dinero.
3. El ingreso es constante durante el horizonte, salvo el prorrateo del primer
   mes.
4. El plan es una recomendación, no una orden ni una autorización de gasto.
5. No se modelan imprevistos, inflación ni variaciones estacionales.
6. El fallback greedy puede ser subóptimo, pero es válido y determinista.
7. Los resultados dependen de la calidad del perfil financiero y del historial.

---

## 9. Pruebas y criterios de aceptación

- Capacidad suficiente: todas las metas se cumplen.
- Capacidad insuficiente: se respeta la prioridad.
- Meta vencida: no recibe asignación después del plazo.
- Capacidad cero: plan vacío con diagnóstico.
- Redondeo entero: ninguna suma mensual supera `C_t`.
- Reproducibilidad: mismos datos, mismo plan.
- Fallback sin SciPy: plan válido.
- Los endpoints no modifican ninguna tabla.
- La suite existente sigue pasando.

---

## 10. Ejemplos numéricos

### 10.1 Escasez con prioridades

Datos:

- Horizonte: 2 meses.
- Capacidad: `C = [100000, 100000]`.
- Meta A: `M=300000`, `S=0`, prioridad 5, plazo 2 meses.
- Meta B: `M=100000`, `S=0`, prioridad 1, plazo 2 meses.

El LP maximiza `5·y_A + 1·y_B`. Para completar B haría falta 100000, pero ese
dinero reduce `y_A` en `100000/300000 = 0.333`, es decir, 1.667 puntos de
objetivo, mientras B solo aporta 1. La solución óptima asigna todo a A:

| Meta | Mes 1 | Mes 2 | Total | Cumplimiento |
|---|---:|---:|---:|---:|
| A | 100000 | 100000 | 200000 | 0.667 |
| B | 0 | 0 | 0 | 0 |

Conclusión: la prioridad pesa más que el monto. El diagnóstico devuelve
`CAPACIDAD_LIMITADA`.

### 10.2 Plazo que limita la asignación

Datos:

- Horizonte: 3 meses.
- Capacidad: `C = [100000, 100000, 100000]`.
- Meta A: `M=150000`, prioridad 3, vence al final del mes 1.
- Meta B: `M=200000`, prioridad 2, vence al final del mes 3.

A solo puede recibir en el mes 1: `min(100000, 150000) = 100000`, así que agota
la capacidad del mes 1. B recibe los 100000 de los meses 2 y 3:

| Meta | Mes 1 | Mes 2 | Mes 3 | Total | Estado |
|---|---:|---:|---:|---:|---|
| A | 100000 | 0 | 0 | 100000 | parcial |
| B | 0 | 100000 | 100000 | 200000 | completada |

`restricciones_activas` incluye `capacidad_mes_1`, `capacidad_mes_2`,
`capacidad_mes_3` y `plazo_meta_1`.

### 10.3 Capacidad cero

Si `ingreso_estimado = 0`, la capacidad es 0. El plan devuelve todas las metas
en `sin_asignacion`, `total_asignado = 0` y diagnóstico `PERFIL_INCOMPLETO`.
No lanza error: la falta de datos es un estado de negocio, no una falla.

---

## 11. Pruebas implementadas

| Archivo | Qué cubre |
|---|---|
| `tests/test_finance_engine.py` | Ingreso conservador, presupuesto, colchón, prorrateo, capacidad cero y overrides. |
| `tests/test_optimization.py` | Prioridades, plazos, metas completas o vencidas, redondeo, fallback y determinismo. |
| `tests/test_api_optimization.py` | Contrato HTTP, validaciones, `/home?incluir_plan=1` y no escritura en la base. |
| `tests/test_simulador.py` | Pantalla `D14` del plan y menú del simulador. |

Comandos:

```powershell
py -3 -m unittest tests.test_finance_engine tests.test_optimization tests.test_api_optimization -v
```

---

## 12. Trabajo futuro

- EOQ adaptado para compras recurrentes.
- Reposición de efectivo y punto de reorden.
- Detección de gastos hormiga.
- Pronóstico probabilístico de gasto.
- Persistencia opcional de planes en `planes_ahorro`.
