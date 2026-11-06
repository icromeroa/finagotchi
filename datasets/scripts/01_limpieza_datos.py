"""
Etapa 1 del procesamiento: Limpieza y transformación de datos.

Este script toma el archivo original, aplica las reglas de calidad en el
orden establecido y guarda un archivo por cada etapa. El objetivo es que
cualquier persona pueda auditar qué se hizo en cada paso. No entrena
modelos ni genera la documentación final, eso se hace en scripts posteriores.

Ejecución:
    python datasets/scripts/limpieza_datos_1.py
"""

import logging
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Configuración de rutas y variables globales
# ----------------------------------------------------------------------------
# __file__ apunta al script actual. parent es la carpeta 'scripts', y
# parent.parent es la carpeta 'datasets'. A partir de ahí se arma la ruta.
CARPETA_BASE = Path(__file__).resolve().parent.parent
CARPETA_DATOS = CARPETA_BASE / "dataset_500"
CARPETA_DOC = CARPETA_DATOS / "documentacion"

# El código crea las carpetas si no existen para evitar errores al guardar.
CARPETA_DOC.mkdir(parents=True, exist_ok=True)

ARCHIVO_ORIGINAL = CARPETA_DATOS / "finagotchi_dataset_completo.csv"

COLS_FECHA_HORA = [
    "fecha_hora", "confirmado_en", "tx_creado_en", "tx_actualizado_en",
    "usuario_creado_en", "usuario_ultimo_acceso",
    "dev_vinculado_en", "dev_ultima_conexion",
]
COLS_FECHA = ["fecha_local", "meta_fecha_limite"]

COLS_CATEGORICAS = [
    "categoria", "categoria_original", "cuenta", "localidad",
    "dev_modelo", "mascota_animo_actual",
]

log = logging.getLogger("limpieza")


def configurar_log() -> None:
    """Registra todo el proceso tanto en consola como en un archivo de texto."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(CARPETA_DOC / "log_limpieza.txt", mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def guardar(df: pd.DataFrame, nombre: str, descripcion: str) -> None:
    """Guarda un DataFrame en formato CSV y deja constancia en el log."""
    ruta = CARPETA_DATOS / nombre
    df.to_csv(ruta, index=False)
    log.info(f"   Guardado: {ruta.name}  {df.shape}  ({descripcion})")


# ----------------------------------------------------------------------------
# Etapas del procesamiento
# ----------------------------------------------------------------------------
def cargar_datos() -> pd.DataFrame:
    """Carga el CSV original y muestra un resumen inicial de su estado."""
    log.info("--- ETAPA 0: CARGA DE DATOS ---")
    if not ARCHIVO_ORIGINAL.exists():
        raise FileNotFoundError(f"No se encontró el dataset original en: {ARCHIVO_ORIGINAL}")
    
    df = pd.read_csv(ARCHIVO_ORIGINAL, low_memory=False)
    log.info(f"   Dimensiones: {df.shape}")
    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0]
    log.info(f"   Columnas con nulos: {len(nulos)} | nulos totales: {int(nulos.sum())}")
    return df


def corregir_tipos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte las columnas de fecha a tipo datetime y las columnas numéricas
    que representan enteros (como IDs o banderas) a Int64. Se usa Int64 en
    lugar de int normal para que admita valores nulos sin romperse.
    """
    log.info("\n--- ETAPA 1: CORRECCIÓN DE TIPOS ---")
    df = df.copy()

    for col in COLS_FECHA_HORA:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    for col in COLS_FECHA:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    convertidas = []
    for col in df.select_dtypes(include="float").columns:
        s = df[col].dropna()
        s = s[np.isfinite(s)]
        if len(s) and (s % 1 == 0).all():
            df[col] = df[col].astype("Int64")
            convertidas.append(col)

    log.info(f"   Fechas/horas -> datetime: {len(COLS_FECHA_HORA) + len(COLS_FECHA)} columnas")
    log.info(f"   float -> Int64 (eran enteros): {len(convertidas)} columnas")
    guardar(df, "finagotchi_dataset_1_tipos_corregidos.csv", "tipos corregidos")
    return df


def tratar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evalúa si cada nulo del dataset tiene una justificación lógica.
    Por ejemplo, un gasto registrado manualmente no tiene audio, por lo
    que sus campos de IA deben ser nulos. En lugar de inventar datos
    (imputar), se dejan los nulos y se crean banderas que indiquen por
    qué están vacíos.
    """
    log.info("\n--- ETAPA 2: TRATAMIENTO DE NULOS ---")
    df = df.copy()

    valida = (df["estado"] == "confirmado") & (df["is_deleted"] == 0)
    hay_cierre = valida.groupby([df["usuario_id"], df["fecha_local"]]).transform("any")

    reglas = [
        (["eliminado_via"], df["is_deleted"] == 0, "La transacción no fue anulada"),
        (["message_id", "texto_transcrito", "confianza_ia", "secuencia",
          "duracion_audio_s", "msg_estado", "msg_latencia_total_s",
          "ia_stt_latencia_ms", "ia_extraccion_latencia_ms", "ia_stt_confianza",
          "ia_tokens_entrada", "ia_tokens_salida", "ia_modelo_extraccion",
          "menciona_cuenta_en_texto"], df["origen"] == "manual", "Registro manual: sin audio ni IA"),
        (["bateria_en_evento", "boton_en_evento"], df["origen"] != "dispositivo", "Registro no vino del dispositivo físico"),
        (["confirmado_en"], df["estado"] == "pendiente", "Transacción pendiente: no confirmada"),
        (["categoria_id", "categoria", "categoria_es_fija", "categoria_es_propia"], df["tipo"] == "ahorro", "El ahorro no lleva categoría"),
        (["categoria_original", "monto_original"], df["editada"] == 0, "La transacción nunca fue editada"),
        (["meta_id", "meta_nombre", "meta_monto", "meta_fecha_limite",
          "meta_frecuencia", "meta_aporte_periodico", "meta_estado",
          "meta_ahorrado", "meta_porcentaje", "meta_estado_plan"], df["tipo"] != "ahorro", "Solo los ahorros tienen meta"),
        (["coincide_palabra_clave_categoria"], (df["tipo"] == "ahorro") | (df["origen"] == "manual"), "Sin texto para comparar"),
        (["cat_mes_total_gastado"], (df["tipo"] != "gasto") | ~valida, "Solo para gastos válidos"),
        (["cat_mes_limite", "cat_mes_superado", "cat_mes_porcentaje_usado"], pd.Series(True, index=df.index), "Categoría sin tope asignado"),
        ([c for c in df.columns if c.startswith("dia_") and c not in ("dia_semana", "dia_del_mes")], ~hay_cierre, "El día no tiene transacciones válidas"),
        (["solicitud_eliminacion_estado"], df["usuario_estado"] == "activo", "El usuario no solicitó eliminación"),
        (["presupuesto_meses"], df["presupuesto_aprobado"] == 0, "Sin presupuesto aprobado"),
    ]

    filas_reporte, inexplicados = [], 0
    for cols, esperado, motivo in reglas:
        for col in cols:
            nulos = df[col].isna()
            fuera = int((nulos & ~esperado).sum())
            inexplicados += fuera
            filas_reporte.append({
                "columna": col, "nulos": int(nulos.sum()),
                "nulos_sin_explicacion": fuera, "motivo": motivo})

    pd.DataFrame(filas_reporte).to_csv(CARPETA_DOC / "reglas_nulos.csv", index=False)

    cubiertas = set([r["columna"] for r in filas_reporte])
    sin_regla = [c for c in df.columns[df.isna().any()] if c not in cubiertas]
    log.info(f"   Columnas con nulos cubiertas por una regla: {len(cubiertas)}")
    log.info(f"   Nulos sin explicación (datos perdidos): {inexplicados}")
    if sin_regla:
        log.warning(f"   Columnas con nulos sin regla: {sin_regla}")

    # Banderas que explicitan los casos donde el nulo significa "no aplica".
    df["tiene_mensaje_ia"] = df["message_id"].notna().astype(int)
    df["tiene_meta"] = df["meta_id"].notna().astype(int)
    df["tiene_limite_categoria"] = df["cat_mes_limite"].notna().astype(int)
    df["tiene_cierre_dia"] = hay_cierre.astype(int)
    df["es_valida_para_calculo"] = valida.astype(int)

    # Solo se rellenan las variables categóricas para evitar problemas
    # con los algoritmos de machine learning.
    etiquetas = {
        "eliminado_via": "no_anulada", "categoria": "sin_categoria",
        "categoria_original": "sin_cambio", "meta_nombre": "sin_meta",
        "meta_frecuencia": "sin_meta", "meta_estado": "sin_meta",
        "meta_estado_plan": "sin_meta", "msg_estado": "sin_mensaje",
        "ia_modelo_extraccion": "sin_ia", "dia_calificacion": "sin_cierre",
        "solicitud_eliminacion_estado": "sin_solicitud",
    }
    for col, etiqueta in etiquetas.items():
        df[col] = df[col].astype("object").fillna(etiqueta)

    log.info(f"   Categóricas rellenadas con etiqueta: {len(etiquetas)}")
    log.info(f"   Nulos que se conservan en numéricos/texto: {int(df.isna().sum().sum())}")
    guardar(df, "finagotchi_dataset_2_nulos_tratados.csv", "nulos tratados")
    return df


def _normalizar_categorica(valor):
    """Convierte a minúsculas, quita tildes y reemplaza espacios por guiones bajos."""
    if pd.isna(valor):
        return valor
    s = unicodedata.normalize("NFD", str(valor))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s.replace(" ", "_")


def normalizar_texto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia espacios y saltos de línea en las columnas de texto. A las
    categóricas se les aplica un formato estandarizado. No se altera
    el contenido de las transcripciones ni de las fechas.
    """
    log.info("\n--- ETAPA 3: NORMALIZACIÓN DE TEXTO ---")
    df = df.copy()

    cols_texto = df.select_dtypes(include=["object", "string"]).columns
    for col in cols_texto:
        mascara = df[col].notna()
        df.loc[mascara, col] = (df.loc[mascara, col].astype(str)
                                .str.replace(r"[\r\n\t]", " ", regex=True)
                                .str.replace(r"\s+", " ", regex=True).str.strip())

    for col in COLS_CATEGORICAS:
        df[col] = df[col].map(_normalizar_categorica)

    log.info(f"   Espacios limpiados en {len(cols_texto)} columnas de texto")
    log.info(f"   Categóricas normalizadas: {len(COLS_CATEGORICAS)}")
    guardar(df, "finagotchi_dataset_3_texto_normalizado.csv", "texto normalizado")
    return df


def eliminar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina duplicados usando el ID de la transacción, conservando la
    versión más reciente. Las transacciones que parecen duplicadas por
    reglas de negocio (mismo monto, mismo día) no se borran; solo se
    marcan para que el analista decida.
    """
    log.info("\n--- ETAPA 4: DUPLICADOS ---")
    n0 = len(df)

    clave_negocio = ["usuario_id", "fecha_hora", "monto", "concepto", "tipo"]
    n_exactos = int(df.duplicated().sum())
    n_pk = int(df.duplicated(subset=["transaccion_id"]).sum())
    n_neg = int(df.duplicated(subset=clave_negocio).sum())
    con_msg = df[df["message_id"].notna()]
    n_msg = int(con_msg.duplicated(subset=["usuario_id", "message_id"]).sum())

    log.info(f"   Filas completamente idénticas: {n_exactos}")
    log.info(f"   Duplicados por transaccion_id (PK): {n_pk}")
    log.info(f"   Duplicados por clave de negocio: {n_neg}")
    log.info(f"   message_id repetido por usuario: {n_msg}")

    df = (df.sort_values("tx_actualizado_en")
            .drop_duplicates(subset=["transaccion_id"], keep="last")
            .sort_values("transaccion_id").reset_index(drop=True))

    df["posible_duplicado_negocio"] = df.duplicated(subset=clave_negocio, keep=False).astype(int)
    df["message_id_duplicado"] = 0
    if n_msg > 0:
        idx_dup = con_msg[con_msg.duplicated(subset=["usuario_id", "message_id"], keep=False)].index
        df.loc[idx_dup, "message_id_duplicado"] = 1

    log.info(f"   Filas: {n0} -> {len(df)}  (eliminadas: {n0 - len(df)})")
    log.info(f"   Posibles duplicados de negocio marcados: {int(df['posible_duplicado_negocio'].sum())}")
    guardar(df, "finagotchi_dataset_4_sin_duplicados.csv", "sin duplicados")
    return df


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _monto_en_texto(texto) -> float:
    """
    Busca un monto dentro de una transcripción. Reconoce números como
    '15 mil', '1.5 millones', '14.000' o '8500'.
    """
    if pd.isna(texto):
        return np.nan
    t = _sin_tildes(str(texto).lower()).replace("$", " ")

    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(millones|millon|mil|k)\b", t)
    if m:
        x = float(m.group(1).replace(",", "."))
        mult = 1_000_000 if m.group(2).startswith("mill") else 1_000
        return x * mult

    m = re.search(r"\d{1,3}(?:[.,]\d{3})+", t)
    if m:
        return float(re.sub(r"[.,]", "", m.group(0)))

    m = re.search(r"\d+(?:[.,]\d+)?", t)
    if m:
        return float(m.group(0).replace(",", "."))
    return np.nan


def validar_consistencia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica reglas lógicas para detectar errores en los datos. Las filas
    que incumplen una regla se marcan con una bandera y se conservan.
    """
    log.info("\n--- ETAPA 5: CONSISTENCIA ---")
    df = df.copy()

    local = df["fecha_hora"].dt.tz_convert("America/Bogota")
    animo_esperado = pd.cut(df["mascota_salud_actual"], [-1, 20, 50, 80, 100],
                            labels=["critico", "triste", "preocupado", "feliz"]).astype(str)
    animo_ok = (df["mascota_salud_actual"].notna() & df["mascota_animo_actual"].notna()
                & (df["mascota_animo_actual"].astype(str) != "nan"))

    # El texto dictado normalmente coincide con el monto final, no con el monto
    # original (el cual suele ser un error de digitación que el usuario corrigió).
    monto_texto = df["texto_transcrito"].map(_monto_en_texto)
    monto_ref = df["monto"].astype("float")
    compara_monto = monto_texto.notna() & monto_ref.notna() & (monto_ref > 0)
    difiere_monto = compara_monto & ~np.isclose(monto_texto, monto_ref, rtol=1e-3, atol=1)

    n_tipos_por_cat = df[df["categoria"] != "sin_categoria"].groupby("categoria")["tipo"].nunique()
    cats_mixtas = n_tipos_por_cat[n_tipos_por_cat > 1].index

    reglas = [
        ("pk_duplicada", df["transaccion_id"].duplicated(keep=False), "alta", "ID repetido"),
        ("fecha_local_no_coincide", local.dt.strftime("%Y-%m-%d") != df["fecha_local"].dt.strftime("%Y-%m-%d"), "alta", "fecha_local distinta a UTC"),
        ("hora_local_no_coincide", local.dt.hour != df["hora_local"], "alta", "hora_local distinta a UTC"),
        ("confirmado_antes_de_crear", df["confirmado_en"].notna() & df["tx_creado_en"].notna() & (df["confirmado_en"] < df["tx_creado_en"]), "alta", "Confirmación previa a creación"),
        ("tx_antes_del_alta_usuario", df["fecha_hora"].notna() & df["usuario_creado_en"].notna() & (df["fecha_hora"] < df["usuario_creado_en"]), "media", "Transacción previa al usuario"),
        ("ultimo_acceso_antes_del_alta", df["usuario_ultimo_acceso"].notna() & df["usuario_creado_en"].notna() & (df["usuario_ultimo_acceso"] < df["usuario_creado_en"]), "media", "Acceso previo al alta"),
        ("monto_no_positivo", df["monto"] <= 0, "alta", "Monto menor o igual a cero"),
        ("duracion_fuera_de_rango", df["duracion_audio_s"].notna() & ((df["duracion_audio_s"] < 0.5) | (df["duracion_audio_s"] > 40)), "alta", "Audio fuera de [0.5, 40] s"),
        ("ia_stt_confianza_fuera_de_rango", df["ia_stt_confianza"].notna() & ((df["ia_stt_confianza"] < 0) | (df["ia_stt_confianza"] > 1)), "alta", "Confianza STT fuera de [0, 1]"),
        ("confianza_ia_fuera_de_rango", df["confianza_ia"].notna() & ((df["confianza_ia"] < 0) | (df["confianza_ia"] > 1)), "alta", "Confianza IA fuera de [0, 1]"),
        ("bateria_fuera_de_rango", df["bateria_en_evento"].notna() & ((df["bateria_en_evento"] < 0) | (df["bateria_en_evento"] > 100)), "alta", "Batería fuera de [0, 100]"),
        ("edad_fuera_de_rango", df["edad"].notna() & ((df["edad"] < 14) | (df["edad"] > 100)), "alta", "Edad fuera de [14, 100]"),
        ("bienestar_fuera_de_rango", df["bienestar_puntaje"].notna() & ((df["bienestar_puntaje"] < 0) | (df["bienestar_puntaje"] > 100)), "media", "Bienestar fuera de [0, 100]"),
        ("puntos_en_anulada", (df["is_deleted"] == 1) & (df["puntos_tx"] > 0), "media", "Anulada con puntos"),
        ("puntos_en_pendiente", (df["estado"] == "pendiente") & (df["puntos_tx"] > 0), "alta", "Pendiente con puntos"),
        ("puntos_mayor_a_1", df["puntos_tx"] > 1, "baja", "Más de 1 punto por transacción"),
        ("animo_no_coincide_con_salud", animo_ok & (df["mascota_animo_actual"].astype(str) != animo_esperado), "alta", "Ánimo no coincide con salud"),
        ("ingreso_total_no_suma", (df["ingreso_trabajo_mensual"] + df["apoyo_familiar_mensual"] + df["beca_mensual"] + df["otros_ingresos_mensual"] != df["ingreso_total_mensual"]), "alta", "Total no cuadra con componentes"),
        ("categoria_mezcla_tipos", df["categoria"].isin(cats_mixtas), "alta", "Categoría en ingresos y gastos a la vez"),
        ("ahorro_sin_meta_o_meta_en_otro_tipo", ((df["tipo"] == "ahorro") & (df["tiene_meta"] == 0)) | ((df["tipo"] != "ahorro") & (df["tiene_meta"] == 1)), "media", "Meta mal asignada"),
        ("texto_no_coincide_con_monto", difiere_monto, "media", "El audio dice un monto distinto"),
    ]

    df["inconsistencias"] = ""
    resumen = []
    for nombre, mascara, severidad, comentario in reglas:
        mascara = mascara.fillna(False).astype(bool)
        df.loc[mascara, "inconsistencias"] += nombre + ";"
        df[f"flag_{nombre}"] = mascara.astype(int)
        resumen.append({"regla": nombre, "filas_afectadas": int(mascara.sum()), "severidad": severidad, "descripcion": comentario})
        log.info(f"   [{severidad:5}] {nombre:42} -> {int(mascara.sum()):4} filas")

    df["inconsistencias"] = df["inconsistencias"].str.rstrip(";")
    df["n_inconsistencias"] = (df["inconsistencias"].str.count(";").astype("Int64") + (df["inconsistencias"] != "").astype("Int64")).astype("Int64")

    nombres_dia = {0: "domingo", 1: "lunes", 2: "martes", 3: "miercoles", 4: "jueves", 5: "viernes", 6: "sabado"}
    df["dia_semana_nombre"] = df["dia_semana"].map(nombres_dia)

    pd.DataFrame(resumen).to_csv(CARPETA_DOC / "reporte_inconsistencias.csv", index=False)
    log.info(f"   Filas con al menos una inconsistencia: {int((df['n_inconsistencias'] > 0).sum())}")
    guardar(df, "finagotchi_dataset_5_consistencia.csv", "con banderas de consistencia")
    return df


def detectar_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Marca los valores atípicos en montos y tiempos usando el rango
    intercuartílico. No elimina nada, solo deja la marca para que los
    modelos puedan decidir si usarlos o no.
    """
    log.info("\n--- ETAPA 6: DETECCIÓN DE OUTLIERS ---")
    df = df.copy()
    df["es_outlier_monto"] = 0
    df["es_outlier_duracion_audio"] = 0

    for tipo, grupo in df.groupby("tipo"):
        m = grupo["monto"].dropna()
        if len(m) >= 4:
            q1, q3 = m.quantile([0.25, 0.75])
            iqr = q3 - q1
            li, ls = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            idx = grupo.index[(grupo["monto"] < li) | (grupo["monto"] > ls)]
            df.loc[idx, "es_outlier_monto"] = 1
            log.info(f"   Monto {tipo:8}: IQR=[{li:.0f}, {ls:.0f}] -> {len(idx)} outliers")

    d = df["duracion_audio_s"].dropna()
    if len(d) >= 4:
        q1, q3 = d.quantile([0.25, 0.75])
        iqr = q3 - q1
        li, ls = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df["duracion_audio_s"].notna() & ((df["duracion_audio_s"] < li) | (df["duracion_audio_s"] > ls)))
        df.loc[mask, "es_outlier_duracion_audio"] = 1
        log.info(f"   Duración audio: IQR=[{li:.2f}, {ls:.2f}] -> {int(mask.sum())} outliers")

    guardar(df, "finagotchi_dataset_6_outliers.csv", "con outliers marcados")
    return df


if __name__ == "__main__":
    configurar_log()
    log.info("=" * 70)
    log.info("LIMPIEZA DE DATOS - FinaGotchi")
    log.info("=" * 70)

    df = cargar_datos()
    df = corregir_tipos(df)
    df = tratar_nulos(df)
    df = normalizar_texto(df)
    df = eliminar_duplicados(df)
    df = validar_consistencia(df)
    df = detectar_outliers(df)

    log.info("\nLimpieza completada exitosamente.")