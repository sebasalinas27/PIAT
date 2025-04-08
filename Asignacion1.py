 import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="PIAT - Asignación de Stock", layout="centered")
st.title("📦 IST - Asignación de Stock por Cliente")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Leer hojas
        df_stock = pd.read_excel(uploaded_file, sheet_name="Stock Disponible")
        df_prioridad = pd.read_excel(uploaded_file, sheet_name="Prioridad Clientes", index_col=0)
        df_minimos = pd.read_excel(uploaded_file, sheet_name="Mínimos de Asignación", index_col=[0, 1])

        # Filtrar productos con stock
        df_stock_filtrado = df_stock[df_stock["Stock Disponible"] > 0].set_index("Codigo")

        # Códigos en común entre stock y mínimos
        codigos_comunes = set(df_stock_filtrado.index).intersection(df_minimos.index.get_level_values(0))

        if not codigos_comunes:
            st.warning("⚠️ No hay códigos en común, se continuará solo con los productos con mínimos definidos.")
            codigos_comunes = set(df_minimos.index.get_level_values(0))

        # Filtrar según los códigos válidos
        codigos_comunes_lista = list(codigos_comunes)
        df_stock_filtrado = df_stock[df_stock["Codigo"].isin(codigos_comunes_lista)].set_index("Codigo")
        df_minimos_filtrado = df_minimos.loc[codigos_comunes_lista]

        # Ordenar clientes por prioridad
        prioridad_clientes = pd.to_numeric(df_prioridad.iloc[:, 0], errors="coerce").fillna(0)
        clientes_ordenados = prioridad_clientes.sort_values().index.tolist()

        # Preparar estructura de asignación
        df_asignacion = pd.DataFrame(0, index=df_stock_filtrado.index.unique(), columns=clientes_ordenados)
        df_stock_filtrado["Stock Restante"] = df_stock_filtrado["Stock Disponible"]

        # Asignación por cliente y producto
        for cliente in clientes_ordenados:
            for codigo in df_stock_filtrado.index:
                if (codigo, cliente) in df_minimos_filtrado.index:
                    minimo_requerido = df_minimos_filtrado.loc[(codigo, cliente), "Minimo"]
                else:
                    minimo_requerido = 0

                stock_disponible = df_stock_filtrado.at[codigo, "Stock Restante"]

                if minimo_requerido > 0:
                    if stock_disponible >= minimo_requerido:
                        df_asignacion.at[codigo, cliente] = minimo_requerido
                        df_stock_filtrado.at[codigo, "Stock Restante"] -= minimo_requerido
                    else:
                        df_asignacion.at[codigo, cliente] = stock_disponible
                        df_stock_filtrado.at[codigo, "Stock Restante"] = 0

        # Guardar en archivo descargable
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_asignacion.to_excel(writer, sheet_name="Asignación Óptima")
            df_stock_filtrado.to_excel(writer, sheet_name="Stock Disponible")
            df_prioridad.to_excel(writer, sheet_name="Prioridad Clientes")
            df_minimos_filtrado.to_excel(writer, sheet_name="Mínimos de Asignación")

        output.seek(0)
        st.success("✅ Optimización completada. Descarga tu archivo optimizado.")
        st.download_button(
            label="📥 Descargar archivo Excel",
            data=output,
            file_name="resultado_optimizado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error en la optimización: {str(e)}")
else:
    st.info("📁 Por favor, sube un archivo Excel para comenzar.")
