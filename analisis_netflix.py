import pandas as pd
import os
import json # puede ser útil para debug
from jinja2 import Environment, FileSystemLoader
import math # Para redondear
import traceback # Para obtener información detallada del error si ocurre

# --- Configuración ---
ruta_archivo_csv = './Data/HistorialNetflix.csv' 


# Carpeta donde se guardará el reporte HTML y donde está la plantilla
carpeta_reporte = 'Reporte del análisis'
# Nombre del archivo de plantilla
nombre_plantilla = 'reporte_template.html'
# Nombre del archivo de salida
nombre_salida = 'index.html'


# --- Carga de datos ---
try:
    # Netflix suele usar UTF-8.
    # Usamos low_memory=False para evitar advertencias con archivos grandes o columnas mixtas
    df = pd.read_csv(ruta_archivo_csv, encoding='utf-8', low_memory=False)
    print(f"Archivo '{ruta_archivo_csv}' cargado exitosamente.")

except FileNotFoundError:
    print(f"Error: El archivo '{ruta_archivo_csv}' no se encontró en '{ruta_archivo_csv}'.")
    print("Por favor, verifica que la ruta del archivo sea correcta y que el archivo exista.")
    exit() # Sale del script si el archivo no se encuentra
except Exception as e:
    print(f"Ocurrió un error al cargar el archivo: {e}")
    # traceback.print_exc() # Descomentar para ver detalles técnicos del error
    exit() # Sale del script si ocurre otro error de carga


# --- Renombra columnas a español ---
# Mapeo de nombres de columnas de inglés a español
columnas_nuevas = {
    'Profile Name': 'Nombre de Perfil',
    'Start Time': 'Fecha y Hora de Inicio',
    'Duration': 'Duración',
    'Attributes': 'Atributos',
    'Title': 'Título',
    'Supplemental Video Type': 'Tipo de Video Suplementario',
    'Device Type': 'Tipo de Dispositivo',
    'Bookmark': 'Marcador',
    'Latest Bookmark': 'Último Marcador',
    'Country': 'País'
}

# Verificar si las columnas esperadas existen antes de renombrar
columnas_existentes = df.columns.tolist()
columnas_a_renombrar = {k: v for k, v in columnas_nuevas.items() if k in columnas_existentes}

# Asegurarse de que las columnas críticas existen antes de proceder
columnas_criticas = ['Title', 'Start Time', 'Duration']
for col_en in columnas_criticas:
    if col_en not in columnas_existentes:
        print(f"\nError fatal: La columna esperada '{col_en}' no se encontró en el archivo CSV.")
        print("Columnas encontradas:", columnas_existentes)
        exit()

df = df.rename(columns=columnas_a_renombrar)

print("\n--- Columnas después de renombrar ---")
print(df.columns.tolist())


# --- Limpieza y preparación de datos ---

# 1. Convertir la columna 'Fecha y Hora de Inicio' a tipo datetime
try:
    df['Fecha y Hora de Inicio'] = pd.to_datetime(df['Fecha y Hora de Inicio'], errors='coerce')
    df.dropna(subset=['Fecha y Hora de Inicio'], inplace=True)
    print("\nColumna 'Fecha y Hora de Inicio' convertida a formato datetime.")
except Exception as e:
    print(f"\nError al convertir la columna 'Fecha y Hora de Inicio' a datetime: {e}")
    print("Por favor, verifica el formato de las fechas en tu archivo CSV (ej: M/D/AAAA H:M).")
    # traceback.print_exc() # Descomentar para ver detalles técnicos del error
    exit()

# 2. Convertir la columna 'Duración' a tipo timedelta
try:
    df['Duración_td'] = pd.to_timedelta(df['Duración'], errors='coerce')
    df.dropna(subset=['Duración_td'], inplace=True)
    print("Columna 'Duración' convertida a formato timedelta.")

    df['Duración_segundos'] = df['Duración_td'].dt.total_seconds()

    # Limpiar entradas muy cortas (ej: menos de 30 segundos)
    umbral_segundos = 30
    vistas_antes = len(df)
    df = df[df['Duración_segundos'] >= umbral_segundos].copy()
    vistas_despues = len(df)
    print(f"Eliminadas {vistas_antes - vistas_despues} entradas con duración menor a {umbral_segundos} segundos.")

except Exception as e:
    print(f"\nError al convertir la columna 'Duración' a timedelta: {e}")
    print("Por favor, verifica el formato de las duraciones en tu archivo CSV (debería ser HH:MM:SS o similar).")
    # traceback.print_exc() # Descomentar para ver detalles técnicos del error
    exit()


# 3. Extraer nombre principal del título
df['Título Principal'] = df['Título'].apply(lambda x: x.split(':')[0].strip() if pd.notnull(x) else x)

# 4. Extraer componentes de fecha y hora
df['Año'] = df['Fecha y Hora de Inicio'].dt.year
df['Mes'] = df['Fecha y Hora de Inicio'].dt.month
df['Día del Mes'] = df['Fecha y Hora de Inicio'].dt.day
df['Día de la Semana'] = df['Fecha y Hora de Inicio'].dt.day_name()
df['Hora del Día'] = df['Fecha y Hora de Inicio'].dt.hour
# df['Día del Año'] = df['Fecha y Hora de Inicio'].dt.dayofyear # No usado en el dashboard actual, pero podría ser útil


# --- Análisis de Datos ---

print("\n--- Realizando Análisis de Datos ---")

# Asegurarse de que el DataFrame no está vacío después de la limpieza
if df.empty:
    print("\nError: El DataFrame está vacío después de la limpieza. No hay datos para analizar.")
    # No salimos, simplemente no habrá datos en el reporte
    total_vistas = 0
    total_duracion = "N/A"
    primer_vista = "N/A"
    ultima_vista = "N/A"
    titulos_unicos = 0
    # Datos vacíos para gráficos
    empty_data = {'categories': [], 'series': [{'name': '', 'data': []}]}
    empty_pie_data = {'series': [], 'labels': []}

    top_titles_count_data = empty_data
    top_titles_duration_data = empty_data
    views_day_data = empty_data
    duration_day_data = empty_data
    views_hour_data = empty_data
    duration_hour_data = empty_data
    views_profile_data = empty_pie_data 
    views_device_data = empty_data
    views_year_data = empty_data

else:
    # Métricas clave para el dashboard (texto)
    total_vistas = len(df)
    total_duracion_td = df['Duración_td'].sum()
    # Formatear duración total para mostrar en HTML
    def format_timedelta(td):
        if pd.isna(td):
            return "N/A"
        total_seconds = int(td.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts: # Incluir segundos si hay, o si la duración es 0 (ej: 0s)
             # Redondear segundos si es necesario, o solo mostrar si es > 0
             if seconds > 0 or total_seconds == 0:
                parts.append(f"{seconds}s")
             elif not parts: # Si es > 0 pero menos de un minuto
                 parts.append(f"{total_seconds}s")


        return " ".join(parts) if parts else "0s"


    total_duracion = format_timedelta(total_duracion_td)
    primer_vista = df['Fecha y Hora de Inicio'].min().strftime('%d/%m/%Y %H:%M')
    ultima_vista = df['Fecha y Hora de Inicio'].max().strftime('%d/%m/%Y %H:%M')
    titulos_unicos = df['Título Principal'].nunique()


    # --- Preparación de Datos para ApexCharts ---

    # Función auxiliar para formatear datos de conteo (barras)
    def format_count_data(series, name='Conteo'):
        # Limitar a un número razonable si hay demasiados (ej: Top 50)
        # series = series.head(50) # Opcional: limitar para gráficos más limpios
        # Maneja el caso de Series vacías
        if series.empty:
            return {'categories': [], 'series': [{'name': name, 'data': []}]}
        return {
            'categories': series.index.tolist(),
            'series': [{'name': name, 'data': series.values.tolist()}]
        }

    # Función auxiliar para formatear datos de duración (barras - en horas)
    def format_duration_data(series_td, name='Tiempo Total (horas)'):
        # series_td = series_td.head(50) # Opcional: limitar
         # Manejar el caso de Series vacías
        if series_td.empty:
             return {'categories': [], 'series': [{'name': name, 'data': []}]}

        # Convertir a horas y redondear a 2 decimales
        duration_hours = (series_td.dt.total_seconds() / 3600).round(2)
        return {
            'categories': duration_hours.index.tolist(),
            'series': [{'name': name, 'data': duration_hours.values.tolist()}]
        }

    # Función auxiliar para formatear datos de pastel/donut
    def format_pie_data(series):
         # Eliminar categorías con 0 si no queremos mostrarlas en el pastel
         series = series[series > 0]
         # Manejar el caso de Series vacías
         if series.empty:
              return {'series': [], 'labels': []}

         return {
             'series': series.values.tolist(),
             'labels': series.index.tolist()
         }


    # Datos: Top 10 Títulos (Conteo)
    top_titles_count = df['Título'].value_counts().head(10)
    top_titles_count_data = format_count_data(top_titles_count, name='Visualizaciones')


    # Datos: Top 10 Títulos Principales (Duración)
    top_main_titles_duration = df.groupby('Título Principal')['Duración_td'].sum().sort_values(ascending=False).head(10)
    # Pasamos horas calculadas
    top_main_titles_duration_hours = (top_main_titles_duration.dt.total_seconds() / 3600).round(2)
    # Manejar el caso de Series vacías después del groupby
    if top_main_titles_duration_hours.empty:
         top_titles_duration_data = empty_data
    else:
        top_titles_duration_data = {
            'categories': top_main_titles_duration_hours.index.tolist(),
            'series': [{'name': 'Tiempo Total (horas)', 'data': top_main_titles_duration_hours.values.tolist()}]
        }


    # Datos: Vistas por Día de la Semana (Conteo)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # Asegurar que todos los días estén presentes, incluso con 0 vistas
    views_per_day_of_week = df['Día de la Semana'].value_counts().reindex(days_order, fill_value=0)
    views_day_data = format_count_data(views_per_day_of_week, name='Visualizaciones')

    # Datos: Tiempo Total por Día de la Semana (Duración)
    total_duration_per_day_of_week = df.groupby('Día de la Semana')['Duración_td'].sum().reindex(days_order, fill_value=pd.Timedelta(0))
    duration_day_data = format_duration_data(total_duration_per_day_of_week, name='Tiempo Total (horas)')


    # Datos: Vistas por Hora del Día (Conteo)
    # Asegura que todas las horas (0-23) estén presentes
    views_per_hour = df['Hora del Día'].value_counts().sort_index().reindex(range(0, 24), fill_value=0)
    views_hour_data = format_count_data(views_per_hour, name='Visualizaciones')

    # Datos: Tiempo Total por Hora del Día (Duración)
    total_duration_per_hour = df.groupby('Hora del Día')['Duración_td'].sum().sort_index().reindex(range(0, 24), fill_value=pd.Timedelta(0))
    duration_hour_data = format_duration_data(total_duration_per_hour, name='Tiempo Total (horas)')


    # Datos: Vistas por Perfil (Pie_chart)
    views_per_profile = df['Nombre de Perfil'].value_counts()
    views_profile_data = format_pie_data(views_per_profile)


    # Datos: Vistas por Dispositivo (Barras)
    views_per_device = df['Tipo de Dispositivo'].value_counts()
    views_device_data = format_count_data(views_per_device, name='Visualizaciones')


    # Datos: Vistas por Año (Barras)
    views_per_year = df['Año'].value_counts().sort_index()
    views_year_data = format_count_data(views_per_year, name='Visualizaciones')


# --- Generación del Reporte HTML ---

print(f"\n--- Generando Reporte HTML en '{carpeta_reporte}/{nombre_salida}' ---")

# Crea la carpeta de reporte si no existe
try:
    os.makedirs(carpeta_reporte, exist_ok=True)
except Exception as e:
    print(f"\nError al crear la carpeta '{carpeta_reporte}': {e}")
    # traceback.print_exc()
    exit()


# Obtener la ruta completa del directorio donde se está ejecutando este script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta absoluta a la carpeta donde se encuentra la plantilla
# Directorio del script + la carpeta del reporte
template_folder_abs = os.path.join(script_dir, carpeta_reporte)


# Configura Jinja2 para cargar la plantilla desde la carpeta ABSOLUTA del reporte
try:
    env = Environment(loader=FileSystemLoader(template_folder_abs))
except Exception as e:
     print(f"\nError al configurar el cargador de Jinja2 con la ruta '{template_folder_abs}': {e}")
     # traceback.print_exc()
     exit()


# Carga la plantilla usando SOLO su nombre de archivo.
# (Jinja2 busca dentro del directorio especificado en el loader)
try:
    template = env.get_template(nombre_plantilla)
except Exception as e:
    # Añadir un mensaje de error más específico si falla la carga de la plantilla
    print(f"\nError CRÍTICO al cargar la plantilla '{nombre_plantilla}'.")
    print(f"Jinja2 la buscó en el directorio ABSOLUTO: '{template_folder_abs}'.")
    print("Por favor, verifica que el archivo reporte_template.html se encuentre exactamente en esa ubicación.")
    print(f"Detalle del error: {e}")
    # traceback.print_exc() # Descomentar para ver detalles técnicos del error
    exit()


# Renderiza la plantilla con los datos preparados
try:
    html_output = template.render(
        total_vistas=total_vistas,
        total_duracion=total_duracion,
        primer_vista=primer_vista,
        ultima_vista=ultima_vista,
        titulos_unicos=titulos_unicos,
        top_titles_count_data=top_titles_count_data,
        top_titles_duration_data=top_titles_duration_data,
        views_day_data=views_day_data,
        duration_day_data=duration_day_data,
        views_hour_data=views_hour_data,
        duration_hour_data=duration_hour_data,
        views_profile_data=views_profile_data,
        views_device_data=views_device_data,
        views_year_data=views_year_data
    )
except Exception as e:
    print(f"\nError al renderizar la plantilla con los datos: {e}")
    # traceback.print_exc()
    exit()


# Guardar el resultado en el archivo HTML de salida
ruta_salida_html = os.path.join(carpeta_reporte, nombre_salida)
try:
    with open(ruta_salida_html, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"\nReporte generado exitosamente en: {os.path.abspath(ruta_salida_html)}")
    

except Exception as e:
     print(f"\nError al escribir el archivo de reporte '{ruta_salida_html}': {e}")
     # traceback.print_exc()


print("\n--- Proceso Completado ---")