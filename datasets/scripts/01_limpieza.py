"""
Módulo de Limpieza de Datos - FinaGotchi
Realiza la carga inicial, inspección estructural, corrección de tipos 
(exportando el dataset 1) y el rellenado total de nulos (exportando el dataset final).
"""

import pandas as pd
import numpy as np

def cargar_datos_correctos():
    ruta_csv = "datasets/dataset_500/finagotchi_dataset_completo.csv"
    print("--- 1. CARGA DE DATOS (DATASET 500) ---")
    try:
        df = pd.read_csv(ruta_csv, low_memory=False)
        print(f"¡Carga exitosa! Dimensiones del dataset: {df.shape}")
        return df
    except Exception as e:
        print(f"Se detectó un error al cargar el archivo CSV: {e}")
        return None

if __name__ == "__main__":
    df_cargado = cargar_datos_correctos()

    if df_cargado is not None:
        # 2. Información general del DataFrame
        print("\n--- 2. INFORMACIÓN GENERAL DEL DATAFRAME (df.info) ---")   
        df_cargado.info()
        
        # 3. Vista previa de los datos 
        print("\n--- 3. VISTA PREVIA DE LOS DATOS (df.head) ---")
        print(df_cargado.head(5))

        # 4. Tipos de dato de cada columna
        print("\n--- 4. TIPO DE DATO DE CADA COLUMNA ---")
        for columna, tipo in df_cargado.dtypes.items():
            print(f"* {columna} --> Tipo: {tipo}")        

        # 5. Corrección de Tipos de Datos (Fechas) y Exportación del Dataset 1
        print("\n--- 5. CORRECCIÓN DE TIPOS DE DATOS Y EXPORTACIÓN ---")
        columnas_fecha = [
            col for col in df_cargado.columns 
            if 'fecha' in col.lower() or col.endswith('_en') or 'creado' in col.lower() or 'actualizado' in col.lower() or 'ultima_conexion' in col.lower()
        ]
        
        for col in columnas_fecha:
            df_cargado[col] = pd.to_datetime(df_cargado[col], errors='coerce')
            
        print(f"-> Se corrigieron {len(columnas_fecha)} columnas temporales a formato datetime.")
        
        # Exportar el primer dataset con tipos corregidos
        ruta_salida_tipos = "datasets/dataset_500/finagotchi_dataset_tipos_corregidos.csv"
        df_cargado.to_csv(ruta_salida_tipos, index=False)
        print(f"¡Dataset 1 (Tipos corregidos) guardado en: {ruta_salida_tipos}")

        # 6. Análisis de datos nulos antes del relleno
        print("\n--- 6. ANÁLISIS DE DATOS NULOS POR COLUMNA (ANTES DEL RELLENO) ---")
        conteo_nulos = df_cargado.isnull().sum()
        columnas_con_nulos = conteo_nulos[conteo_nulos > 0]
        
        if not columnas_con_nulos.empty:
            print(f"Se encontraron {len(columnas_con_nulos)} columnas con datos nulos:")
            for columna, cantidad in columnas_con_nulos.items():
                print(f"  - {columna}: {cantidad} nulos")

        # 7. Relleno robusto y masivo de nulos (Moda, Mediana y Fechas)
        print("\n--- 7. COMPLETAR DATOS NULOS Y EXPORTACIÓN FINAL ---")
        
        # A. Categóricas (texto): Moda o valor descriptivo por defecto
        cols_cat = df_cargado.select_dtypes(include=['object']).columns
        for col in cols_cat:
            if df_cargado[col].isnull().sum() > 0:
                modo = df_cargado[col].mode()
                val_fill = modo[0] if not modo.empty else 'No especificado'
                df_cargado[col] = df_cargado[col].fillna(val_fill)

        # B. Numéricas: Mediana o 0 si está totalmente vacía
        cols_num = df_cargado.select_dtypes(include=[np.number]).columns
        for col in cols_num:
            if df_cargado[col].isnull().sum() > 0:
                med_val = df_cargado[col].median()
                val_fill = med_val if not np.isnan(med_val) else 0
                df_cargado[col] = df_cargado[col].fillna(val_fill)

        # C. Fechas (datetime): Moda o fecha por defecto
        cols_fec = df_cargado.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns
        for col in cols_fec:
            if df_cargado[col].isnull().sum() > 0:
                modo_fec = df_cargado[col].mode()
                val_fill = modo_fec[0] if not modo_fec.empty else pd.to_datetime('2026-01-01')
                df_cargado[col] = df_cargado[col].fillna(val_fill)

        # Limpieza residual final para garantizar 0 nulos en cualquier caso bordillo
        df_cargado = df_cargado.fillna(0)

        # Exportar el dataset procesado final
        ruta_salida_final = "datasets/dataset_500/finagotchi_dataset_datos_nulos_rellenados.csv"
        df_cargado.to_csv(ruta_salida_final, index=False)
        print(f"¡Dataset 2 (Final procesado y limpio) guardado en: {ruta_salida_final}")

        # 8. Verificación final de datos nulos
        print("\n--- 8. ANÁLISIS DE DATOS NULOS (DATASET FINAL RELLENADO) ---")
        conteo_nulos_final = df_cargado.isnull().sum()
        columnas_con_nulos_final = conteo_nulos_final[conteo_nulos_final > 0]
        
        if not columnas_con_nulos_final.empty:
            print(f"Se encontraron {len(columnas_con_nulos_final)} columnas con datos nulos:")
            for columna, cantidad in columnas_con_nulos_final.items():
                print(f"  - {columna}: {cantidad} nulos")
        else:
            print("¡Excelente! No se encontraron valores nulos en el dataset final (0 nulos).")