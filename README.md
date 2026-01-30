# Monitor de Precios GMKtec EVO-X2

Este proyecto monitoriza automáticamente los precios del mini PC GMKtec EVO-X2 (variantes de 96GB y 128GB) en varias tiendas online.

## Funcionalidades

- **Scraping Automático:** Se ejecuta 2 veces al día (9:00 y 21:00 UTC) mediante GitHub Actions.
- **Visualización:** Gráfica interactiva de precios con historial.
- **Persistencia:** Los datos se guardan en un archivo JSON en el repositorio.

## Estructura del proyecto

- `config.json`: Archivo de configuración donde defines las URLs a monitorizar.
- `data/prices.json`: Base de datos histórica (formato JSON).
- `src/scraper.py`: Script Python que realiza el scraping usando Playwright.
- `index.html`: Página web estática para visualizar los datos.
- `.github/workflows/scrape.yml`: Flujo de trabajo de GitHub Actions.

## Configuración y Uso

### 1. Añadir productos

Edita el archivo `config.json` para añadir las URLs que quieres seguir. Ejemplo:

```json
[
  {
    "active": true,
    "variant": "96GB",
    "site_name": "Amazon",
    "url": "https://www.amazon.es/dp/B0CX...",
    "selector": ".a-price-whole"
  },
  {
    "active": true,
    "variant": "128GB",
    "site_name": "PcComponentes",
    "url": "https://www.pccomponentes.com/...",
    "selector": "#precio-main"
  }
]
```

**Consejo para encontrar selectores:**
1. Abre la web del producto en tu navegador (Chrome/Firefox).
2. Haz clic derecho sobre el precio y selecciona "Inspeccionar".
3. Busca el atributo `class` o `id` del elemento que contiene el precio.
   - Si es una clase (ej: `class="price"`), usa `.price`.
   - Si es un ID (ej: `id="product-price"`), usa `#product-price`.

### 2. Ejecutar localmente (Pruebas)

Si quieres probar el scraper en tu máquina:

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Ejecuta el script:
   ```bash
   python src/scraper.py
   ```
3. Para ver la gráfica localmente (debido a restricciones de seguridad del navegador con archivos locales), necesitas iniciar un servidor simple:
   ```bash
   python -m http.server
   ```
   Luego abre `http://localhost:8000` en tu navegador.

### 3. Despliegue en GitHub Pages

Para ver la gráfica online:
1. Sube este código a GitHub.
2. Ve a **Settings** > **Pages**.
3. En "Source", selecciona `Deploy from a branch`.
4. En "Branch", selecciona `main` (o la rama donde esté tu código) y la carpeta `/` (root).
5. Guarda los cambios. Tu web estará disponible en `https://tu-usuario.github.io/tu-repo/`.
