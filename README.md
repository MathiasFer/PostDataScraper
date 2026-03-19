# Instagram Post & Reel Scraper Orchestrator

Este proyecto es un orquestador que permite realizar scraping masivo de publicaciones de Instagram (Posts y Reels) a partir de un archivo Excel, comparando las métricas obtenidas con las reportadas originalmente.

## Estructura del Proyecto

- `main.py`: Script principal que orquesta la lectura, scraping y generación de resultados.
- `posts.py`: Contiene la clase `InstagramPostFinder` para encontrar métricas de imágenes y álbumes.
- `reels.py`: Contiene la clase `InstagramReelFinder` para encontrar métricas de videos (Reels).
- `extractor.py`: Utility script para generar el archivo `auth.json` mediante un inicio de sesión manual.
- `input_posts.xlsx`: Archivo Excel de entrada con los datos de las publicaciones a procesar.

## Requisitos Previos

1. Tener Python instalado.
2. Instalar las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## Configuración de Sesión (Importante)

Para que el scraping funcione sin ser bloqueado, es necesario generar un archivo `auth.json` con tu sesión de Instagram:

1. Ejecuta el script de extracción:
   ```bash
   python extractor.py
   ```
2. Se abrirá una ventana de navegador. Inicia sesión en tu cuenta de Instagram manualmente.
3. Una vez logueado y viendo tu feed, regresa a la terminal y presiona **ENTER**.
4. Esto generará el archivo `auth.json` que los buscadores usarán automáticamente.

## Uso del Orquestador

1. Asegúrate de que `input_posts.xlsx` contenga las columnas requeridas (`Id Publicación`, `Usuario`, `Enlace`, `Tipo publicación`, `Comentarios`, `Reacciones`, `Reproducciones`).
2. Ejecuta el orquestador:
   ```bash
   python main.py
   ```
3. El script procesará cada fila, extraerá el shortcode del enlace y buscará las métricas reales en Instagram.
4. Mostrará el progreso en la consola.
5. Al finalizar, se generará el archivo `scraped_results.xlsx`.

## Resultados y Formato Condicional

El archivo `scraped_results.xlsx` contiene una comparativa entre los datos originales (**SCAN**) y los datos obtenidos de la red social (**REDES SOCIALES**).

**Formato Condicional:** (Sólo visible en Excel)
- Si la diferencia porcentual en cualquiera de las 3 métricas (Comentarios, Reacciones, Reproducciones) es mayor al **5%**, la celda de **Id Publicación** se pintará de **rojo**.
- Esta marcación ayuda a identificar rápidamente inconsistencias o datos desactualizados.

---
**Nota:** No modifiques `posts.py` ni `reels.py`, ya que el orquestador depende de sus interfaces actuales.
