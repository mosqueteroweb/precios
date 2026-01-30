# Monitor de Precios GMKtec EVO-X2

Este proyecto monitoriza automáticamente los precios del mini PC GMKtec EVO-X2 (variantes de 96GB y 128GB) en varias tiendas online.

## Funcionalidades

- **Scraping Automático:** Se ejecuta 2 veces al día (9:00 y 21:00 UTC) mediante GitHub Actions.
- **Alertas por Email:** Envía un correo electrónico si el precio baja de un umbral definido.
- **Visualización:** Gráfica interactiva de precios con historial.
- **Persistencia:** Los datos se guardan en un archivo JSON en el repositorio.

## Estructura del proyecto

- `config.json`: Archivo de configuración donde defines las URLs a monitorizar y precios objetivo.
- `data/prices.json`: Base de datos histórica (formato JSON).
- `src/scraper.py`: Script Python que realiza el scraping usando Playwright.
- `index.html`: Página web estática para visualizar los datos.
- `.github/workflows/scrape.yml`: Flujo de trabajo de GitHub Actions.

## Configuración y Uso

### 1. Configurar Alertas de Email (Opcional)

Para recibir alertas, necesitas configurar dos "Secretos" en tu repositorio de GitHub:

1. Ve a **Settings** > **Secrets and variables** > **Actions**.
2. Haz clic en **New repository secret**.
3. Crea `EMAIL_USER`: Tu dirección de Gmail (ej: `tuemail@gmail.com`).
4. Crea `EMAIL_PASS`: Tu contraseña de aplicación de Google.
   - *Nota:* No uses tu contraseña normal. Ve a [Google Account > Seguridad > Verificación en dos pasos > Contraseñas de aplicaciones](https://myaccount.google.com/apppasswords) y genera una nueva.

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
    "target_price": 1700,
    "recipient_email": "tucorreo@gmail.com"
  },
  {
    "active": true,
    "variant": "128GB",
    "site_name": "PcComponentes",
    "url": "https://www.pccomponentes.com/...",
    "selector": "#precio-main",
    "target_price": 2200,
    "recipient_email": "tucorreo@gmail.com"
  }
]
```

### 3. Ejecutar localmente (Pruebas)

Si quieres probar el scraper en tu máquina:

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Configura las variables de entorno para el email (opcional):
   ```bash
   export EMAIL_USER="tuemail@gmail.com"
   export EMAIL_PASS="tu_contraseña_app"
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

### 4. Despliegue en GitHub Pages

Para ver la gráfica online:
1. Sube este código a GitHub.
2. Ve a **Settings** > **Pages**.
3. En "Source", selecciona `Deploy from a branch`.
4. En "Branch", selecciona `main` (o la rama donde esté tu código) y la carpeta `/` (root).
5. Guarda los cambios. Tu web estará disponible en `https://tu-usuario.github.io/tu-repo/`.
