import json
from playwright.sync_api import sync_playwright

class InstagramReelFinder:
    def __init__(self, auth_file="auth.json"):
        self.auth_file = auth_file
        self.target_code = None
        self.found_data = None

    def handle_response(self, response):
        # 1. Filtro de seguridad: Solo procesar respuestas que tengan 'json' en su tipo de contenido
        # o que provengan de la API de Instagram.
        content_type = response.headers.get("content-type", "").lower()
        
        # Evitamos procesar imágenes, videos o fuentes
        if "json" in content_type or "graphql" in response.url:
            try:
                # 2. En lugar de .text(), intentamos directamente .json() 
                # o verificamos la URL antes de decodificar.
                data = response.json()
                
                # Buscamos la estructura en el objeto JSON ya decodificado
                if "data" in data and "xdt_api__v1__clips__user__connection_v2" in data["data"]:
                    items = data["data"]["xdt_api__v1__clips__user__connection_v2"].get("edges", [])
                
                for item in items:
                    media = item.get("node", {}).get("media", {})
                    current_code = media.get("code")
                    
                    if current_code == self.target_code:
                        self.found_data = {
                            "code": current_code,
                            "plays": media.get("play_count"),
                            "likes": media.get("like_count"),
                            "comments": media.get("comment_count")
                        }
                        print(f"🎯 ¡Encontrado! Reel {current_code}: {self.found_data['plays']} views.")
            except Exception:
                # Si no es un JSON válido o falla la decodificación, simplemente ignoramos
                pass
    def buscar_reel_especifico(self, perfil_url, target_code):
        self.target_code = target_code
        self.found_data = None
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.auth_file)
            page = context.new_page()

            # Suscribirse al evento de respuesta
            page.on("response", self.handle_response)

            print(f"Buscando el Reel [{target_code}] en {perfil_url}...")
            
            # CAMBIO AQUÍ: Usamos 'domcontentloaded' que es mucho más rápido
            # y aumentamos el timeout por si el internet está lento en Ecuador
            try:
                page.goto(perfil_url, wait_until="domcontentloaded", timeout=60000)
                # Esperamos 5 segundos manuales para que carguen los primeros Reels
                page.wait_for_timeout(5000) 
            except Exception as e:
                print(f"Aviso: La página tardó en cargar pero intentaremos seguir. Error: {e}")

            intentos_scroll = 0
            max_intentos = 50 

            while not self.found_data and intentos_scroll < max_intentos:
                # Scrollear hacia abajo
                page.mouse.wheel(0, 3000)
                # Bajamos un poco el tiempo de espera entre scrolls para ser más eficientes
                page.wait_for_timeout(3000) 
                intentos_scroll += 1
                print(f"Scroll {intentos_scroll}... buscando datos en la red.")

                # Opcional: Si el scroll no llega al final, a veces ayuda mover el mouse
                if intentos_scroll % 5 == 0:
                     page.mouse.move(100, 100)

            browser.close()
            return self.found_data

if __name__ == "__main__":
    finder = InstagramReelFinder()
    
    # DATOS DE PRUEBA
    url_perfil_reels = "https://www.instagram.com/armandoayalaroblesoficial/reels/"
    codigo_a_buscar = "DVzYEq5AT_p" # El código de tu ejemplo
    
    resultado = finder.buscar_reel_especifico(url_perfil_reels, codigo_a_buscar)
    
    if resultado:
        print("\n--- RESULTADO FINAL ---")
        print(json.dumps(resultado, indent=4))
    else:
        print("\n❌ No se encontró el Reel después de varios scrolls.")