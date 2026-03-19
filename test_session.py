from playwright.sync_api import sync_playwright

def scrape_con_sesion():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # CARGAMOS EL ARCHIVO AQUÍ
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()
        
        # Al ir a Instagram, ya deberías aparecer logueado
        page.goto("https://www.instagram.com/")
        
        # Aquí ya podrías empezar a buscar tus selectores de reacciones
        page.wait_for_timeout(5000)
        browser.close()

if __name__ == "__main__":
    scrape_con_sesion()