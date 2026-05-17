"""
database.py — Capa de Persistencia con SQLAlchemy + SQLite
Serializa/deserializa la FamilyTree hacia/desde la base de datos local.
"""

from sqlalchemy import create_engine, Column, String, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Session
import json
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./familytree.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class PersonModel(Base):
    """Modelo ORM para la tabla 'persons' en SQLite."""
    __tablename__ = "persons"

    id = Column(String, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(String, nullable=True)
    death_date = Column(String, nullable=True)
    gender = Column(String, default="O")
    birthplace = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    # Listas serializadas como JSON string
    parent_ids = Column(Text, default="[]")
    children_ids = Column(Text, default="[]")
    spouse_ids = Column(Text, default="[]")


class SpouseRelationModel(Base):
    """Tabla auxiliar para relaciones de cónyuge (grafo no dirigido)."""
    __tablename__ = "spouse_relations"

    id = Column(String, primary_key=True)   # "{id_a}_{id_b}"
    person_a_id = Column(String, nullable=False)
    person_b_id = Column(String, nullable=False)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    """Generador de sesión para FastAPI Depends."""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────
# Funciones de sincronización FamilyTree ↔ SQLite
# ─────────────────────────────────────────────────────────────────────────

def save_tree_to_db(tree, db: Session) -> None:
    """Persiste toda la FamilyTree en SQLite. Upsert por ID."""
    for person in tree.persons.values():
        existing = db.get(PersonModel, person.id)
        data = {
            "first_name": person.first_name,
            "last_name": person.last_name,
            "birth_date": person.birth_date,
            "death_date": person.death_date,
            "gender": person.gender.value if hasattr(person.gender, "value") else person.gender,
            "birthplace": person.birthplace,
            "photo_url": person.photo_url,
            "notes": person.notes,
            "parent_ids": json.dumps(person.parent_ids),
            "children_ids": json.dumps(person.children_ids),
            "spouse_ids": json.dumps(person.spouse_ids),
        }
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
        else:
            db.add(PersonModel(id=person.id, **data))

    db.commit()


def load_tree_from_db(db: Session):
    from models import FamilyTree, Person, Gender

    tree = FamilyTree()
    persons_db = db.query(PersonModel).all()

    for pm in persons_db:
        person = Person(
            id=pm.id,
            first_name=pm.first_name,
            last_name=pm.last_name,
            birth_date=pm.birth_date,
            death_date=pm.death_date,
            gender=Gender(pm.gender) if pm.gender else Gender.O,
            birthplace=pm.birthplace,
            photo_url=pm.photo_url,
            notes=pm.notes,
            parent_ids=json.loads(pm.parent_ids or "[]"),
            children_ids=json.loads(pm.children_ids or "[]"),
            spouse_ids=json.loads(pm.spouse_ids or "[]"),
        )
        tree.persons[person.id] = person
        tree.spouse_graph[person.id] = list(person.spouse_ids)

    tree.roots = [pid for pid, p in tree.persons.items() if not p.parent_ids]
    return tree


def delete_person_from_db(person_id: str, db: Session) -> None:
    pm = db.get(PersonModel, person_id)
    if pm:
        db.delete(pm)
        db.commit()
