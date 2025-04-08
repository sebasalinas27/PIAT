#!/usr/bin/env python
# coding: utf-8

# 🔹 Codigo final postulado
import os
import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import linprog
import io

# Instalar xlsxwriter si no está disponible
os.system("pip install xlsxwriter")

# Configuración de la app
st.title("Optimización de Asignación de Productos")
st.write("Sube tu archivo Excel con los datos y obtén la asignación optimizada.")

# Subida de archivo
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Cargar datos desde el archivo subido
        df_stock = pd.read_excel(uploaded_file, sheet_name='Stock Disponible')
        df_prioridad = pd.read_excel(uploaded_file, sheet_name='Prioridad Clientes', index_col=0)
        df_minimos = pd.read_excel(uploaded_file, sheet_name='Mínimos de Asignación', index_col=[0, 1])

        # 🔹 1. Filtrar y preparar stock
        df_stock_filtrado = df_stock[df_stock['Stock Disponible'] > 0].set_index('Codigo')
        df_stock_filtrado['Stock Restante'] = df_stock_filtrado['Stock Disponible']

        # 🔹 2. Preparar mínimos
        codigos_con_minimos = set(df_minimos.index.get_level_values(0))
        codigos_existentes = set(df_stock_filtrado.index)
        codigos_asignables = codigos_con_minimos.intersection(codigos_existentes)
        df_minimos_filtrado = df_minimos.loc[list(codigos_asignables)].sort_index()

        # 🔹 3. Asignación
        prioridad_clientes = pd.to_numeric(df_prioridad.iloc[:, 0], errors='coerce').fillna(0)
        clientes_ordenados = prioridad_clientes.sort_values().index.tolist()
        df_asignacion = pd.DataFrame(0, index=df_minimos_filtrado.index.get_level_values(0).unique(), columns=clientes_ordenados)

        for cliente in clientes_ordenados:
            for codigo in df_stock_filtrado.index:
                minimo_requerido = df_minimos_filtrado.loc[(codigo, cliente), 'Minimo'] if (codigo, cliente) in df_minimos_filtrado.index else 0
                stock_disponible = df_stock_filtrado.at[codigo, 'Stock Restante']
                if minimo_requerido > 0:
                    if stock_disponible >= minimo_requerido:
                        df_asignacion.at[codigo, cliente] = minimo_requerido
                        df_stock_filtrado.at[codigo, 'Stock Restante'] -= minimo_requerido
                    else:
                        df_asignacion.at[codigo, cliente] = stock_disponible
                        df_stock_filtrado.at[codigo, 'Stock Restante'] = 0

        # Guardar en un archivo de salida virtual
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_asignacion.to_excel(writer, sheet_name="Asignación Óptima")
            df_stock_filtrado.to_excel(writer, sheet_name="Stock Disponible")
            df_prioridad.to_excel(writer, sheet_name="Prioridad Clientes")
            df_minimos_filtrado.to_excel(writer, sheet_name="Mínimos de Asignación")
        output.seek(0)

        # Botón para descargar el archivo optimizado
        st.success("✅ Optimización completada. Descarga tu archivo optimizado.")
        st.download_button(
            label="Descargar archivo optimizado",
            data=output,
            file_name="resultado_optimizado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error en la optimización: {str(e)}")
else:
    st.warning("⚠️ Por favor, sube un archivo para continuar.")
