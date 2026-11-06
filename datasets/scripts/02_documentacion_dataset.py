"""
Etapa 2 del procesamiento: Documentación.

Lee el dataset limpio generado por el script de limpieza y produce los
archivos de consulta: diccionario de datos, reporte ejecutivo, guía de
machine learning y un archivo JSON con las columnas excluidas.

Ejecución:
    python datasets/scripts/02_documentacion_dataset.py
"""

import json
import re
from pathlib import Path

import pandas as pd

CARPETA_BASE = Path(__file__).resolve().parent.parent
CARPETA_DATOS = CARPETA_BASE / "dataset_500"
CARPETA_DOC = CARPETA_DATOS / "documentacion"
CARPETA_DOC.mkdir(parents=True, exist_ok=True)

ARCHIVO_ENTRADA = CARPETA_DATOS / "finagotchi_dataset_6_outliers.csv"

# Columnas que no pueden usarse para predecir porque son identificadores
# o contienen texto libre.
COLS_ID_TEXTO = [
    "transaccion_id", "usuario_id", "message_id", "device_uid",
    "cuenta_id", "categoria_id", "meta_id",
    "texto_transcrito", "concepto", "inconsistencias",
    "posible_duplicado_negocio", "message_id_duplicado",
]

# Columnas que se calculan después de que la transacción ocurre. Usarlas
# como predictores causaría fuga de información (data leakage).
COLS_LEAKAGE = [
    "estado", "confirmado_en", "is_deleted", "eliminado_via",
    "puntos_tx", "salud_delta_tx", "n_alertas_tx", "n_notif_dispositivo_tx",
    "monto_cambio", "monto_original", "dia_salud_fin", "dia_delta_salud",
    "dia_version_cierre", "usuario_total_registros", "usuario_dias_con_registro",
    "usuario_puntos_totales", "usuario_dias_perfectos", "usuario_dias_cerrados",
    "usuario_racha_actual", "usuario_mejor_racha", "cat_mes_total_gastado",
    "cat_mes_superado", "cat_mes_porcentaje_usado",
]

TARGETS_POSIBLES = [
    ("categoria", "clasificacion", "Categoría de la transacción"),
    ("mascota_animo_actual", "clasificacion", "Ánimo de la mascota (4 clases)"),
    ("mascota_salud_actual", "regresion", "Salud de la mascota (0-100)"),
    ("salud_delta_tx", "regresion", "Cambio de salud por transacción"),
]


def inferir_rol(col: str, s: pd.Series) -> str:
    """Determina el rol lógico de una columna basándose en su nombre y tipo."""
    c = col.lower()
    if re.search(r"(_id|_uid|_uuid)$|^id$", c): return "id"
    if pd.api.types.is_datetime64_any_dtype(s): return "timestamp"
    if re.search(r"(_en|_at|_on|fecha|hora|_time|_date)$", c): return "timestamp"
    if re.search(r"(texto|transcrip|concepto|descrip|mensaje|observ)", c): return "texto"
    if c in [t[0] for t in TARGETS_POSIBLES]: return "target_candidato"
    if c in COLS_LEAKAGE: return "leakage"
    if re.search(r"^(is_|has_|tiene_|es_|flag_)", c): return "binario"
    if pd.api.types.is_bool_dtype(s): return "binario"
    if pd.api.types.is_numeric_dtype(s):
        valores = set(s.dropna().unique())
        if s.nunique() <= 2 and valores.issubset({0, 1}): return "binario"
        if re.search(r"(_total|_sum|_avg|^dia_|^cat_mes_|^usuario_|_delta)", c): return "agregado"
        return "numerico"
    if s.nunique() > max(50, len(s) * 0.5): return "texto"
    return "categorico"


def _tipo_logico(s: pd.Series) -> str:
    """Define el tipo de dato para el diccionario."""
    if pd.api.types.is_datetime64_any_dtype(s): return "fecha/hora"
    if pd.api.types.is_bool_dtype(s): return "booleano"
    if pd.api.types.is_integer_dtype(s): return "binario" if s.nunique(dropna=True) <= 2 else "entero"
    if pd.api.types.is_float_dtype(s): return "decimal"
    return "categórico"


def generar_diccionario(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for col in df.columns:
        s = df[col]
        filas.append({
            "columna": col, "tipo_pandas": str(s.dtype), "tipo_logico": _tipo_logico(s),
            "rol_sugerido": inferir_rol(col, s), "nulos": int(s.isna().sum()),
            "pct_nulos": round(float(s.isna().mean() * 100), 2),
            "valores_unicos": int(s.nunique(dropna=True)),
            "ejemplo": (s.dropna().iloc[0] if s.notna().any() else None),
        })
    dic = pd.DataFrame(filas).sort_values(["rol_sugerido", "columna"])
    dic.to_csv(CARPETA_DOC / "diccionario_datos.csv", index=False)
    print(f"   diccionario_datos.csv -> {len(dic)} columnas")
    return dic


def generar_guia_ml(df: pd.DataFrame) -> None:
    flags = [c for c in df.columns if c.startswith("flag_") or c.startswith("es_outlier_")]
    lineas = [
        "# Guía para Machine Learning — FinaGotchi\n",
        f"Dataset base: `finagotchi_dataset_6_outliers.csv` ({df.shape[0]} filas, {df.shape[1]} columnas).\n",
        "\n## Posibles variables objetivo\n",
    ]
    for nombre, tipo, desc in TARGETS_POSIBLES:
        lineas.append(f"- `{nombre}` ({tipo}): {desc}")
    
    lineas += ["\n## Columnas que no se usan como features\n", "\n### Identificadores y texto libre\n"]
    for c in COLS_ID_TEXTO: lineas.append(f"- `{c}`")
    
    lineas.append("\n### Post-evento (leakage temporal)\n")
    for c in COLS_LEAKAGE: lineas.append(f"- `{c}`")
    
    lineas.append("\n### Banderas de diagnóstico\n")
    for c in flags: lineas.append(f"- `{c}`")
    
    lineas += [
        "\n## Reglas para el entrenamiento\n",
        "1. Dividir train y test por `fecha_hora`, no de forma aleatoria.",
        "2. Los encoders y escaladores van dentro de un `Pipeline` ajustado solo con train.",
        "3. Para predecir `monto` no se usa `texto_transcrito` porque el monto está escrito en el texto.",
        "4. Filtrar `es_outlier_monto == 1` si el modelo es sensible a extremos.",
        "5. Los agregados `dia_*` y `cat_mes_*` incluyen la fila actual; si se usan como feature deben recalcularse con `shift`.",
    ]
    (CARPETA_DOC / "features_ml.md").write_text("\n".join(lineas), encoding="utf-8")
    print("   features_ml.md escrito")


def exportar_listas_excluidas(df: pd.DataFrame) -> None:
    flags = [c for c in df.columns if c.startswith("flag_") or c.startswith("es_outlier_")]
    datos = {"id_texto": COLS_ID_TEXTO, "leakage": COLS_LEAKAGE, "flags": flags}
    (CARPETA_DOC / "columnas_excluidas.json").write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print("   columnas_excluidas.json escrito")


def generar_reporte_calidad(df: pd.DataFrame, dic: pd.DataFrame) -> None:
    total = len(df)
    validas = int(df["es_valida_para_calculo"].sum())
    eliminadas = int(df["is_deleted"].sum())
    pendientes = int((df["estado"] == "pendiente").sum())
    con_incons = int((df["n_inconsistencias"] > 0).sum())
    outliers = int(df["es_outlier_monto"].sum())
    
    lineas = [
        "# Reporte de calidad — FinaGotchi\n",
        f"- Filas totales: {total}", f"- Columnas: {df.shape[1]}",
        f"- Transacciones válidas: {validas} ({validas / total:.1%})",
        f"- Transacciones eliminadas: {eliminadas}",
        f"- Transacciones pendientes: {pendientes}",
        f"- Filas con inconsistencias: {con_incons} ({con_incons / total:.1%})",
        f"- Outliers marcados en monto: {outliers}",
        "\n## Columnas por rol sugerido",
    ]
    for rol, n in dic["rol_sugerido"].value_counts().items():
        lineas.append(f"- `{rol}`: {n} columnas")
        
    lineas += [
        "\n## Archivos generados", "- `log_limpieza.txt`: registro del proceso",
        "- `reglas_nulos.csv`: justificación de cada nulo", "- `reporte_inconsistencias.csv`: conteo por regla",
        "- `diccionario_datos.csv`: tipo y rol de cada columna", "- `features_ml.md`: guía para el ingeniero",
        "- `columnas_excluidas.json`: listas para el script 03",
    ]
    (CARPETA_DOC / "reporte_calidad.md").write_text("\n".join(lineas), encoding="utf-8")
    print("   reporte_calidad.md escrito")


if __name__ == "__main__":
    print("=" * 70)
    print("DOCUMENTACIÓN DEL DATASET - FinaGotchi")
    print("=" * 70)
    
    if not ARCHIVO_ENTRADA.exists():
        raise FileNotFoundError(f"Ejecuta primero limpieza_datos_1.py. Falta: {ARCHIVO_ENTRADA}")

    df = pd.read_csv(ARCHIVO_ENTRADA, low_memory=False)
    dic = generar_diccionario(df)
    generar_guia_ml(df)
    exportar_listas_excluidas(df)
    generar_reporte_calidad(df, dic)