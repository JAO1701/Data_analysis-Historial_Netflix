# Análisis de Historial de Visualizaciones de Netflix

Este proyecto proporciona un script en Python para procesar y analizar tu historial de visualizaciones de Netflix. El script genera un dashboard interactivo en HTML, utilizando `pandas` para el procesamiento de datos y `Apexchart.js` (a través de una plantilla `jinja2`) para la renderización de gráficos.

## Características y Proceso

El script sigue los siguientes pasos:

1.  **Configuración Inicial:**
    * Define las rutas y nombres de los archivos clave: el archivo CSV de entrada (`HistorialNetflix.csv`) y la carpeta y nombre del archivo HTML de salida (`Reporte del análisis/index.html`).

2.  **Carga de Datos:**
    * Lee el archivo CSV de historial utilizando la librería `pandas`.
    * Incluye manejo básico de errores para `FileNotFoundError` y otros problemas durante la carga.

3.  **Limpieza y Transformación (ETL):**
    * Renombra las columnas del DataFrame a español para una mayor claridad.
    * Convierte las columnas de fecha/hora (`Fecha y Hora de Inicio`) y duración (`Duración`) a los tipos de datos `datetime` y `timedelta` de pandas, respectivamente.
    * Filtra las entradas con una duración muy corta ( configurable, por defecto menos de 30 segundos), considerándolas no como visualizaciones completas.
    * Extrae el título principal de cada entrada y desglosa la fecha/hora en componentes como año, mes, día del mes, día de la semana y hora del día.

4.  **Análisis de Datos:**
    * Calcula métricas clave como el total de visualizaciones, el tiempo total de reproducción, la fecha de la primera y última visualización, y el número de títulos únicos vistos.
    * Agrega datos para la generación de diversos gráficos:
        * Top títulos por conteo de visualizaciones.
        * Top títulos principales por duración total de visualización.
        * Visualizaciones y duración por día de la semana.
        * Visualizaciones y duración por hora del día.
        * Visualizaciones por perfil de usuario.
        * Visualizaciones por tipo de dispositivo.
        * Visualizaciones por año.

5.  **Generación de Reporte HTML:**
    * Utiliza la librería `jinja2` para renderizar una plantilla HTML (`reporte_template.html`).
    * Inserta todos los resultados del análisis (métricas y datos para gráficos) en la plantilla.
    * Guarda el resultado HTML final como `index.html` dentro de la carpeta de reporte especificada, creando un dashboard visual de tu historial.

## Requisitos

* Python 3.x
* pandas
* jinja2
* Se requiere un archivo `reporte_template.html` en la carpeta especificada para la plantilla del reporte.
* Se requiere el archivo CSV de historial de Netflix (generalmente `HistorialNetflix.csv`) en la ruta especificada.
