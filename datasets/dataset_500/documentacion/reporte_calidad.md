# Reporte de calidad — FinaGotchi

- Filas totales: 500
- Columnas: 208
- Transacciones válidas: 478 (95.6%)
- Transacciones eliminadas: 14
- Transacciones pendientes: 8
- Filas con inconsistencias: 48 (9.6%)
- Outliers marcados en monto: 56

## Columnas por rol sugerido
- `binario`: 63 columnas
- `numerico`: 47 columnas
- `categorico`: 34 columnas
- `leakage`: 21 columnas
- `agregado`: 18 columnas
- `id`: 7 columnas
- `texto`: 7 columnas
- `timestamp`: 7 columnas
- `target_candidato`: 4 columnas

## Archivos generados
- `log_limpieza.txt`: registro del proceso
- `reglas_nulos.csv`: justificación de cada nulo
- `reporte_inconsistencias.csv`: conteo por regla
- `diccionario_datos.csv`: tipo y rol de cada columna
- `features_ml.md`: guía para el ingeniero
- `columnas_excluidas.json`: listas para el script 03