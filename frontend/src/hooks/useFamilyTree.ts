// hooks/useFamilyTree.ts — Estado global y llamadas a la API

import { useState, useCallback, useEffect } from "react";
import type { Person, PersonCreate, TreeData, TreeStats, RelationshipResult } from "../api/client";
import {
  listPersons,
  createPerson,
  updatePerson,
  deletePerson,
  searchPersons,
  addParentChild,
  addSpouse,
  getAncestors,
  getDescendants,
  getGenerations,
  findLCA,
  getRelationship,
  getTreeData,
  getStats,
  exportJson,
  importJson,
} from "../api/client";

export function useFamilyTree() {
  const [persons, setPersons] = useState<Person[]>([]);
  const [treeData, setTreeData] = useState<TreeData | null>(null);
  const [stats, setStats] = useState<TreeStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [highlightedPath, setHighlightedPath] = useState<string[]>([]);

  const handleError = (e: unknown) => {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    setError(msg || "Error desconocido");
  };

  // ── Carga inicial ────────────────────────────────────────────────────
  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [p, t, s] = await Promise.all([listPersons(), getTreeData(), getStats()]);
      setPersons(p);
      setTreeData(t);
      setStats(s);
      setError(null);
    } catch (e) {
      handleError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // ── Personas ─────────────────────────────────────────────────────────
  const addPerson = useCallback(async (data: PersonCreate) => {
    setLoading(true);
    try {
      await createPerson(data);
      await loadAll();
      return true;
    } catch (e) {
      handleError(e);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadAll]);

  const editPerson = useCallback(async (id: string, data: Partial<PersonCreate>) => {
    setLoading(true);
    try {
      await updatePerson(id, data);
      await loadAll();
      return true;
    } catch (e) {
      handleError(e);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadAll]);

  const removePerson = useCallback(async (id: string) => {
    setLoading(true);
    try {
      await deletePerson(id);
      if (selectedPerson?.id === id) setSelectedPerson(null);
      await loadAll();
      return true;
    } catch (e) {
      handleError(e);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadAll, selectedPerson]);

  const search = useCallback(async (query: string) => {
    if (!query.trim()) return persons;
    try {
      return await searchPersons(query);
    } catch {
      return [];
    }
  }, [persons]);

  // ── Relaciones ───────────────────────────────────────────────────────
  const connectParentChild = useCallback(async (parentId: string, childId: string) => {
    setLoading(true);
    try {
      await addParentChild(parentId, childId);
      await loadAll();
      setError(null);
      return true;
    } catch (e) {
      handleError(e);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadAll]);

  const connectSpouse = useCallback(async (idA: string, idB: string) => {
    setLoading(true);
    try {
      await addSpouse(idA, idB);
      await loadAll();
      setError(null);
      return true;
    } catch (e) {
      handleError(e);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadAll]);

  // ── Algoritmos ───────────────────────────────────────────────────────
  const fetchAncestors = useCallback(async (id: string) => {
    try {
      const result = await getAncestors(id);
      setHighlightedPath([id, ...result.ancestors.map((p: Person) => p.id)]);
      return result;
    } catch (e) {
      handleError(e);
      return null;
    }
  }, []);

  const fetchDescendants = useCallback(async (id: string) => {
    try {
      const result = await getDescendants(id);
      setHighlightedPath([id, ...result.descendants.map((p: Person) => p.id)]);
      return result;
    } catch (e) {
      handleError(e);
      return null;
    }
  }, []);

  const fetchGenerations = useCallback(async (rootId?: string) => {
    try {
      return await getGenerations(rootId);
    } catch (e) {
      handleError(e);
      return null;
    }
  }, []);

  const fetchLCA = useCallback(async (aId: string, bId: string) => {
    try {
      return await findLCA(aId, bId);
    } catch (e) {
      handleError(e);
      return null;
    }
  }, []);

  const fetchRelationship = useCallback(async (aId: string, bId: string) => {
    try {
      const result: RelationshipResult = await getRelationship(aId, bId);
      setHighlightedPath(result.path);
      return result;
    } catch (e) {
      handleError(e);
      return null;
    }
  }, []);

  const clearHighlight = useCallback(() => setHighlightedPath([]), []);

  // ── Exportación / Importación ────────────────────────────────────────
  const downloadJson = useCallback(async () => {
    const data = await exportJson();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "family_tree.json";
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const uploadJson = useCallback(async (file: File) => {
    const text = await file.text();
    const data = JSON.parse(text);
    setLoading(true);
    try {
      await importJson(data);
      await loadAll();
      return true;
    } catch (e) {
      handleError(e);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadAll]);

  return {
    // Estado
    persons,
    treeData,
    stats,
    loading,
    error,
    setError,
    selectedPerson,
    setSelectedPerson,
    highlightedPath,
    clearHighlight,
    // Personas
    addPerson,
    editPerson,
    removePerson,
    search,
    // Relaciones
    connectParentChild,
    connectSpouse,
    // Algoritmos
    fetchAncestors,
    fetchDescendants,
    fetchGenerations,
    fetchLCA,
    fetchRelationship,
    // Exportación
    downloadJson,
    uploadJson,
    // Recarga
    reload: loadAll,
  };
}
