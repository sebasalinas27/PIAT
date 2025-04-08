#!/usr/bin/env python
# coding: utf-8

import os
import streamlit as st
import numpy as np
import pandas as pd
import io

# Configuración de la app
st.title("Optimización de Asignación de Productos")
st.write("Sube tu archivo Excel con los datos y obtén la asignación optimizada.")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Leer archivos
        df_stock = pd.read_excel(uploaded_file, sheet_name='Stock Disponible')
        df_prioridad = pd.read_excel(uploaded_file, sheet_name='Prioridad Clientes', index_col=0)
        df_minimos = pd.read_excel(uploaded_file, sheet_name='Mínimos de Asignación', index_col=[0, 1])

        # Filtrar stock > 0
        df_stock_filtrado = df_stock[df_stock['Stock Disponible'] > 0].set_index('Codigo')

        # Encontrar códigos comunes
        codigos_comunes = set(df_stock_filtrado.index).intersection(df_minimos.index.get_level_values(0))

        if len(codigos_comunes) == 0:
            st.warning("⚠️ No hay códigos en común entre 'Stock Disponible' y 'Mínimos de Asignación'. El stock se mantendrá igual.")
            df_stock_filtrado['Stock Restante'] = df_stock_filtrado['Stock Disponible']
            df_asignacion = pd.DataFrame(0, index=df_stock_filtrado.index.unique(), columns=df_prioridad.index)
        else:
            # Mostrar advertencia si hay códigos no comunes
            if len(codigos_comunes) < len(df_stock_filtrado.index):
                st.warning("⚠️ No hay códigos en común para todos los productos. Se continuará solo con los productos con mínimos definidos.")

            # Solo usar códigos comunes
            codigos_comunes = sorted(codigos_comunes)
            df_stock_filtrado = df_stock_filtrado.loc[codigos_comunes]
            df_minimos_filtrado = df_minimos.loc[codigos_comunes]

            prioridad_clientes = pd.to_numeric(df_prioridad.iloc[:, 0], errors='coerce').fillna(0)
            clientes_ordenados = prioridad_clientes.sort_values().index.tolist()

            # Inicializar asignación y stock restante
            df_asignacion = pd.DataFrame(0, index=df_stock_filtrado.index, columns=clientes_ordenados)
            df_stock_filtrado['Stock Restante'] = df_stock_filtrado['Stock Disponible']

            # Asignación mínima por prioridad
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

        # Guardar salida
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_asignacion.to_excel(writer, sheet_name="Asignación Óptima")
            df_stock_filtrado.to_excel(writer, sheet_name="Stock Disponible")
            df_prioridad.to_excel(writer, sheet_name="Prioridad Clientes")
            df_minimos.to_excel(writer, sheet_name="Mínimos de Asignación")
        output.seek(0)

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
