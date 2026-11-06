import streamlit as st
import pandas as pd
import joblib
import json
from pathlib import Path

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Finagotchi - Predicción", page_icon="🐷", layout="wide")

# --- RUTAS ---
BASE_DIR = Path(__file__).resolve().parent 
MODEL_PATH = BASE_DIR / "dataset_500" / "ml" / "modelo_categoria.joblib"
METRICAS_PATH = BASE_DIR / "dataset_500" / "ml" / "metricas_categoria.json"
IMPORTANCIA_PATH = BASE_DIR / "dataset_500" / "ml" / "importancia_variables.csv"

# --- CARGAR MODELO Y DATOS ---
@st.cache_resource # Esto hace que el modelo se cargue una sola vez y la app sea rápida
def cargar_modelo():
    return joblib.load(MODEL_PATH)

@st.cache_data
def cargar_metricas():
    with open(METRICAS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def cargar_importancia():
    return pd.read_csv(IMPORTANCIA_PATH, index_col=0)

try:
    modelo = cargar_modelo()
    metricas = cargar_metricas()
    importancia = cargar_importancia()
except Exception as e:
    st.error(f"Error al cargar los archivos. Asegúrate de haber corrido el script 03_entrenamiento_categoria.py. Error: {e}")
    st.stop()

# --- INTERFAZ DE USUARIO ---
st.title(" 🐷 FinaGotchi - Clasificador de Gastos")
st.markdown("Ingresa los datos de tu transacción y la IA adivinará a qué categoría pertenece.")

# Creamos dos columnas: Izquierda para el formulario, Derecha para las conclusiones
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Ingresa los datos")
    
    with st.form("formulario_prediccion"):
        # 1. Variables básicas
        monto = st.number_input("Monto del gasto ($)", min_value=0.0, value=15000.0, step=1000.0)
        cuenta = st.selectbox("Cuenta", ["efectivo", "nequi", "daviplata", "tarjeta_credito"])
        tipo = st.selectbox("Tipo de transacción", ["gasto", "ingreso", "transferencia"])
        
        # 2. Variables temporales
        col_dia, col_hora = st.columns(2)
        with col_dia:
            dia_semana_nombre = st.selectbox("Día de la semana", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        with col_hora:
            hora_local = st.slider("Hora del día (0-23)", min_value=0, max_value=23, value=12)
            
        # Calcular automáticamente si es fin de semana (Sábado o Domingo)
        es_fin_de_semana = 1 if dia_semana_nombre in ["Sábado", "Domingo"] else 0
        
        # 3. Variables de contexto del mensaje/IA
        st.markdown("**Contexto del mensaje:**")
        tiene_mensaje_ia = st.checkbox("¿El gasto fue ingresado por un audio/mensaje de IA?")
        coincide_palabra_clave = st.checkbox("¿El texto menciona explícitamente una categoría (ej. 'comida', 'transporte')?")
        
        submit_button = st.form_submit_button(label="🔮 Predecir Categoría")

    if submit_button:
        try:
            # Creamos el DataFrame con EXACTAMENTE las 8 columnas que entrenamos
            datos_usuario = pd.DataFrame([{
                "monto": monto,
                "cuenta": cuenta,
                "tipo": tipo,
                "hora_local": hora_local,
                "dia_semana_nombre": dia_semana_nombre,
                "es_fin_de_semana": es_fin_de_semana,
                "tiene_mensaje_ia": 1 if tiene_mensaje_ia else 0,
                "coincide_palabra_clave_categoria": 1 if coincide_palabra_clave else 0
            }])
            
            # Predecir
            prediccion = modelo.predict(datos_usuario)[0]
            probabilidades = modelo.predict_proba(datos_usuario)[0]
            clases = modelo.classes_
            
            # Mostrar resultados
            st.success(f"La categoría predicha es: **{prediccion.upper()}**")
            
            st.write("Nivel de confianza:")
            for cls, prob in zip(clases, probabilidades):
                st.progress(float(prob), text=f"{cls}: {prob*100:.1f}%")
                
        except Exception as e:
            st.error(f"Error al predecir. Detalle: {e}")
with col2:
    st.subheader("📊 Conclusiones del Modelo")
    
    # --- EXPLICACIÓN TÉCNICA DEL ALGORITMO ---
    st.markdown("""
    ### 🧠 Arquitectura del Modelo
    Para resolver este problema de clasificación, se implementó un **Random Forest (Bosque Aleatorio)** utilizando la librería de código abierto **`scikit-learn`** (específicamente `RandomForestClassifier`).
    
    **¿Cómo funciona?**
    Un Random Forest es un algoritmo de *Ensemble* (aprendizaje conjunto). En lugar de depender de un solo árbol de decisión (que puede memorizar los datos y fallar con datos nuevos), el modelo construye un "bosque" de **300 árboles de decisión independientes**. 
    Cada árbol vota por una categoría basándose en diferentes subconjuntos de datos y variables. La categoría final es la que obtiene la mayor cantidad de votos, lo que hace que el modelo sea altamente **robusto y resistente al sobreajuste**.
    
    Además, se configuró el parámetro `class_weight="balanced"` para compensar el hecho de que algunas categorías de gastos son más frecuentes que otras.
    """)
    
    st.divider() # Línea separadora visual
    
    # --- MÉTRICAS DE EVALUACIÓN ---
    st.markdown("### 📈 Rendimiento (Evaluación Temporal)")
    st.markdown("""
    Para garantizar que el modelo funcione en el mundo real, **no se usaron datos aleatorios para probar**. Se separó el dataset por fecha: el modelo entrenó con el 80% de los datos más antiguos y fue evaluado con el 20% de los datos más recientes (el "futuro" que el modelo nunca vio).
    """)
    
    # Mostrar métricas en columnas para que se vea más limpio
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="Precisión Global (Accuracy)", value=f"{metricas['accuracy']*100:.1f}%", 
                  help="Porcentaje de aciertos totales del modelo.")
    with m2:
        st.metric(label="F1 Score (Balance)", value=f"{metricas['f1_macro']*100:.1f}%",
                  help="Media armónica entre precisión y exhaustividad. Es mejor que el Accuracy cuando hay categorías desbalanceadas.")
    
    st.divider()

    # --- IMPORTANCIA DE VARIABLES ---
    st.markdown("### 🔍 ¿Qué variables (Features) importan más?")
    st.markdown("Una de las grandes ventajas de `Random Forest` es que nos permite extraer la **importancia de las características** (Feature Importance). Esto nos dice qué datos aportaron más información para que el algoritmo tomara la decisión:")
    
    # Mostrar gráfico de importancia de variables
    st.bar_chart(importancia.head(10)) 

    st.info("💡 **Nota:** Las variables con barras más altas (como el 'monto' o si 'coincide_palabra_clave_categoria') son las que más ayudaron a los árboles de decisión a separar una categoría de otra. Las variables con valores muy bajos aportan poco y podrían ser eliminadas en futuras iteraciones del modelo.")