from playwright.sync_api import sync_playwright
import time

def extraer_auth_instagram():
    with sync_playwright() as p:
        # Lanzamos el Chromium de Playwright
        print("Iniciando Chromium...")
        browser = p.chromium.launch(headless=False) # Necesitamos verlo para loguearnos
        
        # Creamos un contexto nuevo
        context = browser.new_context()
        page = context.new_page()

        # Vamos a Instagram
        print("Navegando a Instagram...")
        page.goto("https://www.instagram.com/", wait_until="networkidle")

        print("\n" + "="*50)
        print("ACCIONES REQUERIDAS:")
        print("1. Ingresa tu usuario y contraseña en la ventana del navegador.")
        print("2. Si tienes verificación de dos pasos, complétala.")
        print("3. Una vez que estés dentro de tu Feed y veas las historias/posts...")
        print("4. Regresa aquí y presiona ENTER para guardar la sesión.")
        print("="*50 + "\n")

        input("Presiona ENTER aquí cuando ya estés logueado...")

        # Guardamos el estado de almacenamiento (cookies, tokens, etc.)
        context.storage_state(path="auth.json")
        
        print("\n✅ ¡Listo! Se ha generado el archivo 'auth.json'.")
        print("Ya puedes usar este archivo para tus scrapes sin volver a loguearte.")
        
        browser.close()

if __name__ == "__main__":
    extraer_auth_instagram()