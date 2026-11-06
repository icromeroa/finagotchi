"""
Módulo de Limpieza de Datos - Finagotchi
Realiza la carga inicial del dataset consolidado de 500 registros 
verificando la integridad y dimensiones estructurales.
"""

import pandas as pd
import numpy as np

def cargar_datos_correctos():
    # Se define la ruta oficial del dataset de 500 registros en el repositorio
    ruta_csv = "datasets/dataset_500/finagotchi_dataset_completo.csv"
    
    print("--- 1. CARGA DE DATOS (DATASET 500) ---")
    try:
        # Se carga el archivo CSV utilizando pandas de forma estándar y eficiente
        df = pd.read_csv(ruta_csv, low_memory=False)
        print(f"¡Carga exitosa! Dimensiones del dataset: {df.shape}")
        return df
    except Exception as e:
        print(f"Se detectó un error al cargar el archivo CSV: {e}")
        return None


def cargar_dataset_con_tipos_corregidos():
    # Se selecciona la ruta del dataset procesado en el paso anterior (el que ya tiene las fechas corregidas)
    ruta_csv = "datasets/dataset_500/finagotchi_dataset_tipos_corregidos.csv"
    
    print("--- CARGA DEL DATASET CON TIPOS CORREGIDOS ---")
    try:
        df = pd.read_csv(ruta_csv, low_memory=False)
        print(f"¡Carga exitosa! Dimensiones del dataset: {df.shape}")
        return df
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return None

if __name__ == "__main__":
    # Se ejecuta la función de carga y se almacena el DataFrame resultante
    df_cargado = cargar_datos_correctos()
    df_procesado = cargar_dataset_con_tipos_corregidos()

    if df_cargado is not None:
#---------------------------
        # 2. Información general del DataFrame
        print("\n--- 2. INFORMACIÓN GENERAL DEL DATAFRAME (df.info) ---")   
        # Muestra el tipo de datos, memoria y cuántos valores no nulos tiene cada columna (como en tu referencia)
        df_cargado.info()
#---------------------------
        # 3. Vista previa de los datos 
        print("\n--- 3. VISTA PREVIA DE LOS DATOS (df.head) ---")
        # Muestra las primeras 5 filas de todas las columnas para inspeccionar el contenido
        print(df_cargado.head(5))
#---------------------------
        # 4. Tipos de dato de cada columna
        print("\n--- 4. TIPO DE DATO DE CADA COLUMNA ---")
        for columna, tipo in df_cargado.dtypes.items():
            print(f"* {columna} --> Tipo: {tipo}")        
#---------------------------
        # 5. Corrección de Tipos de Datos (Fechas) y Exportación del Dataset 1
        print("\n--- 5. CORRECCIÓN DE TIPOS DE DATOS Y EXPORTACIÓN ---")
        
        # Filtro seguro: solo columnas que contengan 'fecha', o que terminen/incluyan marcas de tiempo exactas
        columnas_fecha = [
            col for col in df_cargado.columns 
            if 'fecha' in col.lower() or col.endswith('_en') or 'creado' in col.lower() or 'actualizado' in col.lower() or 'conexion' in col.lower()
        ]
        
        for col in columnas_fecha:
            df_cargado[col] = pd.to_datetime(df_cargado[col], errors='coerce')
            
        print(f"-> Se corrigieron {len(columnas_fecha)} columnas temporales a formato datetime.")
        
        # Exportar el primer dataset con tipos corregidos
        ruta_salida_tipos = "datasets/dataset_500/finagotchi_dataset_tipos_corregidos.csv"
        df_cargado.to_csv(ruta_salida_tipos, index=False)
        print(f"¡Dataset 1 (Tipos corregidos) guardado en: {ruta_salida_tipos}")

#---------------------------
        # 6. Análisis de datos nulos por columna dataset completo
        print("\n--- 6. ANÁLISIS DE DATOS NULOS POR COLUMNA ---")
        # Se calculan los valores nulos totales por cada columna del DataFrame
        conteo_nulos = df_cargado.isnull().sum()
        
        # Se filtran únicamente las columnas que contienen valores nulos mayores a cero
        columnas_con_nulos = conteo_nulos[conteo_nulos > 0]
        
        if not columnas_con_nulos.empty:
            print(f"Se encontraron {len(columnas_con_nulos)} columnas con datos nulos:")
            for columna, cantidad in columnas_con_nulos.items():
                print(f"  - {columna}: {cantidad} nulos")
        else:
            print("¡Excelente! No se encontraron valores nulos en el dataset.")

#---------------------------
        # 7. Relleno de Nulos (Moda para categóricas, Mediana para numéricas) y Exportación Final
        print("\n--- 7. COMPLETAR DATOS NULOS Y EXPORTACIÓN FINAL ---")
        
        # A. Categóricas -> Moda
        cols_cat = df_cargado.select_dtypes(include=['object', 'str']).columns
        for col in cols_cat:
            if df_cargado[col].isnull().sum() > 0:
                moda_val = df_cargado[col].mode()[0]
                df_cargado[col].fillna(moda_val, inplace=True)

        # B. Numéricas -> Mediana
        cols_num = df_cargado.select_dtypes(include=['int64', 'float64']).columns
        for col in cols_num:
            if df_cargado[col].isnull().sum() > 0:
                mediana_val = df_cargado[col].median()
                df_cargado[col].fillna(mediana_val, inplace=True)

        print("-> Datos nulos rellenados correctamente (Moda para texto, Mediana para números).")

        # Exportar el dataset procesado final
        ruta_salida_final = "datasets/dataset_500/finagotchi_dataset_datos_nulos_rellenados.csv"
        df_cargado.to_csv(ruta_salida_final, index=False)
        print(f"¡Dataset 2 (Final procesado y limpio) guardado en: {ruta_salida_final}")


#---------------------------
        # 6. Análisis de datos nulos por columna dataset tipos corregidos
        print("\n--- 6. ANÁLISIS DE DATOS NULOS POR COLUMNA ---")
        # Se calculan los valores nulos totales por cada columna del DataFrame
        conteo_nulos = df_procesado.isnull().sum()
        
        # Se filtran únicamente las columnas que contienen valores nulos mayores a cero
        columnas_con_nulos = conteo_nulos[conteo_nulos > 0]
        
        if not columnas_con_nulos.empty:
            print(f"Se encontraron {len(columnas_con_nulos)} columnas con datos nulos:")
            for columna, cantidad in columnas_con_nulos.items():
                print(f"  - {columna}: {cantidad} nulos")
        else:
            print("¡Excelente! No se encontraron valores nulos en el dataset.")