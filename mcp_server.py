from mcp.server.fastmcp import FastMCP
import httpx
import networkx as nx
import json
import csv
import os
from typing import Any, Dict, List, Optional

# Initialize FastMCP server
mcp = FastMCP("colombia-opendata-mcp")

BASE_URL = "https://www.datos.gov.co"
GRAPH_FILE = "datasets_graph.json"

def load_graph() -> nx.Graph:
    if os.path.exists(GRAPH_FILE):
        try:
            with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return nx.node_link_graph(data)
        except Exception as e:
            print(f"Error loading graph: {e}")
    return nx.Graph()

def save_graph(g: nx.Graph):
    try:
        data = nx.node_link_data(g)
        with open(GRAPH_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving graph: {e}")

local_graph = load_graph()

def _add_dataset_to_graph(dataset_id: str, name: str, category: str, columns: List[Dict[str, Any]]):
    """Helper interno para alimentar el grafo con los metadatos de un dataset."""
    local_graph.add_node(dataset_id, type="Dataset", name=name)
    
    if category:
        local_graph.add_node(category, type="Category")
        local_graph.add_edge(dataset_id, category, relation="IN_CATEGORY")
        
    for col in columns:
        col_name = col.get("fieldName", "")
        if col_name:
            local_graph.add_node(col_name, type="Column")
            local_graph.add_edge(dataset_id, col_name, relation="HAS_COLUMN")
            
    save_graph(local_graph)

BASE_URL = "https://www.datos.gov.co"

@mcp.tool()
async def search_datasets(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Busca conjuntos de datos en datos.gov.co (Socrata API).
    
    Args:
        query: Término de búsqueda (ej. 'salud', 'educación').
        limit: Número máximo de resultados a devolver.
    """
    url = f"{BASE_URL}/api/catalog/v1"
    params = {
        "q": query,
        "limit": limit
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            resource = item.get("resource", {})
            results.append({
                "id": resource.get("id"),
                "name": resource.get("name"),
                "description": resource.get("description"),
                "type": resource.get("type"),
                "updatedAt": resource.get("updatedAt"),
                "page_url": resource.get("permalink")
            })
        return results

@mcp.tool()
async def get_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    """
    Obtiene los metadatos y la estructura (columnas) de un conjunto de datos específico usando su ID.
    
    Args:
        dataset_id: El identificador alfanumérico único del dataset (ej. 'xxxx-xxxx').
    """
    url = f"{BASE_URL}/api/views/{dataset_id}.json"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            columns = []
            for col in data.get("columns", []):
                columns.append({
                    "id": col.get("id"),
                    "name": col.get("name"),
                    "fieldName": col.get("fieldName"),
                    "dataTypeName": col.get("dataTypeName"),
                    "description": col.get("description", "")
                })
                
            result = {
                "id": data.get("id"),
                "name": data.get("name"),
                "description": data.get("description", ""),
                "category": data.get("category", ""),
                "columns": columns
            }
            
            _add_dataset_to_graph(result["id"], result["name"], result["category"], result["columns"])
            return result
        except httpx.HTTPStatusError as e:
            return {"error": f"Error al obtener metadatos: {str(e)}"}

@mcp.tool()
async def query_dataset(dataset_id: str, select: Optional[str] = None, where: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Consulta los datos de un dataset utilizando la API SODA (Socrata Open Data API). Usa SoQL para filtros.
    
    Args:
        dataset_id: El identificador único del dataset (ej. 'xxxx-xxxx').
        select: (Opcional) Campos a seleccionar, separados por coma. Si se omite, trae todos.
        where: (Opcional) Condición de filtrado en formato SoQL (ej. "departamento = 'Antioquia'").
        limit: Número máximo de registros a devolver.
        offset: Desplazamiento para paginación.
    """
    url = f"{BASE_URL}/resource/{dataset_id}.json"
    
    params = {
        "$limit": limit,
        "$offset": offset
    }
    
    if select:
        params["$select"] = select
    if where:
        params["$where"] = where
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            content = e.response.text if hasattr(e, 'response') else ""
            return [{"error": f"Error al consultar datos: {str(e)}", "details": content}]

@mcp.tool()
async def aggregate_dataset(dataset_id: str, select: str = None, group_by: str = None, where: str = None) -> List[Dict[str, Any]]:
    """
    Agrupa los datos y calcula operaciones estadísticas (suma, promedio, cuenta) directamente en la API de Socrata.
    
    Args:
        dataset_id: El identificador único del dataset.
        select: Obligatorio. Qué calcular y devolver. Ejemplo: 'departamento, sum(presupuesto) as total, count(*) as cantidad'.
        group_by: Obligatorio. Por qué columna agrupar. Ejemplo: 'departamento'.
        where: (Opcional) Un filtro previo a la agrupación. Ejemplo: "año = '2023'".
    """
    if not select or not group_by:
        return [{"error": "Tanto 'select' como 'group_by' son parámetros obligatorios para la agregación."}]
        
    url = f"{BASE_URL}/resource/{dataset_id}.json"
    params = {
        "$select": select,
        "$group": group_by,
        "$limit": 50000 # Límite alto para resultados agregados que suelen ser pocos
    }
    if where:
        params["$where"] = where
        
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            content = e.response.text if hasattr(e, 'response') else ""
            return [{"error": f"Error al agrupar datos: {str(e)}", "details": content}]
        except httpx.ReadTimeout:
            return [{"error": "Timeout realizando la agregación, la consulta es demasiado compleja o pesada."}]

@mcp.tool()
async def export_dataset_to_csv(dataset_id: str, limit: int = 100000, output_filename: str = None) -> str:
    """
    Descarga registros de un dataset paginándolos, y los guarda en un archivo CSV local para análisis offline pesados (ej. usando Pandas).
    
    Args:
        dataset_id: El identificador único del dataset.
        limit: Cantidad total de filas máximas a exportar.
        output_filename: (Opcional) Nombre del archivo. Por defecto será 'dataset_[id].csv'.
    """
    if not output_filename:
        output_filename = f"dataset_{dataset_id}.csv"
        
    url = f"{BASE_URL}/resource/{dataset_id}.json"
    page_size = 10000
    offset = 0
    total_downloaded = 0
    
    try:
        # Abrir archivo para escribir por tramos (streaming simulado)
        with open(output_filename, mode='w', newline='', encoding='utf-8') as f:
            writer = None
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                while total_downloaded < limit:
                    current_limit = min(page_size, limit - total_downloaded)
                    params = {
                        "$limit": current_limit,
                        "$offset": offset
                    }
                    
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data:
                        break # No hay más datos
                        
                    # Inicializar el writer y el header si es la primera vez
                    if writer is None:
                        # Extraer todas las columnas posibles (Socrata a veces omite nulos, así que hacemos unión de keys de la primera página)
                        fieldnames = set()
                        for row in data:
                            fieldnames.update(row.keys())
                        fieldnames = list(fieldnames)
                        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                        writer.writeheader()
                        
                    writer.writerows(data)
                    total_downloaded += len(data)
                    offset += current_limit
                    
                    # Si me devolvió menos del límite que pedí, significa que ya acabé
                    if len(data) < current_limit:
                        break
                        
        return f"Éxito: Se exportaron {total_downloaded} filas al archivo local '{output_filename}' exitosamente."
    except Exception as e:
        return f"Error exportando a CSV: {str(e)}"

@mcp.tool()
async def build_graph_from_search(query: str, limit: int = 5) -> str:
    """
    Busca datasets e incorpora automáticamente todos sus metadatos (columnas y categorías) en el grafo local de conocimiento.
    Util para investigar cruces de datos para un tema particular sin pedir los metadatos uno por uno.
    
    Args:
        query: Término de búsqueda (ej. 'movilidad').
        limit: Cuántos datasets incluir en el grafo simultáneamente.
    """
    datasets = await search_datasets(query, limit=limit)
    added = 0
    for ds in datasets:
        ds_id = ds.get("id")
        if ds_id:
            await get_dataset_metadata(ds_id)
            added += 1
            
    return f"Se incorporaron metadatos estructurales de {added} conjuntos de datos asociados a '{query}' para relacionamiento local."

@mcp.tool()
async def explore_related_datasets(dataset_id: str) -> Dict[str, Any]:
    """
    Analiza el grafo de relaciones locales para encontrar otros conjuntos de datos que compartan la misma 
    categoría o que tengan el mismo nombre en sus columnas clave que el dataset dado.
    
    Args:
        dataset_id: El identificador único del dataset base (ej. 'xxxx-xxxx').
    """
    if not local_graph.has_node(dataset_id):
        return {"error": f"Dataset {dataset_id} no está en el grafo local. Intente obtener primero sus metadatos usando get_dataset_metadata."}
        
    related_by_category = []
    related_by_columns = {}
    
    # Buscar vecinos
    neighbors = list(local_graph.neighbors(dataset_id))
    for neighbor in neighbors:
        node_attr = local_graph.nodes[neighbor]
        n_type = node_attr.get("type")
        
        # Si el dataset pertenece a esta categoría, mirar qué otros datasets la comparten
        if n_type == "Category":
            category_peers = [n for n in local_graph.neighbors(neighbor) if local_graph.nodes[n].get("type") == "Dataset" and n != dataset_id]
            related_by_category.extend([{"dataset_id": cp, "dataset_name": local_graph.nodes[cp].get("name", ""), "category": neighbor} for cp in category_peers])
            
        # Si el dataset tiene esta columna, mirar qué otros datasets la usan
        elif n_type == "Column":
            column_peers = [n for n in local_graph.neighbors(neighbor) if local_graph.nodes[n].get("type") == "Dataset" and n != dataset_id]
            for cp in column_peers:
                if cp not in related_by_columns:
                    related_by_columns[cp] = {"dataset_id": cp, "dataset_name": local_graph.nodes[cp].get("name", ""), "shared_columns": []}
                related_by_columns[cp]["shared_columns"].append(neighbor)
                
    # Parse dict to list
    by_cols_list = list(related_by_columns.values())
    
    return {
        "dataset_base": dataset_id,
        "base_name": local_graph.nodes[dataset_id].get("name", ""),
        "related_by_category": related_by_category,
        "related_by_columns": by_cols_list
    }

if __name__ == "__main__":
    # Start the FastMCP server
    mcp.run()
