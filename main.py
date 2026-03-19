import pandas as pd
import re
import os
import logging
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from posts import InstagramPostFinder
from reels import InstagramReelFinder

# Configuración de logging para seguimiento en consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_shortcode(url):
    """Extrae el shortcode de una URL de Instagram."""
    if not isinstance(url, str):
        return None
    # Busca patrones como /p/CODE/, /reel/CODE/, /reels/CODE/
    match = re.search(r'/(?:p|reel|reels)/([^/?#&]+)', url)
    if match:
        return match.group(1)
    return None

def calculate_diff(real, scan):
    """Calcula la diferencia porcentual: abs(real - scan) / max(real, 1) * 100."""
    try:
        real_val = float(real) if real is not None else 0
        scan_val = float(scan) if scan is not None else 0
        if real_val == 0:
            return 0 if scan_val == 0 else 100.0
        return (abs(real_val - scan_val) / max(real_val, 1)) * 100
    except (ValueError, TypeError):
        return 0

def main():
    input_file = 'input_posts.xlsx'
    output_final = 'scraped_results.xlsx'
    
    if not os.path.exists(input_file):
        logging.error(f"No se encontró el archivo de entrada: {input_file}")
        return

    logging.info(f"Leyendo archivo {input_file}...")
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        logging.error(f"Error al leer el Excel: {e}")
        return
    
    results = []
    total_rows = len(df)
    
    # Instanciar buscadores (se asume que auth.json existe y es válido)
    post_finder = InstagramPostFinder()
    reel_finder = InstagramReelFinder()

    for index, row in df.iterrows():
        logging.info(f"--- Procesando fila {index + 1} de {total_rows} ---")
        
        id_publicacion = row.get('Id Publicación', '')
        usuario = str(row.get('Usuario', ''))
        cuenta = str(row.get('Cuenta', ''))
        tipo = str(row.get('Tipo publicación', ''))
        texto = str(row.get('Texto', ''))
        fecha = str(row.get('Fecha publicación', ''))
        enlace = row.get('Enlace', '')
        
        # Métricas SCAN (del Excel original)
        scan_comments = row.get('Comentarios', 0)
        scan_reactions = row.get('Reacciones', 0)
        scan_plays = row.get('Reproducciones', 0)
        
        shortcode = extract_shortcode(enlace)
        
        scraped_data = None
        link_construido = ""
        
        try:
            if tipo == "Video":
                link_construido = f"https://www.instagram.com/{usuario}/reels/"
                if shortcode:
                    logging.info(f"Buscando Reel [{shortcode}] para {usuario}...")
                    scraped_data = reel_finder.buscar_reel_especifico(link_construido, shortcode)
                else:
                    logging.warning(f"No se pudo extraer shortcode del enlace: {enlace}")
            elif tipo in ["Imagen", "Álbum"]:
                link_construido = f"https://www.instagram.com/{usuario}/"
                if shortcode:
                    logging.info(f"Buscando Post [{shortcode}] para {usuario}...")
                    scraped_data = post_finder.buscar_post_especifico(link_construido, shortcode)
                else:
                    logging.warning(f"No se pudo extraer shortcode del enlace: {enlace}")
            else:
                logging.warning(f"Tipo de publicación no reconocido: {tipo}")
        except Exception as e:
            logging.error(f"Error durante el scraping de la fila {index + 1}: {e}")

        # Métricas REALES (de Redes Sociales)
        real_comments = 0
        real_reactions = 0
        real_plays = 0
        
        if scraped_data:
            real_comments = scraped_data.get('comments', 0)
            real_reactions = scraped_data.get('likes', 0)
            # PostFinder usa 'views', ReelFinder usa 'plays'
            real_plays = scraped_data.get('views') if scraped_data.get('views') is not None else scraped_data.get('plays', 0)
            logging.info(f"Datos obtenidos: Likes={real_reactions}, Comms={real_comments}, Views={real_plays}")
        else:
            logging.warning(f"No se obtuvieron datos para el shortcode {shortcode}")
        
        # Comparación y Umbral (5%)
        diff_c = calculate_diff(real_comments, scan_comments)
        diff_r = calculate_diff(real_reactions, scan_reactions)
        diff_p = calculate_diff(real_plays, scan_plays)
        
        es_inconsistente = (diff_c > 5) or (diff_r > 5) or (diff_p > 5)
        
        # Armar fila de salida
        results.append({
            'Id Publicación': id_publicacion,
            'Usuario Cuenta': cuenta if cuenta and str(cuenta).lower() != 'nan' else usuario,
            'Link': link_construido,
            'Texto': texto,
            'Tipo publicación': tipo,
            'Fecha publicación': fecha,
            'SCAN: Comentarios': scan_comments,
            'SCAN: Reacciones': scan_reactions,
            'SCAN: Reproducciones': scan_plays,
            'REDES SOCIALES: Comentarios': real_comments,
            'REDES SOCIALES: Reacciones': real_reactions,
            'REDES SOCIALES: Reproducciones': real_plays,
            '__inconsistent__': es_inconsistente # Columna oculta para formato
        })

    # Crear DataFrame y guardar a Excel
    logging.info("Generando archivo Excel de salida...")
    output_df = pd.DataFrame(results)
    
    # Usar XlsxWriter o Openpyxl para el formato
    with pd.ExcelWriter(output_final, engine='openpyxl') as writer:
        output_df.drop(columns=['__inconsistent__']).to_excel(writer, index=False, sheet_name='Comparativa')
        
    # Aplicar formato condicional con openpyxl
    wb = load_workbook(output_final)
    ws = wb.active
    red_fill = PatternFill(start_color="FFFF0000", end_color="FFFF0000", fill_type="solid")
    
    # Iterar sobre los resultados para pintar la celda 'Id Publicación' (Columna A)
    for i, res in enumerate(results):
        if res['__inconsistent__']:
            # i + 2 porque el Excel empieza en 1 y la fila 1 es el header
            ws.cell(row=i + 2, column=1).fill = red_fill
            
    wb.save(output_final)
    logging.info(f"¡Proceso completado! Archivo generado: {output_final}")

if __name__ == "__main__":
    main()
