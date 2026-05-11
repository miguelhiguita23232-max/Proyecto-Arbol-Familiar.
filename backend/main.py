"""
main.py — API REST con FastAPI
Rutas para gestión de personas, relaciones, algoritmos y exportación.
"""

from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from models import FamilyTree, Person, Gender
from database import create_tables, get_db, save_tree_to_db, load_tree_from_db, delete_person_from_db
from validators import FamilyTreeValidator
from exporters import JsonExporter, GedcomExporter, PdfExporter

# ─────────────────────────────────────────────────────────────────────────
# Inicialización
# ─────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="FamilyTree Pro API",
    description="Sistema Gestor de Árboles Genealógicos — Estructuras de Datos",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FamilyTree en memoria — se carga desde SQLite al iniciar
_tree: FamilyTree = FamilyTree()


@app.on_event("startup")
def startup():
    create_tables()
    db = next(get_db())
    global _tree
    _tree = load_tree_from_db(db)


def get_tree() -> FamilyTree:
    return _tree


# ─────────────────────────────────────────────────────────────────────────
# Schemas Pydantic
# ─────────────────────────────────────────────────────────────────────────

class PersonCreate(BaseModel):
    first_name: str
    last_name: str
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    gender: Optional[str] = "O"
    birthplace: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class PersonUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    gender: Optional[str] = None
    birthplace: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class RelationshipRequest(BaseModel):
    parent_id: str
    child_id: str


class SpouseRequest(BaseModel):
    person_a_id: str
    person_b_id: str


# ─────────────────────────────────────────────────────────────────────────
# ENDPOINTS — Personas
# ─────────────────────────────────────────────────────────────────────────

@app.get("/persons", tags=["Personas"])
def list_persons(tree: FamilyTree = Depends(get_tree)):
    """Lista todas las personas del árbol."""
    return [p.to_dict() for p in tree.persons.values()]


@app.post("/persons", tags=["Personas"], status_code=201)
def create_person(
    data: PersonCreate,
    db: Session = Depends(get_db),
    tree: FamilyTree = Depends(get_tree),
):
    """Agrega una nueva persona al árbol (aparece como nodo huérfano)."""
    valid, error = FamilyTreeValidator.validate_person_data(data.model_dump())
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    person = Person(
        first_name=data.first_name,
        last_name=data.last_name,
        birth_date=data.birth_date,
        death_date=data.death_date,
        gender=Gender(data.gender or "O"),
        birthplace=data.birthplace,
        photo_url=data.photo_url,
        notes=data.notes,
    )
    tree.add_person(person)
    save_tree_to_db(tree, db)
    return person.to_dict()


@app.get("/persons/{person_id}", tags=["Personas"])
def get_person(person_id: str, tree: FamilyTree = Depends(get_tree)):
    person = tree.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return person.to_dict()


@app.put("/persons/{person_id}", tags=["Personas"])
def update_person(
    person_id: str,
    data: PersonUpdate,
    db: Session = Depends(get_db),
    tree: FamilyTree = Depends(get_tree),
):
    """Edita los campos biográficos de una persona existente."""
    person = tree.get_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    valid, error = FamilyTreeValidator.validate_person_data({**person.to_dict(), **update_data})
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    for field, value in update_data.items():
        if field == "gender":
            setattr(person, field, Gender(value))
        else:
            setattr(person, field, value)

    save_tree_to_db(tree, db)
    return person.to_dict()


@app.delete("/persons/{person_id}", tags=["Personas"])
def delete_person(
    person_id: str,
    db: Session = Depends(get_db),
    tree: FamilyTree = Depends(get_tree),
):
    """Elimina una persona y actualiza todas las relaciones asociadas."""
    if not tree.remove_person(person_id):
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    delete_person_from_db(person_id, db)
    save_tree_to_db(tree, db)
    return {"message": "Persona eliminada correctamente"}


@app.get("/persons/search/{query}", tags=["Personas"])
def search_persons(query: str, tree: FamilyTree = Depends(get_tree)):
    """Busca personas por nombre, apellido o ID."""
    results = tree.search_persons(query)
    return [p.to_dict() for p in results]


# ─────────────────────────────────────────────────────────────────────────
# ENDPOINTS — Relaciones
# ─────────────────────────────────────────────────────────────────────────

@app.post("/relations/parent-child", tags=["Relaciones"])
def add_parent_child(
    data: RelationshipRequest,
    db: Session = Depends(get_db),
    tree: FamilyTree = Depends(get_tree),
):
    """Establece relación padre → hijo con todas las validaciones."""
    result = tree.add_parent_child(data.parent_id, data.child_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    save_tree_to_db(tree, db)
    return {"message": "Relación padre-hijo creada correctamente"}


@app.post("/relations/spouse", tags=["Relaciones"])
def add_spouse(
    data: SpouseRequest,
    db: Session = Depends(get_db),
    tree: FamilyTree = Depends(get_tree),
):
    """Registra relación de cónyuge en el grafo auxiliar bidireccional."""
    result = tree.add_spouse(data.person_a_id, data.person_b_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    save_tree_to_db(tree, db)
    return {"message": "Relación de cónyuge registrada"}


@app.get("/persons/{person_id}/siblings", tags=["Relaciones"])
def get_siblings(person_id: str, tree: FamilyTree = Depends(get_tree)):
    """Retorna hermanos inferidos (padres comunes). No almacenado directamente."""
    if person_id not in tree.persons:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    sibling_ids = tree.get_siblings(person_id)
    return {
        "person_id": person_id,
        "siblings": [tree.persons[s].to_dict() for s in sibling_ids if s in tree.persons],
    }


# ─────────────────────────────────────────────────────────────────────────
# ENDPOINTS — Algoritmos
# ─────────────────────────────────────────────────────────────────────────

@app.get("/algorithms/ancestors/{person_id}", tags=["Algoritmos"])
def get_ancestors(person_id: str, tree: FamilyTree = Depends(get_tree)):
    """DFS ascendente: retorna todos los ancestros de una persona."""
    if person_id not in tree.persons:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    ancestor_ids = tree.get_ancestors(person_id)
    return {
        "person_id": person_id,
        "person_name": tree.persons[person_id].full_name(),
        "total": len(ancestor_ids),
        "ancestors": [tree.persons[a].to_dict() for a in ancestor_ids if a in tree.persons],
    }


@app.get("/algorithms/descendants/{person_id}", tags=["Algoritmos"])
def get_descendants(person_id: str, tree: FamilyTree = Depends(get_tree)):
    """DFS descendente: retorna todos los descendientes de una persona."""
    if person_id not in tree.persons:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    desc_ids = tree.get_descendants(person_id)
    return {
        "person_id": person_id,
        "person_name": tree.persons[person_id].full_name(),
        "total": len(desc_ids),
        "descendants": [tree.persons[d].to_dict() for d in desc_ids if d in tree.persons],
    }


@app.get("/algorithms/generations", tags=["Algoritmos"])
def get_generations(
    root_id: Optional[str] = None,
    tree: FamilyTree = Depends(get_tree),
):
    """BFS por niveles: agrupa personas por generación desde la raíz."""
    generations = tree.get_generations(root_id)
    return {
        "total_generations": len(generations),
        "generations": {
            str(level): [
                tree.persons[pid].to_dict()
                for pid in ids
                if pid in tree.persons
            ]
            for level, ids in generations.items()
        },
    }


@app.get("/algorithms/lca", tags=["Algoritmos"])
def find_lca(
    person_a_id: str,
    person_b_id: str,
    tree: FamilyTree = Depends(get_tree),
):
    """Encuentra el Ancestro Común Más Cercano (LCA) entre dos personas."""
    for pid in [person_a_id, person_b_id]:
        if pid not in tree.persons:
            raise HTTPException(status_code=404, detail=f"Persona '{pid}' no encontrada")

    result = tree.find_lca(person_a_id, person_b_id)
    if not result:
        return {"lca": None, "message": "Sin ancestro común en el árbol registrado"}

    lca_id, prof_a, prof_b = result
    lca_person = tree.persons.get(lca_id)
    return {
        "lca": lca_person.to_dict() if lca_person else None,
        "depth_from_a": prof_a,
        "depth_from_b": prof_b,
    }


@app.get("/algorithms/relationship", tags=["Algoritmos"])
def get_relationship(
    person_a_id: str,
    person_b_id: str,
    tree: FamilyTree = Depends(get_tree),
):
    """Calcula y describe el grado de parentesco entre dos personas."""
    for pid in [person_a_id, person_b_id]:
        if pid not in tree.persons:
            raise HTTPException(status_code=404, detail=f"Persona '{pid}' no encontrada")

    from algorithms import TreeAlgorithms
    path = TreeAlgorithms.get_path_between(tree, person_a_id, person_b_id)

    return {
        "person_a": tree.persons[person_a_id].to_dict(),
        "person_b": tree.persons[person_b_id].to_dict(),
        "relationship": tree.get_relationship(person_a_id, person_b_id),
        "path": path,   # IDs para resaltado visual en D3
    }


@app.get("/stats", tags=["Estadísticas"])
def get_stats(tree: FamilyTree = Depends(get_tree)):
    """Retorna estadísticas generales del árbol familiar."""
    return tree.stats()


# ─────────────────────────────────────────────────────────────────────────
# ENDPOINTS — Árbol completo para D3.js
# ─────────────────────────────────────────────────────────────────────────

@app.get("/tree", tags=["Visualización"])
def get_tree_for_d3(tree: FamilyTree = Depends(get_tree)):
    """
    Retorna el árbol en formato de nodos y enlaces para D3.js.
    Incluye tanto aristas padre-hijo como aristas de cónyuge.
    """
    nodes = [p.to_dict() for p in tree.persons.values()]
    links = []

    # Aristas del árbol N-ario (padre → hijo)
    for person in tree.persons.values():
        for child_id in person.children_ids:
            links.append({"source": person.id, "target": child_id, "type": "parent-child"})

    # Aristas del grafo de cónyuges (no dirigidas)
    added_spouse_links: set[str] = set()
    for id_a, neighbors in tree.spouse_graph.items():
        for id_b in neighbors:
            key = "_".join(sorted([id_a, id_b]))
            if key not in added_spouse_links:
                added_spouse_links.add(key)
                links.append({"source": id_a, "target": id_b, "type": "spouse"})

    return {
        "nodes": nodes,
        "links": links,
        "roots": tree.roots,
    }


# ─────────────────────────────────────────────────────────────────────────
# ENDPOINTS — Importación / Exportación
# ─────────────────────────────────────────────────────────────────────────

@app.get("/export/json", tags=["Exportación"])
def export_json(tree: FamilyTree = Depends(get_tree)):
    """Exporta el árbol completo en formato JSON."""
    return tree.export_json()


@app.post("/import/json", tags=["Importación"])
def import_json(
    payload: dict,
    db: Session = Depends(get_db),
    tree: FamilyTree = Depends(get_tree),
):
    """Importa un árbol desde JSON. Reemplaza el árbol actual."""
    try:
        tree.import_json(payload)
        save_tree_to_db(tree, db)
        return {"message": f"Importación exitosa. {len(tree.persons)} personas cargadas."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al importar: {str(e)}")


@app.get("/export/gedcom", tags=["Exportación"])
def export_gedcom(tree: FamilyTree = Depends(get_tree)):
    """Exporta el árbol en formato GEDCOM 5.5.1."""
    content = GedcomExporter.export(tree)
    return Response(content=content, media_type="text/plain", headers={
        "Content-Disposition": "attachment; filename=family_tree.ged"
    })


@app.get("/export/pdf", tags=["Exportación"])
def export_pdf(tree: FamilyTree = Depends(get_tree)):
    """Exporta un reporte PDF con la lista de personas y estadísticas."""
    pdf_bytes = PdfExporter.export(tree)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=family_tree_report.pdf"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
