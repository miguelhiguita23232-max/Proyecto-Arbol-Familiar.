# 🌳 FamilyTree Pro

**Sistema Gestor de Árboles Genealógicos Interactivos**  
Proyecto de Estructuras de Datos — Entregable 2

> Implementa un árbol N-ario genealógico + grafo auxiliar de cónyuges con algoritmos DFS, BFS y LCA propios.

---

## 📁 Estructura del Proyecto

```
familytree-pro/
├── backend/
│   ├── main.py          # API REST con FastAPI — 15+ endpoints
│   ├── models.py        # Clases Person y FamilyTree (árbol N-ario + grafo)
│   ├── algorithms.py    # DFS ascendente/descendente, BFS, LCA, parentesco
│   ├── validators.py    # Detección de ciclos, fechas, límite de padres
│   ├── database.py      # SQLAlchemy + SQLite — persistencia local
│   ├── exporters.py     # Exportadores JSON, GEDCOM 5.5.1, PDF (ReportLab)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.tsx                    # Componente raíz
│       ├── api/client.ts             # Cliente Axios con tipos
│       ├── hooks/useFamilyTree.ts    # Estado global y llamadas a API
│       └── components/
│           ├── TreeView.tsx          # Visualización D3.js
│           └── index.tsx             # PersonCard, PersonForm, SearchPanel, StatsPanel
└── data/
    └── sample_family.json            # Demo: 4 generaciones, 14 personas
```

---

## 🚀 Instalación y Ejecución

### Backend (Python 3.11+)

```bash
cd backend
pip install -r requirements.txt
python main.py
# API disponible en: http://localhost:8000
# Documentación Swagger: http://localhost:8000/docs
```

### Frontend (Node 18+)

```bash
cd frontend
npm install
npm run dev
# App disponible en: http://localhost:5173
```

### Cargar datos de ejemplo

```bash
curl -X POST http://localhost:8000/import/json \
  -H "Content-Type: application/json" \
  -d @data/sample_family.json
```

---

## 🌲 Estructuras de Datos Implementadas

### 1. Árbol N-ario (estructura principal)

```python
# En models.py — clase FamilyTree
persons: dict[str, Person]   # Hashtable O(1) — árbol N-ario implícito
roots: list[str]             # IDs de nodos raíz (sin padres)
```

Cada `Person` almacena `parent_ids` (máx. 2) y `children_ids` (N hijos), 
formando el árbol N-ario a través de referencias en la hashtable.

### 2. Grafo Auxiliar de Cónyuges

```python
# En models.py — clase FamilyTree  
spouse_graph: dict[str, list[str]]   # Grafo no dirigido, O(1) por nodo
```

Las relaciones matrimoniales no son jerárquicas, por lo que se modelan 
como grafo bidireccional separado del árbol.

---

## 🔬 Algoritmos Implementados

### DFS Ascendente — `algorithms.py::get_ancestors()`
Recorre el árbol hacia arriba (hijo → padres → abuelos).  
**Complejidad:** O(V+E)

### DFS Descendente — `algorithms.py::get_descendants()`
Recorre el árbol hacia abajo (padre → hijos → nietos).  
**Complejidad:** O(V+E)

### BFS por Niveles — `algorithms.py::get_generations()`
Agrupa personas por generación usando cola (deque).  
**Complejidad:** O(V+E)

### LCA — `algorithms.py::find_lca()`
Ancestro Común Más Cercano: DFS desde A + BFS desde B.  
**Complejidad:** O(V+E)

### Cálculo de Parentesco — `algorithms.py::get_relationship()`
Usa el LCA y las profundidades para describir la relación en texto.

### Detección de Ciclos — `validators.py`
Antes de insertar padre-hijo, verifica que el padre no sea descendiente del hijo.

---

## 🌐 API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/persons` | Lista todas las personas |
| POST | `/persons` | Crea nueva persona |
| PUT | `/persons/{id}` | Edita persona |
| DELETE | `/persons/{id}` | Elimina persona |
| GET | `/persons/search/{q}` | Busca por nombre/apellido/ID |
| POST | `/relations/parent-child` | Establece relación padre-hijo |
| POST | `/relations/spouse` | Establece relación cónyuge |
| GET | `/algorithms/ancestors/{id}` | DFS ascendente |
| GET | `/algorithms/descendants/{id}` | DFS descendente |
| GET | `/algorithms/generations` | BFS por niveles |
| GET | `/algorithms/lca?a=&b=` | Ancestro Común Más Cercano |
| GET | `/algorithms/relationship?a=&b=` | Grado de parentesco |
| GET | `/tree` | Datos para visualización D3.js |
| GET | `/export/json` | Exportar JSON |
| GET | `/export/gedcom` | Exportar GEDCOM 5.5.1 |
| GET | `/export/pdf` | Exportar PDF |
| POST | `/import/json` | Importar desde JSON |

---

## 👥 Autores

- Miguel Angel Higuita Cardona  
- Eyfer Rodríguez Quintero  
- Miguel Ángel Grajales  

**Curso:** Desarrollo del pensamiento Logico y analitico 3  
**Stack:** Python · FastAPI · React · TypeScript · D3.js · SQLite
