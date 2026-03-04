# colombia-opendata-mcp

Un servidor [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) que expone los conjuntos de datos del portal de datos abiertos de Colombia ([datos.gov.co](https://www.datos.gov.co/)) para que modelos de Inteligencia Artificial (como Claude) puedan consultarlos de manera interactiva.

Este proyecto utiliza el SDK oficial de Python `FastMCP` y se integra con la API de Socrata (SODA).

## 🚀 Características y Herramientas (Tools)

El servidor proporciona la IA con 3 herramientas principales:

1.  **`search_datasets(query: str, limit: int)`**
    *   **Propósito:** Buscar conjuntos de datos basándose en palabras clave (ej. "salud", "educación", "finanzas").
    *   **Retorna:** Una lista de resultados que incluye el nombre, descripción y el ID alfanumérico (`dataset_id` ej. `xxxx-xxxx`) necesario para consultas profundas.

2.  **`get_dataset_metadata(dataset_id: str)`**
    *   **Propósito:** Obtener el esquema o estructura de un conjunto de datos específico.
    *   **Retorna:** Los metadatos de las columnas, incluyendo los nombres de campo reales (`fieldName`), el tipo de dato subyacente y la descripción, lo que ayuda al LLM a saber qué campos se pueden utilizar para filtrar.

3.  **`query_dataset(dataset_id: str, select: str, where: str, limit: int, offset: int)`**
    *   **Propósito:** Extraer datos estructurados aplicando filtros básicos.
    *   **Retorna:** Filas de datos en formato JSON.

4.  **`aggregate_dataset(dataset_id: str, select: str, group_by: str, where: str)`**
    *   **Propósito:** Realizar operaciones matemáticas (sumas, promedios) agrupadas delegando el cálculo al servidor Socrata.
    *   **Retorna:** Resultados agregados rápidos sin descargar millones de filas.

5.  **`export_dataset_to_csv(dataset_id: str, limit: int, output_filename: str)`**
    *   **Propósito:** Descargar grandes volúmenes de datos usando paginación interna automática.
    *   **Retorna:** La ruta al archivo CSV local guardado para que la IA (o tú) lo analicen usando librerías como Pandas.

6.  **`build_graph_from_search` y `explore_related_datasets`**
    *   **Propósito:** Utiliza NetworkX local para relacionar conjuntos de datos a través de sus categorías y nombres de columnas (Knowledge Graph).

## 🛠️ Instalación y Uso

Este servidor puede ejecutarse de dos maneras: a través de un contenedor Docker (Recomendado) o con Python local.

### Opción 1: Usando Docker (Recomendado)

Construye la imagen Docker:

```bash
docker build -t colombia-opendata-mcp .
```

Agrega la siguiente configuración a tu cliente MCP (por ejemplo, en Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "colombia_opendata": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "colombia-opendata-mcp"
      ]
    }
  }
}
```

### Opción 2: Usando Python

Asegúrate de tener Python 3.10 o superior instalado.

1. Clona/descarga este repositorio.
2. Crea un entorno virtual e instala las dependencias:

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt mcp[cli]
```

3. Agrega la siguiente configuración a tu cliente MCP (ajusta la ruta absoluta según tu sistema):

```json
{
  "mcpServers": {
    "datos_gov_co": {
      "command": "/ruta/absoluta/al/proyecto/venv/Scripts/python.exe",
      "args": [
        "/ruta/absoluta/al/proyecto/mcp_server.py"
      ]
    }
  }
}
```

## 🔍 Inspección y Desarrollo

Si deseas probar las herramientas en el navegador a través de una UI gráfica antes de usarlo desde un agente de IA:

```bash
# Asumiendo que el entorno virtual está activo
mcp dev mcp_server.py
```

Esto levantará el **Inspector MCP** (usualmente en `http://localhost:5173`) donde podrás interactuar directamente con las herramientas.
