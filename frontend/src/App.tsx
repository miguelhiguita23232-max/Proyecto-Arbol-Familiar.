// App.tsx — Componente raíz de FamilyTree Pro
import { useState, useRef } from "react";
import TreeView from "./components/TreeView";
import { PersonCard, PersonForm, SearchPanel, StatsPanel } from "./components/index";
import { useFamilyTree } from "./hooks/useFamilyTree";
import type { Person } from "./api/client";

type Panel = "none" | "add" | "edit" | "search" | "relations";

export default function App() {
  const ft = useFamilyTree();
  const [panel, setPanel] = useState<Panel>("none");
  const [relType, setRelType] = useState<"parent-child" | "spouse">("parent-child");
  const [relPersonA, setRelPersonA] = useState("");
  const [relPersonB, setRelPersonB] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const personsMap = Object.fromEntries(ft.persons.map((p) => [p.id, p]));

  const handleDelete = async (id: string) => {
    if (!confirm("¿Eliminar esta persona?")) return;
    await ft.removePerson(id);
  };

  const handleAddRelation = async () => {
    if (!relPersonA || !relPersonB) return;
    if (relType === "parent-child") {
      await ft.connectParentChild(relPersonA, relPersonB);
    } else {
      await ft.connectSpouse(relPersonA, relPersonB);
    }
    setRelPersonA("");
    setRelPersonB("");
    setPanel("none");
  };

  return (
    <div className="h-screen flex flex-col bg-slate-100 font-sans">
      {/* ── Barra superior ──────────────────────────────────────────── */}
      <header className="bg-white border-b border-slate-200 px-4 py-2 flex items-center gap-3 shadow-sm">
        <span className="text-2xl">🌳</span>
        <h1 className="font-bold text-slate-800 text-lg">FamilyTree Pro</h1>
        <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
          Estructuras de Datos
        </span>

        <div className="flex gap-2 ml-auto">
          <button onClick={() => setPanel("add")}
            className="bg-indigo-600 text-white text-sm px-3 py-1.5 rounded-lg hover:bg-indigo-700">
            + Persona
          </button>
          <button onClick={() => setPanel("relations")}
            className="border border-slate-300 text-slate-600 text-sm px-3 py-1.5 rounded-lg hover:bg-slate-50">
            🔗 Relacionar
          </button>
          <button onClick={() => setPanel(panel === "search" ? "none" : "search")}
            className="border border-slate-300 text-slate-600 text-sm px-3 py-1.5 rounded-lg hover:bg-slate-50">
            🔍 Parentesco
          </button>
          {/* Exportar / Importar */}
          <div className="relative group">
            <button className="border border-slate-300 text-slate-600 text-sm px-3 py-1.5 rounded-lg hover:bg-slate-50">
              Exportar ▾
            </button>
            <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-slate-200 z-20 hidden group-hover:block min-w-max">
              <button onClick={ft.downloadJson} className="block w-full text-left px-4 py-2 text-sm hover:bg-slate-50">
                📄 JSON
              </button>
              <a href="http://localhost:8000/export/gedcom" className="block px-4 py-2 text-sm hover:bg-slate-50">
                📋 GEDCOM
              </a>
              <a href="http://localhost:8000/export/pdf" className="block px-4 py-2 text-sm hover:bg-slate-50">
                📑 PDF
              </a>
            </div>
          </div>
          <button onClick={() => fileRef.current?.click()}
            className="border border-slate-300 text-slate-600 text-sm px-3 py-1.5 rounded-lg hover:bg-slate-50">
            📥 Importar JSON
          </button>
          <input ref={fileRef} type="file" accept=".json" className="hidden"
            onChange={(e) => e.target.files?.[0] && ft.uploadJson(e.target.files[0])} />
        </div>
      </header>

      {/* ── Error banner ──────────────────────────────────────────────── */}
      {ft.error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-700 flex justify-between">
          ⚠ {ft.error}
          <button onClick={() => ft.setError(null)} className="text-red-400 hover:text-red-700">×</button>
        </div>
      )}

      {/* ── Área principal ────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden gap-3 p-3">
        {/* Visualización D3 */}
        <div className="flex-1 min-w-0">
          <TreeView
            treeData={ft.treeData}
            selectedPerson={ft.selectedPerson}
            highlightedPath={ft.highlightedPath}
            onSelectPerson={ft.setSelectedPerson}
          />
        </div>

        {/* Panel lateral derecho */}
        <div className="flex flex-col gap-3 w-72 overflow-y-auto">
          {/* Tarjeta de persona seleccionada */}
          {ft.selectedPerson && panel !== "edit" && (
            <PersonCard
              person={ft.selectedPerson}
              allPersons={personsMap}
              onEdit={() => setPanel("edit")}
              onDelete={() => handleDelete(ft.selectedPerson!.id)}
              onClose={() => ft.setSelectedPerson(null)}
            />
          )}

          {/* Formulario nueva persona */}
          {panel === "add" && (
            <PersonForm
              title="Nueva Persona"
              onSubmit={ft.addPerson}
              onCancel={() => setPanel("none")}
            />
          )}

          {/* Formulario editar persona */}
          {panel === "edit" && ft.selectedPerson && (
            <PersonForm
              title={`Editar: ${ft.selectedPerson.first_name}`}
              initial={ft.selectedPerson}
              onSubmit={(data) => ft.editPerson(ft.selectedPerson!.id, data)}
              onCancel={() => setPanel("none")}
            />
          )}

          {/* Panel de relaciones */}
          {panel === "relations" && (
            <div className="bg-white rounded-xl shadow border border-slate-200 p-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold text-slate-800 text-sm">🔗 Establecer Relación</h3>
                <button onClick={() => setPanel("none")} className="text-slate-400 text-lg">×</button>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex gap-2">
                  <button onClick={() => setRelType("parent-child")}
                    className={`flex-1 py-1.5 rounded-lg border text-xs ${relType === "parent-child" ? "bg-indigo-600 text-white border-indigo-600" : "border-slate-200 text-slate-600"}`}>
                    Padre → Hijo
                  </button>
                  <button onClick={() => setRelType("spouse")}
                    className={`flex-1 py-1.5 rounded-lg border text-xs ${relType === "spouse" ? "bg-pink-500 text-white border-pink-500" : "border-slate-200 text-slate-600"}`}>
                    Cónyuge
                  </button>
                </div>
                {[
                  { label: relType === "parent-child" ? "Padre / Madre" : "Persona A", val: relPersonA, set: setRelPersonA },
                  { label: relType === "parent-child" ? "Hijo / Hija" : "Persona B", val: relPersonB, set: setRelPersonB },
                ].map(({ label, val, set }) => (
                  <div key={label}>
                    <label className="text-slate-400 mb-1 block">{label}</label>
                    <select value={val} onChange={(e) => set(e.target.value)}
                      className="block w-full rounded-lg border border-slate-200 px-2 py-1.5 text-xs">
                      <option value="">Seleccionar…</option>
                      {ft.persons.map((p) => (
                        <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
                      ))}
                    </select>
                  </div>
                ))}
                <button onClick={handleAddRelation} disabled={!relPersonA || !relPersonB}
                  className="w-full bg-indigo-600 text-white rounded-lg py-1.5 text-xs hover:bg-indigo-700 disabled:opacity-50">
                  Establecer relación
                </button>
              </div>
            </div>
          )}

          {/* Panel de búsqueda de parentesco */}
          {panel === "search" && (
            <SearchPanel
              persons={ft.persons}
              onSearch={ft.fetchRelationship}
              onFindAncestors={ft.fetchAncestors}
              onFindDescendants={ft.fetchDescendants}
              onClearHighlight={ft.clearHighlight}
            />
          )}

          {/* Estadísticas (siempre visible abajo) */}
          <StatsPanel stats={ft.stats} />
        </div>
      </div>

      {/* Loading overlay */}
      {ft.loading && (
        <div className="fixed inset-0 bg-black/10 flex items-center justify-center z-50 pointer-events-none">
          <div className="bg-white rounded-xl px-6 py-3 shadow-lg text-sm text-slate-600">
            Procesando…
          </div>
        </div>
      )}
    </div>
  );
}
