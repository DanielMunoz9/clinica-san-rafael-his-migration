#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración y limpieza de datos para HIS Clínica San Rafael
Equipo: Daniel Munoz9
"""

import pandas as pd
import re
import os
from typing import Tuple
from datetime import datetime

# ============ CONFIGURACIÓN ============
NUMERO_EQUIPO = 9  # ← CAMBIAR AQUÍ SI ES OTRO EQUIPO
ARCHIVO_ENTRADA = "Migracion_DanielMunoz9.csv"
DIRECTORIO_SALIDA = "datos_limpios"

# ============ CREAR DIRECTORIO DE SALIDA ============
os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)

# ============ FUNCIONES DE NORMALIZACIÓN ============
def normalizar_nombre(valor):
    """Normaliza nombre: limpia espacios y capitalización"""
    if pd.isna(valor):
        return "", "nombre_vacio"
    nombre = str(valor).strip()
    if not nombre:
        return "", "nombre_vacio"
    return " ".join(nombre.split()).title(), ""

def normalizar_email(valor):
    """Normaliza email a minúsculas"""
    if pd.isna(valor):
        return "", "email_vacio"
    email = str(valor).strip().lower()
    if "@" not in email:
        return "", "email_invalido"
    return email, ""

def normalizar_telefono(valor) -> Tuple[str, str]:
    """
    Normaliza teléfono a formato +57XXXXXXXXXX
    Retorna: (teléfono_normalizado, motivo_error)
    """
    if pd.isna(valor):
        return "", "telefono_vacio"
    
    # Extraer solo dígitos
    digitos = re.sub(r"\D+", "", str(valor))
    
    # Remover prefijos internacionales alternativos
    if digitos.startswith("0057"):
        digitos = digitos[2:]  # deja '57...'
    if digitos.startswith("057"):
        digitos = digitos[1:]  # deja '57...'
    
    # Validar y normalizar
    if digitos.startswith("57") and len(digitos) >= 12:
        core = digitos[-10:]  # últimos 10 dígitos
        return f"+57{core}", ""
    elif len(digitos) == 10:
        return f"+57{digitos}", ""
    else:
        return "", f"telefono_invalido_long_{len(digitos)}"

def normalizar_fecha(valor, campo_nombre) -> Tuple[str, str]:
    """
    Normaliza fecha al formato DD/MM/AAAA
    Retorna: (fecha_normalizada, motivo_error)
    """
    if pd.isna(valor):
        return "", f"{campo_nombre}_vacio"
    
    valor_str = str(valor).strip()
    if not valor_str:
        return "", f"{campo_nombre}_vacio"
    
    try:
        # Intentar parsear con formato DD/MM/YYYY
        fecha_obj = pd.to_datetime(valor_str, dayfirst=True, infer_datetime_format=True)
        return fecha_obj.strftime("%d/%m/%Y"), ""
    except:
        return "", f"{campo_nombre}_formato_invalido"

# ============ CARGAR DATOS ============
print(f"⏳ Cargando archivo: {ARCHIVO_ENTRADA}...")
df = pd.read_csv(ARCHIVO_ENTRADA)
print(f"✓ {len(df)} registros cargados\n")

# ============ NORMALIZACIONES ============
print("🔄 Normalizando datos...")

# Almacenar errores
errores_rows = []

# Normalizar nombre
df[['nombre_normalizado', 'error_nombre']] = df['nombre_completo'].apply(
    lambda x: pd.Series(normalizar_nombre(x))
)

# Normalizar email
df[['email_normalizado', 'error_email']] = df['correo'].apply(
    lambda x: pd.Series(normalizar_email(x))
)

# Normalizar teléfono
df[['telefono_normalizado', 'error_telefono']] = df['telefono'].apply(
    lambda x: pd.Series(normalizar_telefono(x))
)

# Normalizar fechas
df[['fecha_nac_norm', 'error_fecha_nac']] = df['fecha_nacimiento'].apply(
    lambda x: pd.Series(normalizar_fecha(x, "fecha_nacimiento"))
)

df[['fecha_cita_norm', 'error_fecha_cita']] = df['fecha_ultima_cita'].apply(
    lambda x: pd.Series(normalizar_fecha(x, "fecha_ultima_cita"))
)

# ============ IDENTIFICAR REGISTROS CON ERRORES ============
print("\n⚠️  Identificando registros con errores...")

# Máscara de registros con errores
errores_mask = (
    (df['error_nombre'] != "") |
    (df['error_email'] != "") |
    (df['error_telefono'] != "") |
    (df['error_fecha_nac'] != "") |
    (df['error_fecha_cita'] != "")
)

# Guardar registros con errores
for idx, row in df[errores_mask].iterrows():
    errores_list = []
    if row['error_nombre']:
        errores_list.append(row['error_nombre'])
    if row['error_email']:
        errores_list.append(row['error_email'])
    if row['error_telefono']:
        errores_list.append(row['error_telefono'])
    if row['error_fecha_nac']:
        errores_list.append(row['error_fecha_nac'])
    if row['error_fecha_cita']:
        errores_list.append(row['error_fecha_cita'])
    
    errores_rows.append({
        'id_original': row['id'],
        'nombre': row['nombre_completo'],
        'email': row['correo'],
        'errores': ' | '.join(errores_list),
        'motivo': 'datos_incompletos_o_invalidos'
    })

# Filtrar solo registros válidos
df_validos = df[~errores_mask].copy()

print(f"✓ {len(df_validos)} registros válidos")
print(f"✗ {len(df) - len(df_validos)} registros con errores\n")

# ============ ELIMINAR DUPLICADOS ============
print("🔍 Eliminando duplicados...")

# Ordenar por fecha de cita (más reciente primero) para conservar la mejor versión
df_validos['fecha_cita_dt'] = pd.to_datetime(
    df_validos['fecha_cita_norm'], 
    format='%d/%m/%Y'
)
df_validos = df_validos.sort_values('fecha_cita_dt', ascending=False)

# Duplicados por email
duplicados_antes = len(df_validos)
df_validos = df_validos.drop_duplicates(subset=['email_normalizado'], keep='first')
duplicados_eliminados = duplicados_antes - len(df_validos)

if duplicados_eliminados > 0:
    print(f"✓ {duplicados_eliminados} registros duplicados eliminados")
    errores_rows.append({
        'id_original': '',
        'nombre': '',
        'email': '',
        'errores': f'duplicados_eliminados',
        'motivo': f'{duplicados_eliminados} registros con email duplicado (conservado más reciente)'
    })

# ============ REASIGNAR IDs SECUENCIALES ============
print("🔢 Reasignando IDs secuenciales...")
df_validos = df_validos.reset_index(drop=True)
df_validos['id_nuevo'] = df_validos.index + 1

# ============ CREAR CSV LIMPIO ============
print("\n📝 Creando CSV limpio...")

# Seleccionar columnas finales
df_final = df_validos[[
    'id_nuevo',
    'nombre_normalizado',
    'fecha_nac_norm',
    'email_normalizado',
    'telefono_normalizado',
    'fecha_cita_norm',
    'diagnostico'
]].rename(columns={
    'id_nuevo': 'id',
    'nombre_normalizado': 'nombre_completo',
    'fecha_nac_norm': 'fecha_nacimiento',
    'email_normalizado': 'correo',
    'telefono_normalizado': 'telefono',
    'fecha_cita_norm': 'fecha_ultima_cita'
})

# Guardar CSV limpio
archivo_salida = os.path.join(DIRECTORIO_SALIDA, f"Migracion_Equipo{NUMERO_EQUIPO}.csv")
df_final.to_csv(archivo_salida, index=False, encoding='utf-8')
print(f"✓ Archivo guardado: {archivo_salida}")

# ============ CREAR REPORTE DE CALIDAD ============
print("📊 Generando reporte de calidad...")

if errores_rows:
    reporte_df = pd.DataFrame(errores_rows)
    reporte_path = os.path.join(DIRECTORIO_SALIDA, f"reporte_calidad_equipo{NUMERO_EQUIPO}.csv")
    reporte_df.to_csv(reporte_path, index=False, encoding='utf-8')
    print(f"✓ Reporte generado: {reporte_path}")

# ============ RESUMEN FINAL ============
print("\n" + "="*60)
print("📈 RESUMEN DE MIGRACIÓN")
print("="*60)
print(f"Registros originales:    {len(df)}")
print(f"Registros con errores:   {len(df) - len(df_validos)}")
print(f"Duplicados eliminados:   {duplicados_eliminados}")
print(f"Registros finales:       {len(df_final)}")
print(f"\n✓ Migración completada exitosamente")
print(f"✓ Archivo: {archivo_salida}")
print("="*60)
