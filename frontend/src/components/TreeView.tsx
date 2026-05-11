// components/TreeView.tsx — Visualización D3.js del árbol genealógico

import { useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";
import type { Person, TreeData } from "../api/client";

interface TreeViewProps {
  treeData: TreeData | null;
  selectedPerson: Person | null;
  highlightedPath: string[];
  onSelectPerson: (person: Person) => void;
}

export default function TreeView({
  treeData,
  selectedPerson,
  highlightedPath,
  onSelectPerson,
}: TreeViewProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  const render = useCallback(() => {
    if (!svgRef.current || !treeData) return;

    const width = svgRef.current.clientWidth || 900;
    const height = svgRef.current.clientHeight || 600;

    // Limpiar SVG anterior
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    // Grupo principal con zoom + pan
    const g = svg.append("g");

    svg.call(
      d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.1, 3])
        .on("zoom", (event) => g.attr("transform", event.transform))
    );

    // ── Separar enlaces por tipo ────────────────────────────────────────
    const parentChildLinks = treeData.links.filter((l) => l.type === "parent-child");
    const spouseLinks = treeData.links.filter((l) => l.type === "spouse");

    // Índice de nodos por ID
    const nodeById = new Map(treeData.nodes.map((n) => [n.id, n]));

    // ── Simulación de fuerza D3 ─────────────────────────────────────────
    const simulation = d3
      .forceSimulation(treeData.nodes as d3.SimulationNodeDatum[])
      .force(
        "link",
        d3
          .forceLink(
            [...parentChildLinks, ...spouseLinks].map((l) => ({
              source: l.source,
              target: l.target,
              type: l.type,
            }))
          )
          .id((d: d3.SimulationNodeDatum) => (d as Person).id)
          .distance((d) => (d.type === "spouse" ? 80 : 120))
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("y", d3.forceY().strength(0.1));

    // ── Dibujar aristas padre-hijo ──────────────────────────────────────
    const linkParent = g
      .append("g")
      .selectAll("line")
      .data(parentChildLinks)
      .join("line")
      .attr("stroke", (d) =>
        highlightedPath.includes(d.source as string) &&
        highlightedPath.includes(d.target as string)
          ? "#f59e0b"
          : "#94a3b8"
      )
      .attr("stroke-width", (d) =>
        highlightedPath.includes(d.source as string) &&
        highlightedPath.includes(d.target as string)
          ? 3
          : 1.5
      )
      .attr("marker-end", "url(#arrow)");

    // Marcador de flecha
    svg
      .append("defs")
      .append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 28)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#94a3b8");

    // ── Dibujar aristas de cónyuge (punteadas) ──────────────────────────
    const linkSpouse = g
      .append("g")
      .selectAll("line")
      .data(spouseLinks)
      .join("line")
      .attr("stroke", "#f472b6")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,4")
      .attr("opacity", 0.8);

    // ── Dibujar nodos ───────────────────────────────────────────────────
    const node = g
      .append("g")
      .selectAll("g")
      .data(treeData.nodes)
      .join("g")
      .attr("cursor", "pointer")
      .on("click", (_, d) => onSelectPerson(d))
      .call(
        d3
          .drag<SVGGElement, Person>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            (d as d3.SimulationNodeDatum).fx = (d as d3.SimulationNodeDatum).x;
            (d as d3.SimulationNodeDatum).fy = (d as d3.SimulationNodeDatum).y;
          })
          .on("drag", (event, d) => {
            (d as d3.SimulationNodeDatum).fx = event.x;
            (d as d3.SimulationNodeDatum).fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            (d as d3.SimulationNodeDatum).fx = null;
            (d as d3.SimulationNodeDatum).fy = null;
          })
      );

    // Círculo del nodo
    node
      .append("circle")
      .attr("r", 24)
      .attr("fill", (d) => {
        if (d.id === selectedPerson?.id) return "#6366f1";
        if (highlightedPath.includes(d.id)) return "#f59e0b";
        if (treeData.roots.includes(d.id)) return "#10b981";
        return d.gender === "M" ? "#3b82f6" : d.gender === "F" ? "#ec4899" : "#8b5cf6";
      })
      .attr("stroke", (d) =>
        d.id === selectedPerson?.id ? "#312e81" : "#fff"
      )
      .attr("stroke-width", (d) => (d.id === selectedPerson?.id ? 3 : 2));

    // Inicial del nombre
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("fill", "white")
      .attr("font-size", 14)
      .attr("font-weight", "bold")
      .attr("pointer-events", "none")
      .text((d) => d.first_name.charAt(0) + d.last_name.charAt(0));

    // Nombre bajo el nodo
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "2.8em")
      .attr("fill", "#1e293b")
      .attr("font-size", 10)
      .attr("pointer-events", "none")
      .text((d) => `${d.first_name} ${d.last_name}`);

    // Años de vida
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "4em")
      .attr("fill", "#64748b")
      .attr("font-size", 9)
      .attr("pointer-events", "none")
      .text((d) => {
        const birth = d.birth_date ? d.birth_date.slice(0, 4) : "?";
        const death = d.death_date ? d.death_date.slice(0, 4) : "vivo";
        return `${birth} – ${death}`;
      });

    // ── Tick ─────────────────────────────────────────────────────────────
    simulation.on("tick", () => {
      linkParent
        .attr("x1", (d) => (nodeById.get(d.source as string) as d3.SimulationNodeDatum)?.x ?? 0)
        .attr("y1", (d) => (nodeById.get(d.source as string) as d3.SimulationNodeDatum)?.y ?? 0)
        .attr("x2", (d) => (nodeById.get(d.target as string) as d3.SimulationNodeDatum)?.x ?? 0)
        .attr("y2", (d) => (nodeById.get(d.target as string) as d3.SimulationNodeDatum)?.y ?? 0);

      linkSpouse
        .attr("x1", (d) => (nodeById.get(d.source as string) as d3.SimulationNodeDatum)?.x ?? 0)
        .attr("y1", (d) => (nodeById.get(d.source as string) as d3.SimulationNodeDatum)?.y ?? 0)
        .attr("x2", (d) => (nodeById.get(d.target as string) as d3.SimulationNodeDatum)?.x ?? 0)
        .attr("y2", (d) => (nodeById.get(d.target as string) as d3.SimulationNodeDatum)?.y ?? 0);

      node.attr("transform", (d) => {
        const n = d as d3.SimulationNodeDatum;
        return `translate(${n.x ?? 0},${n.y ?? 0})`;
      });
    });

    return () => simulation.stop();
  }, [treeData, selectedPerson, highlightedPath, onSelectPerson]);

  useEffect(() => {
    const cleanup = render();
    return cleanup;
  }, [render]);

  // Re-render al cambiar resaltado sin reiniciar simulación
  useEffect(() => {
    if (!svgRef.current || !treeData) return;
    d3.select(svgRef.current)
      .selectAll("circle")
      .attr("fill", (d) => {
        const p = d as Person;
        if (p.id === selectedPerson?.id) return "#6366f1";
        if (highlightedPath.includes(p.id)) return "#f59e0b";
        if (treeData.roots.includes(p.id)) return "#10b981";
        return p.gender === "M" ? "#3b82f6" : p.gender === "F" ? "#ec4899" : "#8b5cf6";
      });
  }, [highlightedPath, selectedPerson, treeData]);

  return (
    <div className="relative w-full h-full bg-slate-50 rounded-xl overflow-hidden border border-slate-200">
      {/* Leyenda */}
      <div className="absolute top-3 left-3 flex flex-col gap-1 bg-white/90 rounded-lg p-2 text-xs shadow z-10">
        <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-500 inline-block"/>Masculino</div>
        <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-pink-500 inline-block"/>Femenino</div>
        <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"/>Raíz</div>
        <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-amber-400 inline-block"/>Resaltado</div>
        <div className="flex items-center gap-1"><span className="w-3 h-0.5 bg-pink-400 inline-block border-dashed"/>Cónyuge</div>
      </div>
      <svg ref={svgRef} className="w-full h-full" />
      {(!treeData || treeData.nodes.length === 0) && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">
          No hay personas en el árbol. Agrega la primera persona para comenzar.
        </div>
      )}
    </div>
  );
}
