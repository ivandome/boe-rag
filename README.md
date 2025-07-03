# Proyecto de Extracción de Datos del BOE

## Descripción Corta

Este proyecto implementa un sistema para la extracción (scraping) y almacenamiento automatizado de datos del Boletín Oficial del Estado (BOE) de España. Utiliza Python y la biblioteca de orquestación de flujos de trabajo Prefect para gestionar los procesos de recopilación de información.

## Funcionalidades Principales

El sistema ofrece las siguientes capacidades:

1.  **Recopilación de Metadatos de Artículos por Fecha:**
    *   Descarga el índice XML diario del BOE para una fecha determinada.
    *   Extrae los identificadores únicos de todos los artículos publicados (ej., `BOE-A-YYYY-NNNNN`).
    *   Para cada artículo, recopila metadatos esenciales, incluyendo las URLs directas a sus versiones en formato XML y PDF.
    *   Almacena estos metadatos de forma estructurada en un archivo JSONL (`data/boe_metadata.jsonl`).
2.  **Extracción de Contenido Textual de Artículos:**
    *   Permite la descarga del contenido completo de una URL específica del BOE (generalmente, la URL XML de un artículo).
    *   Extrae y guarda el contenido textual plano en un archivo dentro del directorio `data/raw/`.
3.  **Orquestación de Flujos con Prefect:**
    *   Define y gestiona los procesos de extracción y almacenamiento mediante flujos de trabajo (`flows`) y tareas (`tasks`) de Prefect.
    *   Incluye configuración para despliegues de Prefect (`prefect.yaml`).

## Tecnologías Utilizadas

*   **Python 3.x**
*   **Prefect:** Para la orquestación de flujos de trabajo.
*   **Requests:** Para realizar peticiones HTTP a los servicios del BOE.
*   **Beautiful Soup 4 (bs4):** Para el parseo de contenido HTML/XML (aunque el uso principal para el BOE se centra en XML).
*   ** estándar de Python:** `re` (expresiones regulares), `json`, `pathlib`.

## Estructura del Proyecto

```
.
├── data/
│   ├── raw/                # Almacena el contenido textual extraído de artículos
│   │   └── boe_13297.txt   # Ejemplo de archivo de texto
│   └── boe_metadata.jsonl  # Almacena los metadatos de los artículos en formato JSONL
├── flows/
│   ├── __init__.py
│   ├── scrape_and_store.py       # Flujo de Prefect para descargar y guardar contenido de una URL
│   └── scrape_boe_day_metadata.py # Flujo de Prefect para obtener metadatos de un día
├── main.py                 # Punto de entrada para ejecuciones de prueba de los flujos
├── prefect.yaml            # Configuración del proyecto y despliegues de Prefect
├── tasks/
│   ├── __init__.py
│   ├── boe.py              # Tareas específicas para interactuar con el BOE
│   ├── scraping.py         # Tareas genéricas de scraping
│   └── storage.py          # Tareas para el almacenamiento de datos
└── README.md               # Este archivo
```

## Instalación

1.  **Clonar el repositorio (si aplica):**
    ```bash
    git clone <url-del-repositorio>
    cd <nombre-del-directorio>
    ```
2.  **Crear y activar un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Linux/macOS
    # venv\Scripts\activate    # En Windows
    ```
3.  **Instalar dependencias:**
    El proyecto incluye un archivo `requirements.txt` con todas las dependencias necesarias, incluyendo las de desarrollo como `pytest`. Para instalarlas:
    ```bash
    pip install -r requirements.txt
    ```

## Configuración

*   **Prefect:** El archivo `prefect.yaml` define la configuración del proyecto Prefect y los despliegues.
    *   El `work_pool` y `work_queue_name` pueden necesitar ajustarse según el entorno del agente de Prefect.
    *   La sección `pull` actualmente contiene una ruta de directorio absoluta que debería modificarse para mayor portabilidad si se utiliza la característica de `set_working_directory` en despliegues.
*   **Parámetros de Flujo:**
    *   El flujo `scrape_boe_day_metadata` en `main.py` tiene la fecha "2025-06-28" hardcodeada para pruebas. Para ejecuciones parametrizadas, esta fecha debe pasarse como argumento al flujo.
    *   El flujo `scrape_and_store` toma `url` y `filename` como parámetros, que pueden ser especificados al ejecutar o desplegar el flujo.
    *   El nombre del archivo de metadatos (`data/boe_metadata.jsonl`) está actualmente hardcodeado en la tarea `tasks.storage.append_metadata`. Para mayor flexibilidad, podría convertirse en un parámetro de configuración.

## Uso Básico

Existen dos maneras principales de ejecutar los flujos:

1.  **Mediante `main.py` (para desarrollo y pruebas locales):**
    El archivo `main.py` está configurado para ejecutar uno de los flujos. Por defecto (según el análisis actual), ejecuta `scrape_boe_day_metadata`:
    ```bash
    python main.py
    ```
    Puedes modificar `main.py` para ejecutar otros flujos o cambiar parámetros.

    **Nota sobre `PREFECT_API_URL`:** Si al ejecutar `python main.py` encuentras un error similar a `ValueError: No Prefect API URL provided...`, significa que Prefect está intentando conectarse a un servidor backend y no encuentra la configuración. Para ejecuciones locales de desarrollo con `main.py` que interactúan con el motor de Prefect, puedes necesitar:

    *   **Iniciar un servidor Prefect local (opcional, si deseas usar la UI y características del backend):**
        En una terminal separada, ejecuta:
        ```bash
        prefect server start
        ```
        Esto iniciará un servidor local (usualmente en `http://127.0.0.1:4200`).

    *   **Configurar la URL de la API:**
        Una vez que el servidor esté en funcionamiento (o si te conectas a otra instancia de Prefect), configura la variable de entorno `PREFECT_API_URL` en la terminal donde ejecutarás `main.py`:
        ```bash
        export PREFECT_API_URL="http://127.0.0.1:4200/api"
        # Para Windows (cmd.exe): set PREFECT_API_URL="http://127.0.0.1:4200/api"
        # Para Windows (PowerShell): $env:PREFECT_API_URL="http://127.0.0.1:4200/api"
        ```
        Alternativamente, puedes configurar esto en tu perfil de Prefect:
        ```bash
        prefect profile set-api-url http://127.0.0.1:4200/api
        ```
        Si prefieres ejecutar los flujos de `main.py` sin un backend (de forma completamente efímera y local, perdiendo características como la UI o el historial de ejecuciones persistente), asegúrate de que tu configuración de Prefect o la forma en que se invocan los flujos no requieran explícitamente un servidor. Para pruebas simples, a veces invocar la función del flujo directamente con `.fn()` (ej. `nombre_del_flujo.fn(...)`) puede evitar la necesidad de un backend, pero esto es más para pruebas unitarias de la lógica del flujo que para una ejecución completa con el motor Prefect.

2.  **Mediante Despliegues de Prefect:**
    El archivo `prefect.yaml` define un despliegue llamado `scrape-boe` para el flujo `scrape_and_store`.
    *   **Construir el despliegue (si es la primera vez o hay cambios):**
        ```bash
        prefect deployment build flows/scrape_and_store.py:scrape_and_store -n scrape-boe -q default
        ```
        (Ajusta los parámetros según `prefect.yaml` o tus necesidades).
    *   **Aplicar el despliegue:**
        ```bash
        prefect deployment apply scrape_and_store-deployment.yaml
        ```
        (El nombre del archivo YAML puede variar según la salida del comando `build`).
    *   **Ejecutar el flujo desde un agente de Prefect:**
        Asegúrate de tener un agente de Prefect iniciado y escuchando la cola de trabajo especificada (ej., `default`):
        ```bash
        prefect agent start -q default
        ```
        Luego, puedes ejecutar el flujo desde la UI de Prefect o mediante la CLI.

## Pruebas

Este proyecto utiliza `pytest` para la ejecución de pruebas unitarias y de integración, y `pytest-cov` para medir la cobertura de código.

Para ejecutar las pruebas:

1.  **Asegúrate de tener las dependencias de desarrollo instaladas:**
    Si seguiste la sección de "Instalación", ya deberías tener `pytest` y `pytest-cov` instalados desde `requirements.txt`. Si no, instálalas:
    ```bash
    pip install pytest pytest-cov
    # o reinstala todas las dependencias
    # pip install -r requirements.txt
    ```

2.  **Ejecutar Pytest:**
    Desde la raíz del repositorio, ejecuta el siguiente comando:
    ```bash
    pytest
    ```
    Esto descubrirá y ejecutará automáticamente todas las pruebas en el directorio `tests/`. También generará un informe de cobertura en la terminal y un archivo `coverage.xml`.

## Posibles Mejoras / Próximos Pasos

Basado en el análisis inicial del proyecto, se sugieren las siguientes áreas de mejora:

*   **Robustez y Manejo de Errores:** Implementar reintentos, manejo de excepciones más específico y validación de datos.
*   **Configuración Avanzada:** Externalizar todas las configuraciones hardcodeadas.
*   **Logging:** Integrar un sistema de logging detallado.
*   **Pruebas Automatizadas:** Desarrollar tests unitarios y de integración.
*   **Gestión de Dependencias:** Crear y mantener un archivo `requirements.txt` o `pyproject.toml`.
*   **Escalabilidad:** Explorar la ejecución concurrente/paralela de tareas para grandes volúmenes de datos.
*   **Parseo Avanzado de Contenido:** Desarrollar parsers específicos para la estructura interna de los artículos del BOE si se requiere un análisis de contenido más profundo.
*   **Documentación:** Mantener y expandir este README y añadir comentarios en el código donde sea necesario.

```
