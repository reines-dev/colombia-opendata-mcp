# Roadmap y Características (Features)

Este documento detalla el estado actual del servidor MCP para datos.gov.co, así como las características planeadas para futuras versiones que ampliarán su capacidad y utilidad.

## 🌟 Características Actuales (Current Features)

Las siguientes herramientas ya están implementadas y funcionales, permitiendo una exploración robusta del portal de datos abiertos:

- **Búsqueda de Conjuntos de Datos (`search_datasets`)**:
  - Permite buscar conjuntos de datos por palabras clave utilizando la API de Socrata (SODA).
  - Devuelve resultados relevantes que incluyen el identificador único (`dataset_id`), el nombre y la descripción de la base de datos.
  - Soporta paginación básica mediante atributos de límite.

- **Exploración de Metadatos (`get_dataset_metadata`)**:
  - A partir de un `dataset_id`, recupera el esquema completo de la tabla.
  - Expone el nombre real de cada columna (`fieldName`), su tipo de dato (texto, número, fecha, etc.) y su descripción, permitiendo al LLM entender cómo usar la información.

- **Consulta Dinámica de Datos (`query_dataset`)**:
  - Herramienta principal para extraer los registros (filas).
  - Integración completa con **SoQL (Socrata Query Language)** permitiendo:
    - Seleccionar columnas específicas (`$select`).
    - Aplicar filtros condicionales robustos (`$where`), como búsquedas exactas o rangos.
    - Limitar y paginar los resultados (`$limit`, `$offset`).

- **Soporte de Contenedorización**:
  - `Dockerfile` listo para compilar una imagen ligera de Python.
  - Comunicación estándar de entrada/salida (stdio) optimizada para uso con clientes MCP (ej. Claude Desktop).

- **Analítica Avanzada: Agregaciones (`aggregate_dataset`) y Exportación (`export_dataset_to_csv`)**:
  - Permite agrupar variables numéricas derivando el cómputo matematico directamente al servidor Socrata (ideal para contar sumatorias masivas o promedios sobre millones de filas instantáneamente).
  - Volcado a archivos locales CSV estructurados utilizando auto-paginación del API, lo que empodera al usuario para cruzar información en Pandas, Excel o R posteriormente desconectados.

---

## 🚀 Características Futuras (Future Features)

El servidor tiene un gran potencial de expansión. A continuación se listan las mejoras y nuevas herramientas que se planean integrar:

### 1. Mejoras en Consultas (SoQL Avanzado)
- **Ordenamiento (`$order`)**: Añadir parámetros para ordenar los resultados de forma ascendente o descendente.

### 2. Descubrimiento Avanzado
- **Listar Categorías / Dominios (`list_categories`)**: Una herramienta que permita al LLM ver qué temas principales existen en *datos.gov.co* (Salud, Educación, Seguridad, Transporte) antes de realizar una búsqueda por palabra clave.
- **Obtención de Vistas/Gráficos**: Extraer no solo datos estructurados, sino también la metadata de mapas o gráficos que hayan sido creados sobre el dataset en la plataforma web original.

### 4. Seguridad y Rendimiento
- **Soporte de App Tokens**: Socrata limita las llamadas anónimas de las IP. Una característica futura será permitir pasar un `App Token` a través de variables de entorno para aumentar masivamente los límites de cuota (Rate Limits) para usuarios frecuentes.
- **Caché en Memoria**: Implementar un sistema de caché temporal (ej. 5 minutos) para acelerar repetidas llamadas a `get_dataset_metadata` sobre los mismos recursos.
