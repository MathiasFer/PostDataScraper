import json
from playwright.sync_api import sync_playwright

class InstagramPostFinder:
    def __init__(self, auth_file="auth.json"):
        self.auth_file = auth_file
        self.target_code = None
        self.found_data = None

    def handle_response(self, response):
        content_type = response.headers.get("content-type", "").lower()
        
        if "json" in content_type or "graphql" in response.url:
            try:
                data = response.json()
                # Navegamos la estructura exacta que mencionaste
                container = data.get("data", {}).get("xdt_api__v1__feed__user_timeline_graphql_connection", {})
                edges = container.get("edges", [])

                for edge in edges:
                    node = edge.get("node", {})
                    current_code = node.get("code")
                    
                    if current_code == self.target_code:
                        # --- EXTRACCIÓN DE LIKES ---
                        # Instagram suele enviarlo en 'edge_media_preview_like' o 'edge_liked_by'
                        likes = 0
                        if "edge_media_preview_like" in node:
                            likes = node["edge_media_preview_like"].get("count", 0)
                        elif "edge_liked_by" in node:
                            likes = node["edge_liked_by"].get("count", 0)
                        elif "like_count" in node: # Algunos nodos nuevos lo traen directo
                            likes = node["like_count"]

                        # --- EXTRACCIÓN DE COMENTARIOS ---
                        comments = 0
                        if "edge_media_to_comment" in node:
                            comments = node["edge_media_to_comment"].get("count", 0)
                        elif "comment_count" in node:
                            comments = node["comment_count"]

                        # --- EXTRACCIÓN DE VIEWS (Si es video) ---
                        views = node.get("video_view_count", 0)

                        self.found_data = {
                            "code": current_code,
                            "likes": likes,
                            "comments": comments,
                            "views": views
                        }
                        print(f"🎯 Post Detectado [{current_code}] -> {likes} Likes, {comments} Comms.")
            except Exception:
                pass

    def buscar_post_especifico(self, perfil_url, target_code):
        self.target_code = target_code
        self.found_data = None
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.auth_file)
            page = context.new_page()

            page.on("response", self.handle_response)

            print(f"Buscando el Post [{target_code}] en {perfil_url}...")
            
            try:
                # Vamos al perfil principal (sin /reels)
                page.goto(perfil_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000) 
            except Exception as e:
                print(f"Aviso: Carga lenta, procediendo con scroll. {e}")

            intentos_scroll = 0
            max_intentos = 50 

            while not self.found_data and intentos_scroll < max_intentos:
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(3500) # Un poco más de tiempo para el feed principal
                intentos_scroll += 1
                print(f"Scroll {intentos_scroll}... analizando red.")

            browser.close()
            return self.found_data

if __name__ == "__main__":
    finder = InstagramPostFinder()
    
    # DATOS DE PRUEBA
    url_perfil = "https://www.instagram.com/fronterabaja/"
    codigo_a_buscar = "DVrs9Y7CICI" # El código de tu post de ejemplo
    
    resultado = finder.buscar_post_especifico(url_perfil, codigo_a_buscar)
    
    if resultado:
        print("\n--- DATOS DEL POST ---")
        print(json.dumps(resultado, indent=4))
    else:
        print("\n❌ No se encontró el post en el perfil.")