#!/usr/bin/env python
# coding: utf-8

# In[4]:


# 🔹 Codigo final postulado

import numpy as np
import pandas as pd
from scipy.optimize import linprog

# 💕 Rutas de archivos de entrada y salida
entrada_path = "Template_Pruebas_PIAT.xlsx"
salida_path = "asignacion_resultados_completo.xlsx"

# 🔹 1. Cargar datos
df_stock = pd.read_excel(entrada_path, sheet_name='Stock Disponible')
df_prioridad = pd.read_excel(entrada_path, sheet_name='Prioridad Clientes', index_col=0)
df_minimos = pd.read_excel(entrada_path, sheet_name='Mínimos de Asignación', index_col=[0, 1])

# 🔹 2. Filtrar datos innecesarios
# Filtrar productos con stock disponible
df_stock_filtrado = df_stock[df_stock['Stock Disponible'] > 0].set_index('Codigo')

# Filtrar códigos comunes entre 'Stock Disponible' y 'Mínimos de Asignación'
codigos_comunes = set(df_stock_filtrado.index).intersection(df_minimos.index.get_level_values(0))
if not codigos_comunes:
    raise ValueError("❌ No se encontraron códigos comunes entre 'Stock Disponible' y 'Mínimos de Asignación'. Verifica los datos.")

codigos_comunes_lista = list(codigos_comunes)

# Aplicar filtros a los DataFrames
df_stock_filtrado = df_stock_filtrado.loc[codigos_comunes_lista].sort_index()
df_minimos_filtrado = df_minimos.loc[codigos_comunes_lista].sort_index()

# Preparar datos para el modelo
prioridad_clientes = pd.to_numeric(df_prioridad.iloc[:, 0], errors='coerce').fillna(0)

# Ordenar clientes por prioridad de menor a mayor
clientes_ordenados = prioridad_clientes.sort_values().index.tolist()

# Inicializar DataFrame para la asignación
df_asignacion = pd.DataFrame(0, index=df_minimos_filtrado.index.get_level_values(0).unique(), columns=clientes_ordenados)

# 🔹 3. Asignación por prioridad
df_stock_filtrado['Stock Restante'] = df_stock_filtrado['Stock Disponible']

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

# Guardar en Excel
with pd.ExcelWriter(salida_path) as writer:
    df_asignacion.to_excel(writer, sheet_name="Asignación Óptima")
    df_stock_filtrado.to_excel(writer, sheet_name="Stock Disponible")
    df_prioridad.to_excel(writer, sheet_name="Prioridad Clientes")
    df_minimos_filtrado.to_excel(writer, sheet_name="Mínimos de Asignación")

print(f"✅ Optimización completada. Resultados guardados en '{salida_path}'.")


# In[ ]:




