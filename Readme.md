
# Web Scraper con Interfaz Gráfica

## Descripción
Este proyecto es una aplicación de web scraping con interfaz gráfica desarrollada en Python. Permite a los usuarios extraer datos de múltiples sitios web de manera simultánea, con un sistema de caché para optimizar las solicitudes y almacenamiento de datos en diversos formatos.

## Capturas de Pantalla

### Modo claro
![Captura de pantalla de la calculadora en modo claro]()


## Características principales
- Interfaz gráfica de usuario intuitiva
- Scraping multihilo para procesamiento eficiente
- Sistema de caché para reducir solicitudes repetidas
- Almacenamiento de datos en SQLite, CSV, Excel y JSON
- Manejo de errores y registro de actividades
- Rotación de User-Agents para evitar bloqueos

## Requisitos del sistema
- Python 3.7+
- PyQt6
- Pandas
- BeautifulSoup4
- Requests
- Fake-UseragentAgent


## Uso
1. Ejecute la aplicación:
2. En la interfaz gráfica:
   - Ingrese las URLs de los sitios web que desea scrapear en el campo de texto.
   - Haga clic en "Agregar URL" para cada URL que desee incluir.
   - Una vez agregadas todas las URLs, haga clic en "Iniciar Scraping".
   - El progreso se mostrará en la barra de progreso y el estado en la etiqueta inferior.


## Funcionamiento interno
1. La aplicación crea una instancia de `WebScraper` para cada sesión de scraping.
2. Cada URL se procesa en un hilo separado para mejorar la eficiencia.
3. Los datos se extraen utilizando BeautifulSoup4 y se almacenan temporalmente en memoria.
4. Al finalizar, los datos se guardan en la base de datos SQLite y se exportan a CSV, Excel y JSON.
5. El sistema de caché guarda las respuestas HTTP para reducir solicitudes repetidas en un período de 24 horas.

## Limitaciones y consideraciones éticas
- Este scraper está diseñado para uso educativo y de investigación.
- Asegúrese de respetar los términos de servicio de los sitios web que está scrapeando.
- Implemente retrasos entre solicitudes para no sobrecargar los servidores objetivo.
- Algunos sitios web pueden tener medidas anti-scraping que podrían bloquear la aplicación.

## Resolución de problemas
- Si experimenta bloqueos frecuentes, intente aumentar los retrasos entre solicitudes.
- Verifique su conexión a Internet si el scraper falla al conectarse a los sitios web.
- Asegúrese de que las clases CSS utilizadas para la extracción de datos sean correctas para los sitios objetivo.
