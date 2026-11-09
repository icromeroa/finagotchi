DROP VIEW IF EXISTS v_metas_estado;
DROP VIEW IF EXISTS v_metas_progreso;
DROP VIEW IF EXISTS v_bienestar_financiero;
DROP VIEW IF EXISTS v_perfil_completitud;
DROP VIEW IF EXISTS v_estado_mascota;
DROP VIEW IF EXISTS v_progreso_etapa;
DROP VIEW IF EXISTS v_puntos_usuario;
DROP VIEW IF EXISTS v_gasto_categoria_dia;
DROP VIEW IF EXISTS v_gasto_categoria_mes;
DROP VIEW IF EXISTS v_cuentas_resumen;
DROP VIEW IF EXISTS v_balance_mensual;
DROP VIEW IF EXISTS v_balance_diario;
DROP VIEW IF EXISTS v_presupuesto_diario_actual;
DROP VIEW IF EXISTS v_papelera;
DROP VIEW IF EXISTS v_movimientos;

CREATE VIEW v_movimientos AS
SELECT t.usuario_id, t.id, t.tipo, t.monto, t.concepto, t.fecha_hora, t.fecha_local,
       t.origen, t.estado, (t.version > 1) AS editada,
       t.categoria_id, c.nombre AS categoria,
       t.cuenta_id, cu.nombre AS cuenta,
       t.meta_id, m.nombre AS meta,
       t.mensaje_id, t.confirmado_en
FROM transacciones t
JOIN cuentas cu
  ON cu.usuario_id = t.usuario_id AND cu.id = t.cuenta_id
LEFT JOIN categorias c
  ON c.usuario_id = t.usuario_id AND c.id = t.categoria_id
LEFT JOIN metas m
  ON m.usuario_id = t.usuario_id AND m.id = t.meta_id
WHERE t.is_deleted = 0;

CREATE VIEW v_papelera AS
SELECT t.usuario_id, t.id, t.tipo, t.monto, t.concepto, t.fecha_hora, t.fecha_local,
       t.categoria_id, c.nombre AS categoria,
       t.cuenta_id, cu.nombre AS cuenta,
       t.meta_id, m.nombre AS meta,
       t.deleted_at, t.eliminado_via
FROM transacciones t
JOIN cuentas cu
  ON cu.usuario_id = t.usuario_id AND cu.id = t.cuenta_id
LEFT JOIN categorias c
  ON c.usuario_id = t.usuario_id AND c.id = t.categoria_id
LEFT JOIN metas m
  ON m.usuario_id = t.usuario_id AND m.id = t.meta_id
WHERE t.is_deleted = 1;

CREATE VIEW v_presupuesto_diario_actual AS
SELECT u.id AS usuario_id,
       date('now','-5 hours') AS fecha_local,
       COALESCE((
           SELECT h.monto
           FROM presupuesto_diario_historial h
           WHERE h.usuario_id = u.id
             AND h.fecha_local <= date('now','-5 hours')
           ORDER BY h.fecha_local DESC
           LIMIT 1
       ), u.presupuesto_diario) AS monto
FROM usuarios u;

CREATE VIEW v_balance_diario AS
SELECT a.usuario_id,
       a.fecha_local,
       a.total_ingresos,
       a.total_gastos,
       a.total_ahorrado,
       a.total_ingresos - a.total_gastos AS balance_neto,
       COALESCE((
           SELECT h.monto
           FROM presupuesto_diario_historial h
           WHERE h.usuario_id = a.usuario_id
             AND h.fecha_local <= a.fecha_local
           ORDER BY h.fecha_local DESC
           LIMIT 1
       ), u.presupuesto_diario) AS presupuesto_diario,
       COALESCE((
           SELECT h.monto
           FROM presupuesto_diario_historial h
           WHERE h.usuario_id = a.usuario_id
             AND h.fecha_local <= a.fecha_local
           ORDER BY h.fecha_local DESC
           LIMIT 1
       ), u.presupuesto_diario) - a.total_gastos AS cupo_restante,
       CASE
           WHEN COALESCE((
               SELECT h.monto
               FROM presupuesto_diario_historial h
               WHERE h.usuario_id = a.usuario_id
                 AND h.fecha_local <= a.fecha_local
               ORDER BY h.fecha_local DESC
               LIMIT 1
           ), u.presupuesto_diario) = 0 THEN NULL
           ELSE CAST(100.0 * a.total_gastos / COALESCE((
               SELECT h.monto
               FROM presupuesto_diario_historial h
               WHERE h.usuario_id = a.usuario_id
                 AND h.fecha_local <= a.fecha_local
               ORDER BY h.fecha_local DESC
               LIMIT 1
           ), u.presupuesto_diario) AS INTEGER)
       END AS porcentaje_usado,
       a.num_registros
FROM (
    SELECT usuario_id, fecha_local,
           SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) AS total_ingresos,
           SUM(CASE WHEN tipo = 'gasto'   THEN monto ELSE 0 END) AS total_gastos,
           SUM(CASE WHEN tipo = 'ahorro'  THEN monto ELSE 0 END) AS total_ahorrado,
           COUNT(*) AS num_registros
    FROM transacciones
    WHERE is_deleted = 0 AND estado = 'confirmado'
    GROUP BY usuario_id, fecha_local
) a
JOIN usuarios u ON u.id = a.usuario_id;

CREATE VIEW v_balance_mensual AS
SELECT usuario_id,
       substr(fecha_local, 1, 7) AS mes,
       SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) AS total_ingresos,
       SUM(CASE WHEN tipo = 'gasto'   THEN monto ELSE 0 END) AS total_gastos,
       SUM(CASE WHEN tipo = 'ahorro'  THEN monto ELSE 0 END) AS total_ahorrado,
       SUM(CASE WHEN tipo = 'ingreso' THEN monto
                WHEN tipo = 'gasto'   THEN -monto
                ELSE 0 END) AS balance_neto,
       COUNT(*) AS num_registros
FROM transacciones
WHERE is_deleted = 0 AND estado = 'confirmado'
GROUP BY usuario_id, substr(fecha_local, 1, 7);

CREATE VIEW v_cuentas_resumen AS
SELECT cu.usuario_id,
       cu.id AS cuenta_id,
       cu.nombre,
       cu.tipo_cuenta,
       cu.oculta,
       cu.es_por_defecto,
       cu.orden,
       COUNT(t.id) AS num_movs,
       CASE WHEN cu.tipo_cuenta = 'tarjeta' THEN NULL
            ELSE cu.saldo_inicial + COALESCE(SUM(
                CASE WHEN t.tipo = 'ingreso' THEN t.monto ELSE -t.monto END
            ), 0)
       END AS saldo_actual
FROM cuentas cu
LEFT JOIN transacciones t
  ON t.usuario_id = cu.usuario_id
 AND t.cuenta_id = cu.id
 AND t.is_deleted = 0
 AND t.estado = 'confirmado'
GROUP BY cu.id, cu.usuario_id, cu.nombre, cu.tipo_cuenta, cu.oculta,
         cu.es_por_defecto, cu.orden, cu.saldo_inicial;

CREATE VIEW v_gasto_categoria_mes AS
WITH g AS (
    SELECT usuario_id,
           substr(fecha_local, 1, 7) AS mes,
           categoria_id,
           SUM(monto) AS total_gastado,
           COUNT(*) AS num_movs
    FROM transacciones
    WHERE is_deleted = 0 AND estado = 'confirmado' AND tipo = 'gasto'
    GROUP BY usuario_id, substr(fecha_local, 1, 7), categoria_id
), h AS (
    SELECT g.*,
           c.nombre AS categoria,
           c.icono,
           c.es_fija,
           (
               SELECT pc.monto_limite_mensual
               FROM presupuesto_categoria pc
               JOIN presupuestos p
                 ON p.usuario_id = pc.usuario_id AND p.id = pc.presupuesto_id
               WHERE pc.usuario_id = g.usuario_id
                 AND pc.categoria_id = g.categoria_id
                 AND p.aprobado = 1
                 AND g.mes || '-01' BETWEEN p.fecha_inicio AND p.fecha_fin
               ORDER BY p.fecha_inicio DESC
               LIMIT 1
           ) AS limite_mensual
    FROM g
    JOIN categorias c
      ON c.usuario_id = g.usuario_id AND c.id = g.categoria_id
)
SELECT h.*,
       h.limite_mensual - h.total_gastado AS restante,
       CASE WHEN h.limite_mensual IS NULL THEN NULL
            WHEN h.total_gastado > h.limite_mensual THEN 1
            ELSE 0
       END AS superado,
       CASE WHEN h.limite_mensual IS NULL OR h.limite_mensual = 0 THEN NULL
            ELSE CAST(100.0 * h.total_gastado / h.limite_mensual AS INTEGER)
       END AS porcentaje_usado
FROM h;

CREATE VIEW v_gasto_categoria_dia AS
SELECT usuario_id,
       fecha_local,
       categoria_id,
       SUM(monto) AS total_gastado,
       COUNT(*) AS num_movs
FROM transacciones
WHERE is_deleted = 0 AND estado = 'confirmado' AND tipo = 'gasto'
GROUP BY usuario_id, fecha_local, categoria_id;

CREATE VIEW v_puntos_usuario AS
SELECT p.usuario_id,
       COALESCE(SUM(p.puntos), 0) AS puntos_totales
FROM puntos_log p
LEFT JOIN transacciones t
  ON t.usuario_id = p.usuario_id AND t.id = p.transaccion_id
WHERE p.transaccion_id IS NULL
   OR (t.estado = 'confirmado' AND t.is_deleted = 0)
GROUP BY p.usuario_id;

CREATE VIEW v_progreso_etapa AS
SELECT pe.*,
       (SELECT COUNT(*)
          FROM transacciones t
         WHERE t.usuario_id = pe.usuario_id
           AND t.is_deleted = 0
           AND t.estado = 'confirmado') AS total_registros,
       (SELECT COUNT(DISTINCT t.fecha_local)
          FROM transacciones t
         WHERE t.usuario_id = pe.usuario_id
           AND t.is_deleted = 0
           AND t.estado = 'confirmado') AS dias_con_registro,
       COALESCE((
           SELECT v.puntos_totales
           FROM v_puntos_usuario v
           WHERE v.usuario_id = pe.usuario_id
       ), 0) AS puntos_totales,
       (SELECT COUNT(*)
          FROM cierres_dia c
         WHERE c.usuario_id = pe.usuario_id
           AND c.total_gastos <= c.presupuesto_diario) AS dias_perfectos,
       (SELECT COUNT(*)
          FROM cierres_dia c
         WHERE c.usuario_id = pe.usuario_id) AS dias_cerrados
FROM progreso_etapa pe;

CREATE VIEW v_estado_mascota AS
SELECT usuario_id,
       nombre,
       salud,
       CASE WHEN salud <= 20 THEN 'CRITICO'
            WHEN salud <= 50 THEN 'TRISTE'
            WHEN salud <= 80 THEN 'PREOCUPADO'
            ELSE 'FELIZ'
       END AS animo,
       CASE WHEN salud <= 20 THEN 1 ELSE 0 END AS alerta_critica,
       ultima_actualizacion
FROM estado_mascota;

CREATE VIEW v_perfil_completitud AS
SELECT usuario_id,
       SUM(CASE WHEN estado = 'completo' THEN 1 ELSE 0 END) AS secciones_completas,
       COUNT(*) AS secciones_totales,
       CAST(100.0 * SUM(CASE WHEN estado = 'completo' THEN 1 ELSE 0 END) / COUNT(*) AS INTEGER) AS porcentaje
FROM perfil_secciones
GROUP BY usuario_id;

CREATE VIEW v_bienestar_financiero AS
WITH componentes AS (
    SELECT p.usuario_id,
           CASE WHEN p.estres_financiero IS NULL THEN NULL
                ELSE (10.0 - p.estres_financiero) / 9.0 * 100.0 END AS s_estres,
           CASE WHEN p.se_siente_seguro IS NULL THEN NULL
                ELSE p.se_siente_seguro * 100.0 END AS s_seguridad,
           CASE WHEN p.dificultad_llevar_cuentas IS NULL THEN NULL
                ELSE (5.0 - p.dificultad_llevar_cuentas) / 4.0 * 100.0 END AS s_dificultad,
           CASE WHEN p.tiene_deuda_tarjeta IS NULL THEN NULL
                WHEN p.tiene_deuda_tarjeta = 0 THEN 100.0
                WHEN p.paga_a_cuotas = 1 THEN 50.0
                ELSE 0.0 END AS s_deuda,
           CASE WHEN p.tiene_fondo_emergencia IS NULL THEN NULL
                WHEN p.tiene_fondo_emergencia = 1 THEN 100.0
                ELSE 0.0 END AS s_fondo,
           CASE WHEN p.ahorro_mensual IS NULL OR p.ingreso_total_mensual IS NULL THEN NULL
                WHEN p.ingreso_total_mensual = 0 THEN NULL
                ELSE MIN(100.0, 100.0 * p.ahorro_mensual / (0.10 * p.ingreso_total_mensual)) END AS s_ahorro
    FROM perfil_financiero p
), ponderado AS (
    SELECT usuario_id,
           COALESCE(s_estres * 0.25, 0) +
           COALESCE(s_seguridad * 0.20, 0) +
           COALESCE(s_dificultad * 0.15, 0) +
           COALESCE(s_deuda * 0.15, 0) +
           COALESCE(s_fondo * 0.15, 0) +
           COALESCE(s_ahorro * 0.10, 0) AS suma,
           (CASE WHEN s_estres IS NULL THEN 0 ELSE 0.25 END) +
           (CASE WHEN s_seguridad IS NULL THEN 0 ELSE 0.20 END) +
           (CASE WHEN s_dificultad IS NULL THEN 0 ELSE 0.15 END) +
           (CASE WHEN s_deuda IS NULL THEN 0 ELSE 0.15 END) +
           (CASE WHEN s_fondo IS NULL THEN 0 ELSE 0.15 END) +
           (CASE WHEN s_ahorro IS NULL THEN 0 ELSE 0.10 END) AS pesos
    FROM componentes
)
SELECT usuario_id,
       CAST(ROUND(suma / NULLIF(pesos, 0), 0) AS INTEGER) AS puntaje,
       CAST(ROUND(pesos * 100.0, 0) AS INTEGER) AS cobertura
FROM ponderado;

CREATE VIEW v_metas_progreso AS
SELECT m.usuario_id,
       m.id AS meta_id,
       m.nombre,
       m.icono,
       m.monto_meta,
       m.fecha_limite,
       m.frecuencia_ahorro,
       m.aporte_periodico,
       m.estado,
       m.creado_en,
       COALESCE(SUM(t.monto), 0) AS ahorrado,
       m.monto_meta - COALESCE(SUM(t.monto), 0) AS faltante,
       CAST(100.0 * COALESCE(SUM(t.monto), 0) / m.monto_meta AS INTEGER) AS porcentaje
FROM metas m
LEFT JOIN transacciones t
  ON t.usuario_id = m.usuario_id
 AND t.meta_id = m.id
 AND t.tipo = 'ahorro'
 AND t.is_deleted = 0
 AND t.estado = 'confirmado'
WHERE m.is_deleted = 0
GROUP BY m.id, m.usuario_id, m.nombre, m.icono, m.monto_meta, m.fecha_limite,
         m.frecuencia_ahorro, m.aporte_periodico, m.estado, m.creado_en;

CREATE VIEW v_metas_estado AS
WITH parametros AS (
    SELECT mp.*,
           date('now', '-5 hours') AS hoy,
           date(mp.creado_en) AS inicio,
           date(mp.fecha_limite) AS limite
    FROM v_metas_progreso mp
),
periodos AS (
    SELECT p.*,
           CASE p.frecuencia_ahorro
               WHEN 'diaria' THEN MAX(0, CAST(
                   julianday(MIN(p.hoy, p.limite)) - julianday(p.inicio)
               AS INTEGER))
               WHEN 'semanal' THEN MAX(0, CAST(
                   (julianday(MIN(p.hoy, p.limite)) - julianday(p.inicio)) / 7
               AS INTEGER))
               WHEN 'quincenal' THEN MAX(0, CAST(
                   (julianday(MIN(p.hoy, p.limite)) - julianday(p.inicio)) / 15
               AS INTEGER))
               WHEN 'mensual' THEN MAX(0,
                   (CAST(strftime('%Y', MIN(p.hoy, p.limite)) AS INTEGER)
                    - CAST(strftime('%Y', p.inicio) AS INTEGER)) * 12
                   + CAST(strftime('%m', MIN(p.hoy, p.limite)) AS INTEGER)
                   - CAST(strftime('%m', p.inicio) AS INTEGER)
                   - CASE
                         WHEN CAST(strftime('%d', MIN(p.hoy, p.limite)) AS INTEGER)
                              < CAST(strftime('%d', p.inicio) AS INTEGER)
                         THEN 1 ELSE 0
                     END
               )
           END AS aportes_vencidos
    FROM parametros p
),
calculo AS (
    SELECT p.*,
           MIN(p.monto_meta, p.aportes_vencidos * p.aporte_periodico) AS esperado
    FROM periodos p
)
SELECT c.*,
       MAX(0, CAST(julianday(c.limite) - julianday(c.hoy) AS INTEGER)) AS dias_restantes,
       CASE WHEN c.estado = 'completada' OR c.ahorrado >= c.monto_meta THEN 'completada'
            WHEN c.ahorrado < c.esperado * 0.95 THEN 'atrasada'
            ELSE 'vas_bien'
       END AS estado_plan
FROM calculo c;
