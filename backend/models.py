"""
models.py — Clases Person y FamilyTree
Estructura de datos principal: Árbol N-ario + Grafo auxiliar de cónyuges
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import date
from enum import Enum
import uuid


class Gender(str, Enum):
    M = "M"
    F = "F"
    O = "O"


@dataclass
class Person:
    first_name: str
    last_name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    birth_date: Optional[str] = None       # formato "YYYY-MM-DD"
    death_date: Optional[str] = None
    gender: Gender = Gender.O
    birthplace: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    # ── Relaciones (listas de IDs) ──────────────────────────────────────
    parent_ids: list[str] = field(default_factory=list)     # máx. 2
    children_ids: list[str] = field(default_factory=list)
    spouse_ids: list[str] = field(default_factory=list)

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def age(self) -> Optional[int]:
        if not self.birth_date:
            return None
        birth = date.fromisoformat(self.birth_date)
        end = date.fromisoformat(self.death_date) if self.death_date else date.today()
        return end.year - birth.year - ((end.month, end.day) < (birth.month, birth.day))

    def is_alive(self) -> bool:
        return self.death_date is None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "birth_date": self.birth_date,
            "death_date": self.death_date,
            "gender": self.gender.value if isinstance(self.gender, Gender) else self.gender,
            "birthplace": self.birthplace,
            "photo_url": self.photo_url,
            "notes": self.notes,
            "parent_ids": self.parent_ids,
            "children_ids": self.children_ids,
            "spouse_ids": self.spouse_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Person":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            first_name=data["first_name"],
            last_name=data["last_name"],
            birth_date=data.get("birth_date"),
            death_date=data.get("death_date"),
            gender=Gender(data.get("gender", "O")),
            birthplace=data.get("birthplace"),
            photo_url=data.get("photo_url"),
            notes=data.get("notes"),
            parent_ids=data.get("parent_ids", []),
            children_ids=data.get("children_ids", []),
            spouse_ids=data.get("spouse_ids", []),
        )


class FamilyTree:
    """
    Motor principal del árbol genealógico.

    Estructura de datos interna:
      - persons       : dict[str → Person]   → Hashtable O(1), árbol N-ario
      - spouse_graph  : dict[str → list[str]] → Grafo no dirigido de cónyuges
      - roots         : list[str]             → Personas sin padre registrado
    """

    def __init__(self):
        # ESTRUCTURA 1: Hashtable principal (árbol N-ario implícito via parent/children ids)
        self.persons: dict[str, Person] = {}
        # ESTRUCTURA 2: Grafo auxiliar no dirigido de cónyuges
        self.spouse_graph: dict[str, list[str]] = {}
        # Lista de raíces (nodos sin padres)
        self.roots: list[str] = []

    # ─────────────────────────────────────────────────────────────────────
    # GESTIÓN DE PERSONAS
    # ─────────────────────────────────────────────────────────────────────

    def add_person(self, person: Person) -> None:
        """Agrega una persona al árbol. O(1) en la hashtable."""
        self.persons[person.id] = person
        self.spouse_graph[person.id] = []
        # Si no tiene padres, es raíz del árbol
        if not person.parent_ids:
            self.roots.append(person.id)

    def remove_person(self, person_id: str) -> bool:
        """Elimina una persona y actualiza todas las relaciones asociadas."""
        if person_id not in self.persons:
            return False
        person = self.persons[person_id]

        # Limpiar referencias en padres
        for pid in person.parent_ids:
            if pid in self.persons:
                self.persons[pid].children_ids = [
                    c for c in self.persons[pid].children_ids if c != person_id
                ]

        # Limpiar referencias en hijos
        for cid in person.children_ids:
            if cid in self.persons:
                self.persons[cid].parent_ids = [
                    p for p in self.persons[cid].parent_ids if p != person_id
                ]
                # El hijo se convierte en raíz si queda sin padres
                if not self.persons[cid].parent_ids and cid not in self.roots:
                    self.roots.append(cid)

        # Limpiar del grafo de cónyuges
        for sid in self.spouse_graph.get(person_id, []):
            if sid in self.spouse_graph:
                self.spouse_graph[sid] = [x for x in self.spouse_graph[sid] if x != person_id]

        del self.persons[person_id]
        del self.spouse_graph[person_id]
        self.roots = [r for r in self.roots if r != person_id]
        return True

    def get_person(self, person_id: str) -> Optional[Person]:
        return self.persons.get(person_id)

    def search_persons(self, query: str) -> list[Person]:
        """Búsqueda lineal O(n) por nombre, apellido o ID."""
        q = query.lower()
        return [
            p for p in self.persons.values()
            if q in p.first_name.lower()
            or q in p.last_name.lower()
            or q in p.id.lower()
        ]

    # ─────────────────────────────────────────────────────────────────────
    # GESTIÓN DE RELACIONES
    # ─────────────────────────────────────────────────────────────────────

    def add_parent_child(self, parent_id: str, child_id: str) -> dict:
        """
        Establece relación padre → hijo en el árbol N-ario.
        Valida ciclos, fechas y límite de 2 padres antes de insertar.
        """
        from validators import FamilyTreeValidator
        valid, error = FamilyTreeValidator.validate_parent_child(self, parent_id, child_id)
        if not valid:
            return {"success": False, "error": error}

        parent = self.persons[parent_id]
        child = self.persons[child_id]

        parent.children_ids.append(child_id)
        child.parent_ids.append(parent_id)

        # Si el hijo era raíz, ya deja de serlo
        if child_id in self.roots:
            self.roots.remove(child_id)

        return {"success": True}

    def add_spouse(self, id_a: str, id_b: str) -> dict:
        """
        Agrega relación de cónyuge en el grafo auxiliar bidireccional.
        No permite relación si ya existe vínculo padre-hijo entre ellos.
        """
        if id_a not in self.persons or id_b not in self.persons:
            return {"success": False, "error": "Persona no encontrada"}

        a = self.persons[id_a]
        b = self.persons[id_b]

        if id_b in a.parent_ids or id_a in b.parent_ids:
            return {"success": False, "error": "No se puede registrar cónyuge con relación padre-hijo directa"}

        if id_b not in self.spouse_graph[id_a]:
            self.spouse_graph[id_a].append(id_b)
            a.spouse_ids.append(id_b)

        if id_a not in self.spouse_graph[id_b]:
            self.spouse_graph[id_b].append(id_a)
            b.spouse_ids.append(id_a)

        return {"success": True}

    def get_siblings(self, person_id: str) -> list[str]:
        """Hermanos inferidos: personas con al menos un padre en común. No almacenado directamente."""
        person = self.persons.get(person_id)
        if not person:
            return []
        siblings = set()
        for pid in person.parent_ids:
            parent = self.persons.get(pid)
            if parent:
                for cid in parent.children_ids:
                    if cid != person_id:
                        siblings.add(cid)
        return list(siblings)

    # ─────────────────────────────────────────────────────────────────────
    # ALGORITMOS DE ANÁLISIS — Árboles y Grafos
    # ─────────────────────────────────────────────────────────────────────

    def get_ancestors(self, person_id: str) -> list[str]:
        """
        DFS iterativo ASCENDENTE sobre el árbol N-ario.
        Recorre padre → abuelo → bisabuelo → …
        Complejidad: O(V+E) donde V=nodos visitados, E=aristas padre-hijo
        """
        from algorithms import TreeAlgorithms
        return TreeAlgorithms.get_ancestors(self, person_id)

    def get_descendants(self, person_id: str) -> list[str]:
        """
        DFS iterativo DESCENDENTE sobre el árbol N-ario.
        Recorre hijo → nieto → bisnieto → …
        """
        from algorithms import TreeAlgorithms
        return TreeAlgorithms.get_descendants(self, person_id)

    def get_generations(self, root_id: str = None) -> dict[int, list[str]]:
        """
        BFS por niveles para agrupar personas por generación.
        Usa una cola. Cada nivel = una generación familiar.
        """
        from algorithms import TreeAlgorithms
        start = root_id or (self.roots[0] if self.roots else None)
        if not start:
            return {}
        return TreeAlgorithms.get_generations(self, start)

    def find_lca(self, id_a: str, id_b: str) -> Optional[tuple]:
        """
        Encuentra el Ancestro Común Más Cercano (LCA).
        Retorna (lca_id, profundidad_desde_A, profundidad_desde_B)
        """
        from algorithms import TreeAlgorithms
        return TreeAlgorithms.find_lca(self, id_a, id_b)

    def get_relationship(self, id_a: str, id_b: str) -> str:
        """Calcula y describe el grado de parentesco entre dos personas."""
        from algorithms import TreeAlgorithms
        return TreeAlgorithms.get_relationship(self, id_a, id_b)

    # ─────────────────────────────────────────────────────────────────────
    # IMPORTACIÓN / EXPORTACIÓN
    # ─────────────────────────────────────────────────────────────────────

    def export_json(self) -> dict:
        from datetime import datetime
        return {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "persons": [p.to_dict() for p in self.persons.values()],
            "spouses": [
                [id_a, id_b]
                for id_a, neighbors in self.spouse_graph.items()
                for id_b in neighbors
                if id_a < id_b   # evitar duplicados en grafo no dirigido
            ],
        }

    def import_json(self, data: dict) -> None:
        self.persons.clear()
        self.spouse_graph.clear()
        self.roots.clear()

        for p_data in data.get("persons", []):
            person = Person.from_dict(p_data)
            self.persons[person.id] = person
            self.spouse_graph[person.id] = []

        # Reconstruir grafo de cónyuges
        for id_a, id_b in data.get("spouses", []):
            if id_a in self.spouse_graph and id_b not in self.spouse_graph[id_a]:
                self.spouse_graph[id_a].append(id_b)
            if id_b in self.spouse_graph and id_a not in self.spouse_graph[id_b]:
                self.spouse_graph[id_b].append(id_a)

        # Recalcular raíces
        self.roots = [
            pid for pid, p in self.persons.items() if not p.parent_ids
        ]

    def stats(self) -> dict:
        total = len(self.persons)
        alive = sum(1 for p in self.persons.values() if p.is_alive())
        generations = self.get_generations()
        return {
            "total_persons": total,
            "alive": alive,
            "deceased": total - alive,
            "total_generations": len(generations),
            "roots": len(self.roots),
            "total_relationships": sum(
                len(p.children_ids) for p in self.persons.values()
            ),
        }
