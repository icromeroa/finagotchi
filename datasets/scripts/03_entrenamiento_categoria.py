"""
Etapa 3 del procesamiento: Entrenamiento de Machine Learning.

ENTRENA un modelo supervisado para predecir la categoría de un gasto.

CONCEPTOS CLAVE DE ESTE SCRIPT:
- TARGET (y): Es la columna que queremos predecir. En este caso, "categoria".
- FEATURES (X): Son las columnas (pistas) que el modelo usará para adivinar el TARGET.
  Ejemplo: monto, cuenta, tipo, hora, etc.
- DATA LEAKAGE: Es cuando le pasamos al modelo información que en la vida real no tendría
  en el momento de predecir (ej: el ID de la transacción, o la categoría misma).
  Por eso excluimos columnas.

Ejecución:
    python datasets/scripts/03_entrenamiento_categoria.py
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# --- CONFIGURACIÓN DE RUTAS ---
# Path(__file__).resolve().parent.parent sube dos niveles desde la ubicación de este script.
# Como el script está en datasets/scripts/, subir dos niveles nos deja en la raíz finagotchi.
CARPETA_BASE = Path(__file__).resolve().parent.parent
CARPETA_DATOS = CARPETA_BASE / "dataset_500"
CARPETA_DOC = CARPETA_DATOS / "documentacion"
CARPETA_ML = CARPETA_DATOS / "ml"

# Creamos la carpeta 'ml' si no existe para guardar los resultados del modelo.
CARPETA_ML.mkdir(parents=True, exist_ok=True)

# Archivos de entrada
ARCHIVO_ENTRADA = CARPETA_DATOS / "finagotchi_dataset_6_outliers.csv"
ARCHIVO_EXCLUIDAS = CARPETA_DOC / "columnas_excluidas.json"

# --- DEFINICIÓN DEL TARGET Y PARÁMETROS ---
# ¡AQUÍ ESTÁ EL TARGET! Es la variable objetivo que el modelo intentará predecir.
TARGET = "categoria"

# Parámetros de control del entrenamiento
MIN_MUESTRAS_POR_CLASE = 5  # Si una categoría tiene menos de 5 datos, se agrupa en "otras" para evitar errores.
FRACCION_TEST = 0.2         # Usaremos el 20% de los datos más recientes para probar el modelo.
SEMILLA = 42                # Semilla para que los resultados aleatorios sean reproducibles.

def cargar_listas_excluidas() -> list[str]:
    """
    Carga las columnas que NO deben usarse como features (X).
    
    ¿POR QUÉ EXCLUIMOS?
    - 'id_texto': IDs únicos (ej. transaccion_id). No aportan patrones, solo ruido.
    - 'leakage': Columnas que contienen información del futuro o de la respuesta.
    - 'flags': Columnas técnicas del sistema que no definen el gasto del usuario.
    """
    if ARCHIVO_EXCLUIDAS.exists():
        datos = json.loads(ARCHIVO_EXCLUIDAS.read_text(encoding="utf-8"))
        return datos["id_texto"] + datos["leakage"] + datos["flags"]
    # Fallback de seguridad en caso de que el archivo JSON no exista.
    return ["transaccion_id", "usuario_id", "message_id", "device_uid", "texto_transcrito", "estado", "is_deleted"]


def preparar_datos() -> tuple[pd.DataFrame, list[str]]:
    """
    Filtra las transacciones válidas y define cuáles serán nuestras X (features).
    """
    df = pd.read_csv(ARCHIVO_ENTRADA, low_memory=False)
    
    # 1. FILTRADO: Solo predecimos sobre transacciones válidas que tengan categoría asignada.
    df = df[(df["es_valida_para_calculo"] == 1) & (df[TARGET] != "sin_categoria")].copy()
    
    # 2. MANEJO DE CLASES RARAS: Si una categoría aparece muy poco (ej. "mascotas"), 
    # el modelo no podrá aprender. Las agrupamos en "otras" y luego las sacamos.
    frecuencia = df[TARGET].value_counts()
    clases_raras = frecuencia[frecuencia < MIN_MUESTRAS_POR_CLASE].index
    df.loc[df[TARGET].isin(clases_raras), TARGET] = "otras"
    df = df[df[TARGET] != "otras"].copy()

    # 3. DEFINICIÓN DE FEATURES (X): 
    # Creamos una lista con todas las columnas, MENOS las excluidas y MENOS el TARGET.
    # ¡AQUÍ SE DEFINEN LAS FEATURES QUE USARÁ EL MODELO!
    excluir = set(cargar_listas_excluidas()) | {TARGET}
    excluir = [c for c in excluir if c in df.columns] # Nos aseguramos que existan en el df

    # 4. ORDEN TEMPORAL: Es crucial ordenar por fecha. 
    # Un modelo de ML no debe "entrenar con el futuro para predecir el pasado".
    df = df.sort_values("fecha_hora").reset_index(drop=True)
    
    # Lista blanca: Solo usaremos estas columnas para entrenar
    columnas_relevantes = [
        "monto", "cuenta", "tipo", "hora_local", "dia_semana_nombre", 
        "es_fin_de_semana", "tiene_mensaje_ia", "coincide_palabra_clave_categoria"
    ]
    
    # Filtramos solo las que existan en el dataframe
    features = [c for c in columnas_relevantes if c in df.columns]
    
    return df, features


def dividir_temporal(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separa los datos: 80% más antiguo para ENTRENAR y 20% más nuevo para PROBAR.
    """
    corte = int(len(df) * (1 - FRACCION_TEST))
    # Train: datos del pasado. Test: datos del futuro (simulando la vida real).
    return df.iloc[:corte].copy(), df.iloc[corte:].copy()


def construir_pipeline(features: list[str], df: pd.DataFrame) -> Pipeline:
    """
    Crea el flujo de preprocesamiento y el modelo.
    
    ¿POR QUÉ USAR UN PIPELINE?
    Porque empaqueta la limpieza (imputar nulos, escalar números, codificar texto) 
    junto con el modelo. Esto evita el DATA LEAKAGE (que el escalador aprenda del set de prueba)
    y nos permite guardar TODO en un solo archivo .joblib.
    """
    # Separamos las features por tipo de dato
    cat_cols = [c for c in features if not pd.api.types.is_numeric_dtype(df[c])] # Texto/Categorías
    num_cols = [c for c in features if c not in cat_cols]                       # Números

    # Transformador para columnas de texto/categóricas
    preprocesador = ColumnTransformer([
        ("cat", Pipeline([
            # Si hay nulos en texto, los pone como "desconocido"
            ("imputar", SimpleImputer(strategy="constant", fill_value="desconocido")),
            # Convierte texto a números (0s y 1s). handle_unknown ignora categorías nuevas en el futuro.
            ("codificar", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), cat_cols),
        
        # Transformador para columnas numéricas
        ("num", Pipeline([
            # Si hay nulos en números, usa la mediana de esa columna
            ("imputar", SimpleImputer(strategy="median")),
            # Escala los números para que tengan media 0 y varianza 1 (ayuda a algunos modelos)
            ("escalar", StandardScaler()),
        ]), num_cols),
    ])

    # El algoritmo: Random Forest (Bosque Aleatorio). 
    # Es robusto, funciona bien con datos tabulares y no se sobreajusta fácil.
    clasificador = RandomForestClassifier(
        n_estimators=300,       # 300 árboles de decisión
        max_depth=None,         # Deja que los árboles crezcan lo necesario
        min_samples_leaf=2,     # Evita hojas con un solo dato (sobreajuste)
        class_weight="balanced",# Compensa si hay categorías con más datos que otras
        random_state=SEMILLA, 
        n_jobs=-1               # Usa todos los núcleos del procesador
    )

    # Unimos todo: Preprocesamiento -> Clasificador
    return Pipeline([("prep", preprocesador), ("clf", clasificador)])


def evaluar(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Calcula y guarda las métricas de rendimiento del modelo.
    """
    # El modelo hace las predicciones basándose en las Features del set de prueba (X_test)
    y_pred = pipeline.predict(X_test)
    
    # Calculamos métricas: Accuracy (Aciertos globales) y F1 (Balance entre precisión y recall)
    metricas = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
        "n_test": int(len(X_test)),
        "n_features": int(pipeline.named_steps["prep"].transform(X_test.head(1)).shape[1]),
        "n_clases": int(len(pipeline.named_steps["clf"].classes_)),
    }

    # Guardamos las métricas en un JSON para que Streamlit luego las muestre.
    (CARPETA_ML / "metricas_categoria.json").write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")
    
    reporte = classification_report(y_test, y_pred, zero_division=0, labels=pipeline.named_steps["clf"].classes_)
    (CARPETA_ML / "reporte_clasificacion.txt").write_text(reporte, encoding="utf-8")
    
    matriz = confusion_matrix(y_test, y_pred, labels=pipeline.named_steps["clf"].classes_)
    pd.DataFrame(matriz, index=pipeline.named_steps["clf"].classes_, columns=pipeline.named_steps["clf"].classes_).to_csv(CARPETA_ML / "matriz_confusion_categoria.csv")

    return metricas, y_pred, pipeline.predict_proba(X_test), pipeline.named_steps["clf"].classes_


def guardar_importancias(pipeline: Pipeline) -> None:
    """
    Extrae la importancia de cada feature (Qué pistas le importaron más al modelo).
    """
    nombres = pipeline.named_steps["prep"].get_feature_names_out()
    importancias = pipeline.named_steps["clf"].feature_importances_

    agregadas: dict[str, float] = {}
    for nombre, imp in zip(nombres, importancias):
        # Limpiamos los nombres que OneHotEncoder pone (ej: cat__cuenta_efectivo -> cuenta)
        original = nombre.split("__", 1)[-1]
        for sufijo in ("_desconocido",):
            if original.endswith(sufijo):
                original = original[: -len(sufijo)]
                break
        base = original.split("_", 1)[0] if "_" in original else original
        agregadas[base] = agregadas.get(base, 0.0) + float(imp)

    # Guardamos un CSV con las variables ordenadas de más importante a menos
    pd.Series(agregadas).sort_values(ascending=False).to_csv(CARPETA_ML / "importancia_variables.csv", header=["importancia"])


def guardar_predicciones(contexto: pd.DataFrame, y_pred, y_proba, clases, y_test) -> None:
    """Guarda un archivo con las predicciones (Real vs Predicción) para análisis."""
    salida = contexto.copy()
    salida["categoria_real"] = y_test.values
    salida["categoria_predicha"] = y_pred
    for i, cls in enumerate(clases):
        salida[f"prob_{cls}"] = y_proba[:, i].round(4)
    salida.to_csv(CARPETA_ML / "predicciones_test.csv", index=False)


if __name__ == "__main__":
    print("=" * 70)
    print("ENTRENAMIENTO - Clasificador de categorías - FinaGotchi")
    print("=" * 70)
    
    if not ARCHIVO_ENTRADA.exists():
        raise FileNotFoundError(f"Falta el dataset. Ejecuta los scripts anteriores primero: {ARCHIVO_ENTRADA}")

    # 1. Preparamos los datos. 'features' es la lista de columnas que serán nuestras X.
    df, features = preparar_datos()
    
    # 2. Dividimos en pasado (train) y futuro (test)
    train, test = dividir_temporal(df)
    
    # =========================================================
    # ¡AQUÍ SE DEFINEN X e Y!
    # X = Todas las columnas de 'features' (las pistas)
    # y = La columna TARGET (la respuesta que queremos adivinar)
    # =========================================================
    
    # Para entrenar
    X_train = train[features]  # X (Pistas)
    y_train = train[TARGET]    # y (Respuesta)
    
    # Para probar
    X_test = test[features]    # X (Pistas nuevas)
    y_test = test[TARGET]      # y (Respuesta real para comparar)

    # 3. Construimos y entrenamos el modelo
    pipeline = construir_pipeline(features, df)
    
    print("Entrenando el modelo... (esto puede tardar unos segundos)")
    # .fit() es la función que le enseña al modelo: "Mira X_train, y la respuesta correcta es y_train"
    pipeline.fit(X_train, y_train)

    # 4. Evaluamos el modelo
    metricas, y_pred, y_proba, clases = evaluar(pipeline, X_test, y_test)
    
    print(f"\n   Resultados en el set de prueba (Futuro):")
    print(f"   - Accuracy: {metricas['accuracy']:.3f} (Porcentaje de aciertos)")
    print(f"   - F1 macro: {metricas['f1_macro']:.3f} (Balance del modelo)")

    # 5. Guardamos herramientas para Streamlit
    guardar_importancias(pipeline)
    
    contexto = test[["transaccion_id", "fecha_hora", "monto", "tipo", "cuenta"]]
    guardar_predicciones(contexto, y_pred, y_proba, clases, y_test)

    # GUARDADO FINAL: Empaquetamos TODO el pipeline (limpieza + modelo) en un archivo.
    # Este archivo es el que Streamlit consumirá.
    joblib.dump(pipeline, CARPETA_ML / "modelo_categoria.joblib")
    
    print(f"\n   Proceso terminado. Archivo modelo guardado en: {CARPETA_ML / 'modelo_categoria.joblib'}")