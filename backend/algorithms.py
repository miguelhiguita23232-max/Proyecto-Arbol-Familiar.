"""
algorithms.py — Algoritmos sobre el Árbol Genealógico
Implementa: DFS ascendente/descendente, BFS por generaciones, LCA, parentesco
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from collections import deque

if TYPE_CHECKING:
    from models import FamilyTree


class TreeAlgorithms:
    """
    Colección de algoritmos sobre el árbol N-ario genealógico.

    Todas las funciones reciben la instancia de FamilyTree para
    navegar la hashtable persons y el spouse_graph.
    """

    # ─────────────────────────────────────────────────────────────────────
    # DFS ASCENDENTE — Obtener todos los ancestros
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_ancestors(tree: "FamilyTree", person_id: str) -> list[str]:
        """
        DFS iterativo hacia arriba en el árbol N-ario.
        Usa una pila (stack) para simular la recursión.

        Algoritmo:
          1. Apilar persona inicial.
          2. Desapilar → recorrer sus parent_ids.
          3. Si el padre no fue visitado, agregarlo a ancestros y apilarlo.
          4. Repetir hasta vaciar la pila.

        Complejidad: O(V+E) — V nodos visitados, E aristas padre-hijo
        """
        visited: set[str] = set()
        stack: list[str] = [person_id]
        ancestors: list[str] = []

        while stack:
            current = stack.pop()
            person = tree.persons.get(current)
            if not person:
                continue

            for parent_id in person.parent_ids:
                if parent_id not in visited:
                    visited.add(parent_id)
                    ancestors.append(parent_id)
                    stack.append(parent_id)

        return ancestors

    # ─────────────────────────────────────────────────────────────────────
    # DFS DESCENDENTE — Obtener todos los descendientes
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_descendants(tree: "FamilyTree", person_id: str) -> list[str]:
        """
        DFS iterativo hacia abajo en el árbol N-ario.
        Estructura idéntica al DFS ascendente pero navega children_ids.

        Algoritmo:
          1. Apilar persona inicial.
          2. Desapilar → recorrer sus children_ids.
          3. Si el hijo no fue visitado, agregarlo a descendientes y apilarlo.
          4. Repetir hasta vaciar la pila.

        Complejidad: O(V+E)
        """
        visited: set[str] = set()
        stack: list[str] = [person_id]
        descendants: list[str] = []

        while stack:
            current = stack.pop()
            person = tree.persons.get(current)
            if not person:
                continue

            for child_id in person.children_ids:
                if child_id not in visited:
                    visited.add(child_id)
                    descendants.append(child_id)
                    stack.append(child_id)

        return descendants

    # ─────────────────────────────────────────────────────────────────────
    # BFS POR NIVELES — Agrupar personas por generación
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_generations(tree: "FamilyTree", root_id: str) -> dict[int, list[str]]:
        """
        BFS (Breadth-First Search) por niveles sobre el árbol N-ario.
        Usa una cola (deque) para procesar nodo a nodo por nivel.

        Algoritmo:
          1. Encolar (raíz, nivel=0).
          2. Desencolar → agregar nodo al nivel correspondiente.
          3. Encolar todos sus hijos con (nivel + 1).
          4. Repetir hasta vaciar la cola.

        Resultado: dict[nivel_generación → lista de IDs en ese nivel]
        Complejidad: O(V+E)
        """
        generations: dict[int, list[str]] = {}
        queue: deque[tuple[str, int]] = deque()
        visited: set[str] = set()

        queue.append((root_id, 0))
        visited.add(root_id)

        while queue:
            current, level = queue.popleft()

            if level not in generations:
                generations[level] = []
            generations[level].append(current)

            person = tree.persons.get(current)
            if not person:
                continue

            for child_id in person.children_ids:
                if child_id not in visited:
                    visited.add(child_id)
                    queue.append((child_id, level + 1))

        return generations

    # ─────────────────────────────────────────────────────────────────────
    # LCA — Ancestro Común Más Cercano
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_ancestors_with_depth(tree: "FamilyTree", person_id: str) -> dict[str, int]:
        """
        DFS para obtener todos los ancestros de una persona con su profundidad.
        Retorna dict[id_ancestro → profundidad desde person_id].
        """
        result: dict[str, int] = {}
        stack: list[tuple[str, int]] = [(person_id, 0)]

        while stack:
            current, depth = stack.pop()
            person = tree.persons.get(current)
            if not person:
                continue

            for parent_id in person.parent_ids:
                if parent_id not in result:
                    result[parent_id] = depth + 1
                    stack.append((parent_id, depth + 1))

        return result

    @staticmethod
    def find_lca(
        tree: "FamilyTree", id_a: str, id_b: str
    ) -> Optional[tuple[str, int, int]]:
        """
        Encuentra el Ancestro Común Más Cercano (LCA) entre dos personas.

        Algoritmo combinado DFS + BFS:
          1. DFS desde A: obtener todos sus ancestros con profundidad.
          2. BFS desde B: recorrer ancestros de B nivel a nivel.
          3. El primer ancestro de B que aparezca en el conjunto de A = LCA.

        Retorna: (lca_id, prof_desde_A, prof_desde_B) o None si no existe.
        Complejidad: O(V+E)
        """
        # Manejo de casos directos
        if id_a == id_b:
            return (id_a, 0, 0)

        person_a = tree.persons.get(id_a)
        person_b = tree.persons.get(id_b)
        if not person_a or not person_b:
            return None

        # Caso: A es ancestro directo de B
        if id_a in TreeAlgorithms._get_ancestors_with_depth(tree, id_b):
            depth = TreeAlgorithms._get_ancestors_with_depth(tree, id_b)[id_a]
            return (id_a, 0, depth)

        # Caso: B es ancestro directo de A
        if id_b in TreeAlgorithms._get_ancestors_with_depth(tree, id_a):
            depth = TreeAlgorithms._get_ancestors_with_depth(tree, id_a)[id_b]
            return (id_b, depth, 0)

        # Caso general: buscar LCA
        ancestors_a = TreeAlgorithms._get_ancestors_with_depth(tree, id_a)

        # BFS desde B hacia sus ancestros
        queue: deque[tuple[str, int]] = deque()
        queue.append((id_b, 0))

        while queue:
            current, depth_b = queue.popleft()
            person = tree.persons.get(current)
            if not person:
                continue

            for parent_id in person.parent_ids:
                if parent_id in ancestors_a:
                    return (parent_id, ancestors_a[parent_id], depth_b + 1)
                queue.append((parent_id, depth_b + 1))

        return None  # Sin ancestro común

    # ─────────────────────────────────────────────────────────────────────
    # CÁLCULO DE GRADO DE PARENTESCO
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_relationship(tree: "FamilyTree", id_a: str, id_b: str) -> str:
        """
        Describe en texto el grado de parentesco entre dos personas.
        Usa el LCA para determinar la relación basada en profundidades.

        Casos:
          - lca == A           → A es ancestro directo de B
          - lca == B           → B es ancestro directo de A
          - prof_A=1, prof_B=1 → Hermanos
          - prof_A=1, prof_B>1 → Tío/Tía
          - prof_B=1, prof_A>1 → Sobrino/Sobrina
          - prof_A == prof_B   → Primos de N grado
          - en el grafo cónyuge → Cónyuge
          - sin LCA            → Sin parentesco conocido
        """
        if id_a == id_b:
            return "Misma persona"

        # Verificar relación de cónyuge en grafo auxiliar
        if id_b in tree.spouse_graph.get(id_a, []):
            return "Cónyuge"

        lca_result = TreeAlgorithms.find_lca(tree, id_a, id_b)
        if lca_result is None:
            return "Sin parentesco conocido"

        lca_id, prof_a, prof_b = lca_result

        if lca_id == id_a:
            generation_map = {1: "Hijo/Hija", 2: "Nieto/Nieta", 3: "Bisnieto/Bisnieta", 4: "Tataranieto/a"}
            return generation_map.get(prof_b, f"Descendiente directo (generación {prof_b})")

        if lca_id == id_b:
            generation_map = {1: "Padre/Madre", 2: "Abuelo/Abuela", 3: "Bisabuelo/Bisabuela", 4: "Tatarabuelo/a"}
            return generation_map.get(prof_a, f"Ancestro directo (generación {prof_a})")

        if prof_a == 1 and prof_b == 1:
            return "Hermano/Hermana"

        if prof_a == 1:
            return f"Tío/Tía de {prof_b - 1}° grado"

        if prof_b == 1:
            return f"Sobrino/Sobrina de {prof_a - 1}° grado"

        if prof_a == prof_b:
            degree = prof_a - 1
            if degree == 1:
                return "Primos hermanos (1er grado)"
            return f"Primos de {degree}° grado"

        return f"Parentesco lejano: {prof_a + prof_b} pasos desde ancestro común"

    # ─────────────────────────────────────────────────────────────────────
    # UTILIDADES EXTRA
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_path_between(tree: "FamilyTree", id_a: str, id_b: str) -> list[str]:
        """
        Retorna la lista de IDs que forman el camino entre dos personas,
        pasando por el LCA. Útil para resaltar visualmente en D3.js.
        """
        lca_result = TreeAlgorithms.find_lca(tree, id_a, id_b)
        if not lca_result:
            return []

        lca_id, _, _ = lca_result

        def path_to_ancestor(start: str, ancestor: str) -> list[str]:
            """Reconstruye el camino desde start hasta ancestor."""
            if start == ancestor:
                return [start]
            # BFS para encontrar el camino
            queue: deque[list[str]] = deque([[start]])
            visited: set[str] = set()
            while queue:
                path = queue.popleft()
                current = path[-1]
                if current == ancestor:
                    return path
                person = tree.persons.get(current)
                if not person or current in visited:
                    continue
                visited.add(current)
                for parent_id in person.parent_ids:
                    queue.append(path + [parent_id])
            return []

        path_a = path_to_ancestor(id_a, lca_id)
        path_b = path_to_ancestor(id_b, lca_id)

        # Combinar: A → LCA + LCA → B (sin duplicar LCA)
        return path_a + list(reversed(path_b[:-1]))
