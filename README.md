# Monitor de Precios GMKtec EVO-X2

Este proyecto monitoriza automáticamente los precios del mini PC GMKtec EVO-X2 (variantes de 96GB y 128GB) en varias tiendas online.

## Funcionalidades

- **Scraping Automático:** Se ejecuta 2 veces al día (9:00 y 21:00 UTC) mediante GitHub Actions.
- **Alertas por Telegram:** Envía un mensaje instantáneo si el precio baja de un umbral definido.
- **Visualización:** Gráfica interactiva de precios con historial.
- **Persistencia:** Los datos se guardan en un archivo JSON en el repositorio.

## Estructura del proyecto

- `config.json`: Archivo de configuración donde defines las URLs a monitorizar y precios objetivo.
- `data/prices.json`: Base de datos histórica (formato JSON).
- `src/scraper.py`: Script Python que realiza el scraping usando Playwright.
- `index.html`: Página web estática para visualizar los datos.
- `.github/workflows/scrape.yml`: Flujo de trabajo de GitHub Actions.

## Configuración y Uso

### 1. Configurar Alertas de Telegram

Para recibir alertas en tu móvil, sigue estos pasos:

#### A. Crear el Bot
1. Abre Telegram y busca a **@BotFather**.
2. Envía el comando `/newbot`.
3. Sigue las instrucciones para ponerle nombre.
4. Al finalizar, te dará un **API TOKEN** (algo como `123456789:ABCdefGHI...`). Guárdalo.

#### B. Obtener tu Chat ID
1. Abre Telegram y busca a **@userinfobot**.
2. Dale a "Start" o envía cualquier mensaje.
3. Te responderá con tu ID (un número tipo `12345678`). Guárdalo.

#### C. Configurar Secretos en GitHub
1. En tu repositorio, ve a **Settings** > **Secrets and variables** > **Actions**.
2. Haz clic en **New repository secret**.
3. Crea `TELEGRAM_BOT_TOKEN` con el token del paso A.
4. Crea `TELEGRAM_CHAT_ID` con el ID del paso B.

### 2. Añadir productos

Edita el archivo `config.json` para añadir las URLs que quieres seguir y el precio objetivo para alertas (`target_price`).

Ejemplo:

```json
[
  {
    "active": true,
    "type": "gmktec_official",
    "site_name": "GMKtec Official",
    "url": "https://de.gmktec.com/...",
    "target_ram": "96GB",
    "target_price": 1700
  },
  {
    "active": true,
    "variant": "128GB",
    "site_name": "PcComponentes",
    "url": "https://www.pccomponentes.com/...",
    "selector": "#precio-main",
    "target_price": 2200
  }
]
```

### 3. Ejecución Manual (GitHub Actions)

Si quieres forzar una actualización de precios ahora mismo sin esperar a la hora programada:

1. Ve a la pestaña **Actions** en tu repositorio de GitHub.
2. En la lista de la izquierda, selecciona el flujo de trabajo **Scrape Prices**.
3. A la derecha, verás un botón desplegable llamado **Run workflow**.
4. Haz clic en él y pulsa el botón verde **Run workflow**.
5. En unos segundos, aparecerá una nueva ejecución en la lista y, al terminar (1-2 min), se actualizará la gráfica y recibirás alertas si hay bajada de precio.

### 4. Despliegue en GitHub Pages

Para ver la gráfica online:
1. Sube este código a GitHub.
2. Ve a **Settings** > **Pages**.
3. En "Source", selecciona `Deploy from a branch`.
4. En "Branch", selecciona `main` (o la rama donde esté tu código) y la carpeta `/` (root).
5. Guarda los cambios. Tu web estará disponible en `https://tu-usuario.github.io/tu-repo/`.

### 5. Ejecutar localmente (Desarrollo)

Si quieres probar el scraper en tu máquina:

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Configura las variables de entorno para Telegram (opcional):
   ```bash
   export TELEGRAM_BOT_TOKEN="tu_token"
   export TELEGRAM_CHAT_ID="tu_chat_id"
   ```
3. Ejecuta el script:
   ```bash
   python src/scraper.py
   ```
4. Para ver la gráfica localmente (debido a restricciones de seguridad del navegador con archivos locales), necesitas iniciar un servidor simple:
   ```bash
   python -m http.server
   ```
   Luego abre `http://localhost:8000` en tu navegador.
