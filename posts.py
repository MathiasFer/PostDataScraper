import json
from playwright.sync_api import sync_playwright

class InstagramPostFinder:
    def __init__(self, auth_file="auth.json"):
        self.auth_file = auth_file
        self.target_code = None
        self.target_codes = None  # modo batch: set[str]
        self.found_data = None
        self.found_data_map = {}  # modo batch: {code: data}
        # Para evitar registrar múltiples listeners si reutilizamos la misma page.
        self._attached_page_ids = set()

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
                    
                    # Batch: si estamos buscando varios códigos, guardamos todos los que aparezcan.
                    if self.target_codes is not None and current_code in self.target_codes:
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

                        self.found_data_map[current_code] = {
                            "code": current_code,
                            "likes": likes,
                            "comments": comments,
                            "views": views
                        }
                        print(f"🎯 Post Detectado [{current_code}] -> {likes} Likes, {comments} Comms.")

                    # Modo single (compatibilidad con el método original).
                    if self.target_codes is None and current_code == self.target_code:
                        # --- EXTRACCIÓN DE LIKES ---
                        likes = 0
                        if "edge_media_preview_like" in node:
                            likes = node["edge_media_preview_like"].get("count", 0)
                        elif "edge_liked_by" in node:
                            likes = node["edge_liked_by"].get("count", 0)
                        elif "like_count" in node:  # Algunos nodos nuevos lo traen directo
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
        self.target_codes = None
        self.found_data = None
        self.found_data_map = {}
        
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

    def buscar_post_especifico_en_pagina(self, perfil_url, target_code, page):
        """
        Variante que reutiliza una page existente (sin abrir/cerrar browser).
        Útil para scraping batch donde se quiere 1 solo navegador para muchos posts.
        """
        self.target_code = target_code
        self.target_codes = None
        self.found_data = None
        self.found_data_map = {}

        # Adjuntamos handler solo una vez por page.
        page_id = id(page)
        if page_id not in self._attached_page_ids:
            page.on("response", self.handle_response)
            self._attached_page_ids.add(page_id)

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
            page.wait_for_timeout(3500)  # Un poco más de tiempo para el feed principal
            intentos_scroll += 1
            print(f"Scroll {intentos_scroll}... analizando red.")

        return self.found_data

    def buscar_posts_multiples_en_pagina(self, perfil_url, target_codes, page):
        """
        Busca múltiples posts dentro de una misma page (sin recargar por shortcode).

        Retorna dict: { shortcode: {code, likes, comments, views} }
        """
        self.target_codes = set(target_codes) if target_codes else set()
        self.found_data = None
        self.found_data_map = {}

        page_id = id(page)
        if page_id not in self._attached_page_ids:
            page.on("response", self.handle_response)
            self._attached_page_ids.add(page_id)

        print(f"Buscando {len(self.target_codes)} posts en {perfil_url}...")
        # Cargar perfil una sola vez.
        try:
            page.goto(perfil_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Aviso: la página tardó en cargar; se intentará igual. Error: {e}")

        intentos_scroll = 0
        max_intentos = 50

        while len(self.found_data_map) < len(self.target_codes) and intentos_scroll < max_intentos:
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(3500)
            intentos_scroll += 1
            print(f"Scroll {intentos_scroll}... buscando posts en la red.")

        return dict(self.found_data_map)

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