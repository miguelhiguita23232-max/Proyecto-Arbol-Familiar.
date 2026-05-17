import { useState } from "react";
import type { Person, PersonCreate, TreeStats } from "../api/client";

// ─────────────────────────────────────────────────────────────────────────
// PersonCard
// ─────────────────────────────────────────────────────────────────────────
interface PersonCardProps {
  person: Person;
  allPersons: Record<string, Person>;
  onEdit: () => void;
  onDelete: () => void;
  onClose: () => void;
}

export function PersonCard({ person, allPersons, onEdit, onDelete, onClose }: PersonCardProps) {
  const age = () => {
    if (!person.birth_date) return null;
    const birth = new Date(person.birth_date).getFullYear();
    const end = person.death_date ? new Date(person.death_date).getFullYear() : new Date().getFullYear();
    return end - birth;
  };

  const genderLabel = { M: "Masculino", F: "Femenino", O: "Otro" }[person.gender] ?? "—";
  const lifespan = `${person.birth_date?.slice(0, 4) ?? "?"} – ${person.death_date?.slice(0, 4) ?? "presente"}`;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-4 w-72">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h2 className="font-bold text-slate-800 text-lg leading-tight">{person.first_name} {person.last_name}</h2>
          <p className="text-sm text-slate-500">{lifespan}{age() ? ` (${age()} años)` : ""}</p>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-xl leading-none">×</button>
      </div>

      <div className="text-sm space-y-1 border-t border-slate-100 pt-2">
        {person.birthplace && <div><span className="text-slate-400">Nacimiento:</span> {person.birthplace}</div>}
        <div><span className="text-slate-400">Género:</span> {genderLabel}</div>
        {person.death_date && <div><span className="text-slate-400">Defunción:</span> {person.death_date}</div>}
      </div>

      {(person.spouse_ids.length > 0 || person.children_ids.length > 0 || person.parent_ids.length > 0) && (
        <div className="text-sm space-y-1 border-t border-slate-100 pt-2 mt-2">
          {person.parent_ids.length > 0 && (
            <div><span className="text-slate-400">Padres:</span>{" "}
              {person.parent_ids.map(id => allPersons[id]?.first_name ?? id).join(", ")}
            </div>
          )}
          {person.spouse_ids.length > 0 && (
            <div><span className="text-slate-400">Cónyuge(s):</span>{" "}
              {person.spouse_ids.map(id => allPersons[id]?.first_name ?? id).join(", ")}
            </div>
          )}
          {person.children_ids.length > 0 && (
            <div><span className="text-slate-400">Hijos:</span>{" "}
              {person.children_ids.map(id => allPersons[id]?.first_name ?? id).join(", ")}
            </div>
          )}
        </div>
      )}

      {person.notes && (
        <p className="text-xs text-slate-500 border-t border-slate-100 pt-2 mt-2 italic">
          {person.notes}
        </p>
      )}

      <div className="flex gap-2 mt-3">
        <button onClick={onEdit} className="flex-1 text-sm bg-indigo-600 text-white rounded-lg py-1.5 hover:bg-indigo-700">
          ✏ Editar
        </button>
        <button onClick={onDelete} className="flex-1 text-sm bg-red-50 text-red-600 border border-red-200 rounded-lg py-1.5 hover:bg-red-100">
          🗑 Eliminar
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// PersonForm
// ─────────────────────────────────────────────────────────────────────────
interface PersonFormProps {
  initial?: Partial<PersonCreate>;
  onSubmit: (data: PersonCreate) => Promise<boolean>;
  onCancel: () => void;
  title?: string;
}

export function PersonForm({ initial = {}, onSubmit, onCancel, title = "Nueva Persona" }: PersonFormProps) {
  const [form, setForm] = useState<PersonCreate>({
    first_name: initial.first_name ?? "",
    last_name: initial.last_name ?? "",
    birth_date: initial.birth_date ?? "",
    death_date: initial.death_date ?? "",
    gender: initial.gender ?? "O",
    birthplace: initial.birthplace ?? "",
    notes: initial.notes ?? "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handle = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    const ok = await onSubmit(form);
    setSubmitting(false);
    if (ok) onCancel();
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-4 w-80">
      <h2 className="font-bold text-slate-800 text-base mb-3">{title}</h2>
      <div className="space-y-2 text-sm">
        {[
          { label: "Nombre *", name: "first_name", type: "text" },
          { label: "Apellido *", name: "last_name", type: "text" },
          { label: "Fecha Nac.", name: "birth_date", type: "date" },
          { label: "Fecha Def.", name: "death_date", type: "date" },
          { label: "Lugar de nacimiento", name: "birthplace", type: "text" },
        ].map(({ label, name, type }) => (
          <label key={name} className="block">
            <span className="text-slate-500 text-xs">{label}</span>
            <input
              type={type}
              name={name}
              value={(form as Record<string, string>)[name] ?? ""}
              onChange={handle}
              className="mt-0.5 block w-full rounded-lg border border-slate-200 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </label>
        ))}
        <label className="block">
          <span className="text-slate-500 text-xs">Género</span>
          <select name="gender" value={form.gender ?? "O"} onChange={handle}
            className="mt-0.5 block w-full rounded-lg border border-slate-200 px-2 py-1 text-sm">
            <option value="M">Masculino</option>
            <option value="F">Femenino</option>
            <option value="O">Otro</option>
          </select>
        </label>
        <label className="block">
          <span className="text-slate-500 text-xs">Notas</span>
          <textarea name="notes" rows={2} value={form.notes ?? ""} onChange={handle}
            className="mt-0.5 block w-full rounded-lg border border-slate-200 px-2 py-1 text-sm resize-none" />
        </label>
      </div>
      <div className="flex gap-2 mt-3">
        <button onClick={handleSubmit} disabled={submitting}
          className="flex-1 bg-indigo-600 text-white rounded-lg py-1.5 text-sm hover:bg-indigo-700 disabled:opacity-50">
          {submitting ? "Guardando…" : "Guardar"}
        </button>
        <button onClick={onCancel} className="flex-1 border border-slate-200 text-slate-600 rounded-lg py-1.5 text-sm hover:bg-slate-50">
          Cancelar
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// SearchPanel
// ─────────────────────────────────────────────────────────────────────────
interface SearchPanelProps {
  persons: Person[];
  onSearch: (aId: string, bId: string) => Promise<{ relationship: string; path: string[] } | null>;
  onFindAncestors: (id: string) => void;
  onFindDescendants: (id: string) => void;
  onClearHighlight: () => void;
}

export function SearchPanel({ persons, onSearch, onFindAncestors, onFindDescendants, onClearHighlight }: SearchPanelProps) {
  const [personA, setPersonA] = useState("");
  const [personB, setPersonB] = useState("");
  const [result, setResult] = useState<{ relationship: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!personA || !personB) return;
    setLoading(true);
    const r = await onSearch(personA, personB);
    setResult(r);
    setLoading(false);
  };

  const personSelect = (value: string, setter: (v: string) => void) => (
    <select value={value} onChange={(e) => setter(e.target.value)}
      className="block w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm">
      <option value="">Seleccionar persona...</option>
      {persons.map((p) => (
        <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
      ))}
    </select>
  );

  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 p-4 w-64">
      <h3 className="font-bold text-slate-800 text-sm mb-3">🔍 Calculador de Parentesco</h3>
      <div className="space-y-2 text-xs">
        <div>
          <label className="text-slate-400 mb-1 block">Persona A</label>
          {personSelect(personA, setPersonA)}
        </div>
        <div>
          <label className="text-slate-400 mb-1 block">Persona B</label>
          {personSelect(personB, setPersonB)}
        </div>
        <button onClick={handleSearch} disabled={loading || !personA || !personB}
          className="w-full bg-indigo-600 text-white rounded-lg py-1.5 text-xs hover:bg-indigo-700 disabled:opacity-50">
          {loading ? "Calculando…" : "Calcular parentesco"}
        </button>
        {result && (
          <div className="mt-2 p-2 bg-indigo-50 rounded-lg border border-indigo-200">
            <p className="font-semibold text-indigo-800">{result.relationship}</p>
          </div>
        )}
      </div>

      <div className="border-t border-slate-100 mt-3 pt-3">
        <p className="text-slate-400 text-xs mb-2">Análisis rápido</p>
        <div className="space-y-1">
          <select className="block w-full rounded-lg border border-slate-200 px-2 py-1 text-xs"
            onChange={(e) => { if (e.target.value) onFindAncestors(e.target.value); }}>
            <option value="">Ancestros de...</option>
            {persons.map((p) => (
              <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
            ))}
          </select>
          <button onClick={onClearHighlight}
            className="w-full border border-slate-200 text-slate-500 rounded-lg py-1 text-xs hover:bg-slate-50">
            Limpiar resaltado
          </button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// StatsPanel
// ─────────────────────────────────────────────────────────────────────────
export function StatsPanel({ stats }: { stats: TreeStats | null }) {
  if (!stats) return null;
  const items = [
    { label: "Total personas", value: stats.total_persons, icon: "👥" },
    { label: "Personas vivas", value: stats.alive, icon: "💚" },
    { label: "Fallecidos", value: stats.deceased, icon: "🕊" },
    { label: "Generaciones", value: stats.total_generations, icon: "🌳" },
    { label: "Relaciones", value: stats.total_relationships, icon: "🔗" },
  ];
  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 p-3">
      <h3 className="font-bold text-slate-600 text-xs mb-2">📊 Estadísticas</h3>
      <div className="space-y-1">
        {items.map((i) => (
          <div key={i.label} className="flex justify-between items-center text-xs">
            <span className="text-slate-500">{i.icon} {i.label}</span>
            <span className="font-bold text-slate-800">{i.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}