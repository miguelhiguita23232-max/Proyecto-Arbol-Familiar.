"""
exporters.py — Exportación a JSON, GEDCOM y PDF
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import json
import io

if TYPE_CHECKING:
    from models import FamilyTree


class JsonExporter:
    @staticmethod
    def export(tree: "FamilyTree") -> str:
        return json.dumps(tree.export_json(), indent=2, ensure_ascii=False)

    @staticmethod
    def import_from_string(tree: "FamilyTree", json_str: str) -> None:
        data = json.loads(json_str)
        tree.import_json(data)


class GedcomExporter:
    """
    Exporta/importa el subconjunto GEDCOM 5.5.1:
    Registros INDI (individuos) y FAM (familias).
    """

    @staticmethod
    def export(tree: "FamilyTree") -> str:
        lines = [
            "0 HEAD",
            "1 SOUR FamilyTree Pro",
            "1 GEDC",
            "2 VERS 5.5.1",
            "1 CHAR UTF-8",
            "1 LANG Spanish",
        ]

        # Registros INDI
        for person in tree.persons.values():
            lines.append(f"0 @I{person.id[:8]}@ INDI")
            lines.append(f"1 NAME {person.first_name} /{person.last_name}/")
            gender_map = {"M": "M", "F": "F", "O": "U"}
            lines.append(f"1 SEX {gender_map.get(str(person.gender.value if hasattr(person.gender,'value') else person.gender), 'U')}")

            if person.birth_date:
                lines.append("1 BIRT")
                lines.append(f"2 DATE {_format_gedcom_date(person.birth_date)}")
                if person.birthplace:
                    lines.append(f"2 PLAC {person.birthplace}")

            if person.death_date:
                lines.append("1 DEAT")
                lines.append(f"2 DATE {_format_gedcom_date(person.death_date)}")

            if person.notes:
                # GEDCOM: NOTE puede ser multilínea
                lines.append(f"1 NOTE {person.notes[:200]}")

        # Registros FAM — una familia por cada pareja con hijos compartidos
        families_written: set[str] = set()
        for person in tree.persons.values():
            if not person.spouse_ids:
                continue
            for spouse_id in person.spouse_ids:
                fam_key = "_".join(sorted([person.id[:8], spouse_id[:8]]))
                if fam_key in families_written:
                    continue
                families_written.add(fam_key)
                lines.append(f"0 @F{fam_key}@ FAM")
                lines.append(f"1 HUSB @I{person.id[:8]}@")
                lines.append(f"1 WIFE @I{spouse_id[:8]}@")
                # Hijos en común
                shared_children = set(person.children_ids) & set(
                    tree.persons[spouse_id].children_ids
                ) if spouse_id in tree.persons else set()
                for cid in shared_children:
                    lines.append(f"1 CHIL @I{cid[:8]}@")

        lines.append("0 TRLR")
        return "\n".join(lines)

    @staticmethod
    def import_from_string(tree: "FamilyTree", gedcom_str: str) -> None:
        """
        Importación básica de GEDCOM 5.5.1.
        Procesa registros INDI con NAME, SEX, BIRT/DATE, DEAT/DATE.
        """
        from models import Person, Gender

        lines = gedcom_str.strip().split("\n")
        current_indi: dict | None = None
        current_tag: str | None = None

        for line in lines:
            parts = line.strip().split(" ", 2)
            if len(parts) < 2:
                continue
            level = parts[0]
            tag_or_id = parts[1]
            value = parts[2] if len(parts) > 2 else ""

            if level == "0":
                # Guardar individuo previo
                if current_indi:
                    person = Person(
                        id=current_indi.get("id", ""),
                        first_name=current_indi.get("first_name", ""),
                        last_name=current_indi.get("last_name", ""),
                        birth_date=current_indi.get("birth_date"),
                        death_date=current_indi.get("death_date"),
                        gender=Gender(current_indi.get("gender", "O")),
                    )
                    tree.add_person(person)
                    current_indi = None
                    current_tag = None

                if "@I" in tag_or_id and "INDI" in value:
                    current_indi = {"id": tag_or_id.strip("@").replace("I", "", 1)}

            elif level == "1" and current_indi is not None:
                current_tag = tag_or_id
                if tag_or_id == "NAME":
                    name_parts = value.replace("/", "").split()
                    current_indi["first_name"] = name_parts[0] if name_parts else ""
                    current_indi["last_name"] = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                elif tag_or_id == "SEX":
                    sex_map = {"M": "M", "F": "F"}
                    current_indi["gender"] = sex_map.get(value, "O")

            elif level == "2" and current_indi is not None:
                if tag_or_id == "DATE":
                    parsed = _parse_gedcom_date(value)
                    if current_tag == "BIRT":
                        current_indi["birth_date"] = parsed
                    elif current_tag == "DEAT":
                        current_indi["death_date"] = parsed
                elif tag_or_id == "PLAC" and current_tag == "BIRT":
                    current_indi["birthplace"] = value


class PdfExporter:
    """Exporta un reporte PDF con la lista de personas y estadísticas del árbol."""

    @staticmethod
    def export(tree: "FamilyTree") -> bytes:
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import inch
        except ImportError:
            return b"ReportLab no instalado. Ejecute: pip install reportlab"

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Título
        title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=20, spaceAfter=20)
        story.append(Paragraph("FamilyTree Pro — Reporte Familiar", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Estadísticas
        stats = tree.stats()
        stats_data = [
            ["Métrica", "Valor"],
            ["Total personas", str(stats["total_persons"])],
            ["Personas vivas", str(stats["alive"])],
            ["Personas fallecidas", str(stats["deceased"])],
            ["Total generaciones", str(stats["total_generations"])],
            ["Relaciones padre-hijo", str(stats["total_relationships"])],
        ]
        stats_table = Table(stats_data, colWidths=[3 * inch, 2 * inch])
        stats_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.3 * inch))

        # Lista de personas
        story.append(Paragraph("Personas Registradas", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        persons_data = [["Nombre completo", "Nac.", "Def.", "Género", "Padres", "Hijos"]]
        for person in sorted(tree.persons.values(), key=lambda p: p.last_name):
            persons_data.append([
                person.full_name(),
                person.birth_date or "—",
                person.death_date or "Vivo/a",
                person.gender.value if hasattr(person.gender, "value") else str(person.gender),
                str(len(person.parent_ids)),
                str(len(person.children_ids)),
            ])

        persons_table = Table(persons_data, colWidths=[2.2*inch, 1*inch, 1*inch, 0.7*inch, 0.7*inch, 0.6*inch])
        persons_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(persons_table)

        doc.build(story)
        return buffer.getvalue()


# ─────────────────────────────────────────────────────────────────────────
# Helpers de formato de fechas GEDCOM
# ─────────────────────────────────────────────────────────────────────────

_MONTH_MAP = {
    "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR",
    "05": "MAY", "06": "JUN", "07": "JUL", "08": "AUG",
    "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC",
}
_MONTH_BACK = {v: f"{int(k):02d}" for k, v in _MONTH_MAP.items()}


def _format_gedcom_date(iso_date: str) -> str:
    """Convierte 'YYYY-MM-DD' → 'DD MMM YYYY' (formato GEDCOM)."""
    try:
        y, m, d = iso_date.split("-")
        return f"{d} {_MONTH_MAP.get(m, m)} {y}"
    except Exception:
        return iso_date


def _parse_gedcom_date(gedcom_date: str) -> str | None:
    """Convierte 'DD MMM YYYY' → 'YYYY-MM-DD' (formato ISO)."""
    parts = gedcom_date.strip().split()
    try:
        if len(parts) == 3:
            d, m, y = parts
            month = _MONTH_BACK.get(m.upper(), "01")
            return f"{y}-{month}-{int(d):02d}"
        elif len(parts) == 2:
            m, y = parts
            month = _MONTH_BACK.get(m.upper(), "01")
            return f"{y}-{month}-01"
        elif len(parts) == 1:
            return f"{parts[0]}-01-01"
    except Exception:
        pass
    return None
