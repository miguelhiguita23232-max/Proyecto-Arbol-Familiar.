"""
validators.py — Validaciones de Integridad del Árbol Genealógico
Detecta ciclos, incoherencias de fechas y límite de padres biológicos.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import FamilyTree


class FamilyTreeValidator:

    @staticmethod
    def validate_parent_child(
        tree: "FamilyTree", parent_id: str, child_id: str
    ) -> tuple[bool, str]:
        """
        Valida una relación padre-hijo antes de insertarla.

        Reglas aplicadas:
          1. Detección de ciclos: el padre no debe ser descendiente del hijo.
          2. Coherencia de fechas: diferencia mínima de 13 años.
          3. Máximo 2 padres biológicos por persona.
          4. Existencia de ambas personas en el árbol.

        Retorna: (válido: bool, mensaje_de_error: str)
        """
        # ── Existencia ────────────────────────────────────────────────────
        if parent_id not in tree.persons:
            return False, f"Padre con ID '{parent_id}' no existe en el árbol"
        if child_id not in tree.persons:
            return False, f"Hijo con ID '{child_id}' no existe en el árbol"

        # ── Regla 1: Detección de ciclos ──────────────────────────────────
        # Si el padre ya es descendiente del hijo, hay ciclo
        descendants_of_child = _dfs_descendants(tree, child_id)
        if parent_id in descendants_of_child:
            return False, "Error: Relación cíclica detectada. El padre ya es descendiente del hijo."

        # Evitar duplicado exacto
        if parent_id in tree.persons[child_id].parent_ids:
            return False, "Esta relación padre-hijo ya existe"

        # ── Regla 2: Coherencia de fechas ─────────────────────────────────
        parent = tree.persons[parent_id]
        child = tree.persons[child_id]

        if parent.birth_date and child.birth_date:
            from datetime import date
            parent_year = date.fromisoformat(parent.birth_date).year
            child_year = date.fromisoformat(child.birth_date).year
            diff = child_year - parent_year
            if diff < 13:
                return (
                    False,
                    f"Error: Diferencia de edad incoherente ({diff} años). "
                    "Se requieren mínimo 13 años entre padre e hijo.",
                )

        # ── Regla 3: Máximo 2 padres biológicos ──────────────────────────
        if len(tree.persons[child_id].parent_ids) >= 2:
            return False, "Error: El hijo ya tiene 2 padres biológicos registrados"

        return True, ""

    @staticmethod
    def validate_person_data(data: dict) -> tuple[bool, str]:
        """Valida los campos mínimos requeridos para crear una persona."""
        if not data.get("first_name", "").strip():
            return False, "El nombre es requerido"
        if not data.get("last_name", "").strip():
            return False, "El apellido es requerido"

        # Validar formato de fechas si se proporcionan
        from datetime import date
        for field in ("birth_date", "death_date"):
            val = data.get(field)
            if val:
                try:
                    date.fromisoformat(val)
                except ValueError:
                    return False, f"Formato de fecha inválido en '{field}'. Use YYYY-MM-DD."

        # Validar coherencia birth_date < death_date
        birth = data.get("birth_date")
        death = data.get("death_date")
        if birth and death:
            from datetime import date as dt
            if dt.fromisoformat(death) < dt.fromisoformat(birth):
                return False, "La fecha de defunción no puede ser anterior a la de nacimiento"

        return True, ""


def _dfs_descendants(tree: "FamilyTree", person_id: str) -> set[str]:
    """
    DFS iterativo para obtener todos los descendientes de una persona.
    Función auxiliar interna para la detección de ciclos en O(V+E).
    """
    visited: set[str] = set()
    stack: list[str] = [person_id]

    while stack:
        current = stack.pop()
        person = tree.persons.get(current)
        if not person:
            continue
        for child_id in person.children_ids:
            if child_id not in visited:
                visited.add(child_id)
                stack.append(child_id)

    return visited
