// api/client.ts — Cliente Axios con todos los endpoints tipados

import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ─── Tipos ────────────────────────────────────────────────────────────────

export type Gender = "M" | "F" | "O";

export interface Person {
  id: string;
  first_name: string;
  last_name: string;
  birth_date?: string;
  death_date?: string;
  gender: Gender;
  birthplace?: string;
  photo_url?: string;
  notes?: string;
  parent_ids: string[];
  children_ids: string[];
  spouse_ids: string[];
}

export interface PersonCreate {
  first_name: string;
  last_name: string;
  birth_date?: string;
  death_date?: string;
  gender?: Gender;
  birthplace?: string;
  photo_url?: string;
  notes?: string;
}

export interface TreeData {
  nodes: Person[];
  links: { source: string; target: string; type: "parent-child" | "spouse" }[];
  roots: string[];
}

export interface RelationshipResult {
  person_a: Person;
  person_b: Person;
  relationship: string;
  path: string[];
}

export interface LCAResult {
  lca: Person | null;
  depth_from_a: number;
  depth_from_b: number;
  message?: string;
}

export interface GenerationsResult {
  total_generations: number;
  generations: Record<string, Person[]>;
}

export interface TreeStats {
  total_persons: number;
  alive: number;
  deceased: number;
  total_generations: number;
  roots: number;
  total_relationships: number;
}

// ─── API Functions ────────────────────────────────────────────────────────

// Personas
export const listPersons = () => api.get<Person[]>("/persons").then((r) => r.data);
export const createPerson = (data: PersonCreate) => api.post<Person>("/persons", data).then((r) => r.data);
export const getPerson = (id: string) => api.get<Person>(`/persons/${id}`).then((r) => r.data);
export const updatePerson = (id: string, data: Partial<PersonCreate>) =>
  api.put<Person>(`/persons/${id}`, data).then((r) => r.data);
export const deletePerson = (id: string) => api.delete(`/persons/${id}`).then((r) => r.data);
export const searchPersons = (q: string) =>
  api.get<Person[]>(`/persons/search/${encodeURIComponent(q)}`).then((r) => r.data);

// Relaciones
export const addParentChild = (parent_id: string, child_id: string) =>
  api.post("/relations/parent-child", { parent_id, child_id }).then((r) => r.data);
export const addSpouse = (person_a_id: string, person_b_id: string) =>
  api.post("/relations/spouse", { person_a_id, person_b_id }).then((r) => r.data);
export const getSiblings = (id: string) =>
  api.get(`/persons/${id}/siblings`).then((r) => r.data);

// Algoritmos
export const getAncestors = (id: string) =>
  api.get(`/algorithms/ancestors/${id}`).then((r) => r.data);
export const getDescendants = (id: string) =>
  api.get(`/algorithms/descendants/${id}`).then((r) => r.data);
export const getGenerations = (rootId?: string) =>
  api
    .get<GenerationsResult>("/algorithms/generations", { params: rootId ? { root_id: rootId } : {} })
    .then((r) => r.data);
export const findLCA = (aId: string, bId: string) =>
  api
    .get<LCAResult>("/algorithms/lca", { params: { person_a_id: aId, person_b_id: bId } })
    .then((r) => r.data);
export const getRelationship = (aId: string, bId: string) =>
  api
    .get<RelationshipResult>("/algorithms/relationship", {
      params: { person_a_id: aId, person_b_id: bId },
    })
    .then((r) => r.data);

// Árbol D3
export const getTreeData = () => api.get<TreeData>("/tree").then((r) => r.data);

// Stats
export const getStats = () => api.get<TreeStats>("/stats").then((r) => r.data);

// Exportación
export const exportJson = () => api.get("/export/json").then((r) => r.data);
export const exportGedcomUrl = () => `${BASE_URL}/export/gedcom`;
export const exportPdfUrl = () => `${BASE_URL}/export/pdf`;

// Importación JSON
export const importJson = (data: object) =>
  api.post("/import/json", data).then((r) => r.data);
