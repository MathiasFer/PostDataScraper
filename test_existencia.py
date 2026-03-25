from playwright.sync_api import sync_playwright

def construir_url(shortcode, tipo="post"):
    if tipo == "reel":
        return f"https://www.instagram.com/reel/{shortcode}/"
    else:
        return f"https://www.instagram.com/p/{shortcode}/"


def validar_existencia_playwright_batch(shortcodes, tipo="post", auth_file="auth.json"):
    """
    Valida existencia de múltiples shortcodes manteniendo una sola instancia de navegador.

    Retorna un dict: { "shortcode1": True, "shortcode2": False }
    """
    if not shortcodes:
        return {}

    # Normalizamos para no romper el batch si llega una lista con valores falsy.
    shortcodes = [sc for sc in shortcodes if isinstance(sc, str) and sc.strip()]
    if not shortcodes:
        return {}

    resultados = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Mantiene el comportamiento previo
        context = browser.new_context(storage_state=auth_file)
        page = context.new_page()

        try:
            for shortcode in shortcodes:
                url = construir_url(shortcode, tipo)

                try:
                    # Navegamos en la misma pestaña para evitar overhead de abrir nuevas páginas.
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)  # Pequeña espera para que React cargue contenido

                    final_url = (page.url or "").lower()
                    html = page.content().lower()

                    # Criterio: si redirige a login -> NO EXISTE
                    if "login" in final_url:
                        resultados[shortcode] = False
                        continue

                    # Criterio: mensajes de no-disponibilidad -> NO EXISTE
                    if (
                        "esta página no está disponible" in html
                        or "page isn't available" in html
                    ):
                        resultados[shortcode] = False
                        continue

                    resultados[shortcode] = True

                except Exception:
                    resultados[shortcode] = False

        finally:
            browser.close()

    return resultados


def validar_existencia_playwright(shortcode, tipo="post", auth_file="auth.json"):
    # Mantiene compatibilidad con el uso anterior de la función.
    resultados = validar_existencia_playwright_batch([shortcode], tipo=tipo, auth_file=auth_file)
    return resultados.get(shortcode, False)


if __name__ == "__main__":
    pruebas = [
        ("DVwS8KrCZsP", "post"),
        ("DVyyV6fE8Q4", "reel"),
        ("DVzpxRQDaYC", "reel"),
        ("DVt7pZnFZCx", "post")
    ]

    # Ejemplo rápido con batch.
    posts = [code for code, tipo in pruebas if tipo == "post"]
    reels = [code for code, tipo in pruebas if tipo == "reel"]
    print(validar_existencia_playwright_batch(posts, tipo="post"))
    print(validar_existencia_playwright_batch(reels, tipo="reel"))