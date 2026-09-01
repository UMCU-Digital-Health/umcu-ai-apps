"""This module contains the SQLAlchemy models for the database.
The main function of this database is to store logging, feedback and evaluation data.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase, MappedAsDataclass):
    """Base class for all models."""

    pass


class Reference(Base):
    """Table that stores reference information."""

    __tablename__ = "reference"
    __table_args__ = {"schema": "llm_eval"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    reference_id: Mapped[int] = mapped_column(Integer, unique=True)
    reference_description: Mapped[str] = mapped_column(String, nullable=True)
    department: Mapped[str] = mapped_column(String(50), nullable=True)
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(), init=False
    )

    # Relationships
    evaluation_item_relation: Mapped["EvaluationItem"] = relationship(
        back_populates="reference_relation", uselist=False, init=False
    )
    context_relation: Mapped["Context"] = relationship(
        back_populates="reference_relation", uselist=False, init=False
    )


class EvaluationItem(Base):
    """Table that stores the items that are evaluated, typically LLM responses."""

    __tablename__ = "evaluation_item"
    __table_args__ = {"schema": "llm_eval"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    reference_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(Reference.id), unique=True, init=True
    )
    llm_response: Mapped[str]
    model: Mapped[str] = mapped_column(String(10), nullable=True)

    # Relationships
    reference_relation: Mapped["Reference"] = relationship(
        back_populates="evaluation_item_relation", init=False
    )
    markings_relation: Mapped[list["Marking"]] = relationship(
        back_populates="evaluation_item_relation", init=False
    )
    assessment_usability_relation: Mapped["AssessmentUsability"] = relationship(
        back_populates="evaluation_item_relation", init=False
    )


class Context(Base):
    """Table that stores context information."""

    __tablename__ = "context"
    __table_args__ = {"schema": "llm_eval"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    reference_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(Reference.id), unique=True, init=True
    )
    context_text: Mapped[str]

    # Relationships
    reference_relation: Mapped["Reference"] = relationship(
        back_populates="context_relation", init=False
    )
    markings_relation: Mapped[list["Marking"]] = relationship(
        back_populates="context_relation", init=False
    )


class User(Base):
    """Table that stores user information."""

    __tablename__ = "user"
    __table_args__ = {"schema": "llm_eval"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    email: Mapped[str]

    # Relationships
    markings_relation: Mapped[list["Marking"]] = relationship(
        back_populates="user_relation", init=False
    )
    assessment_usabilities_relation: Mapped[list["AssessmentUsability"]] = relationship(
        back_populates="user_relation", init=False
    )


class Marking(Base):
    """Table that stores markings made."""

    __tablename__ = "marking"
    __table_args__ = {"schema": "llm_eval"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), init=True)
    evaluation_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(EvaluationItem.id), init=True
    )
    context_id: Mapped[int] = mapped_column(Integer, ForeignKey(Context.id), init=True)
    marking_type: Mapped[str]
    marking_text: Mapped[str]
    marking_start: Mapped[int]
    marking_end: Mapped[int]
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    is_severe: Mapped[bool] = mapped_column(Boolean, default=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True, default=None)

    # Relationships
    user_relation: Mapped["User"] = relationship(
        back_populates="markings_relation", init=False
    )
    evaluation_item_relation: Mapped["EvaluationItem"] = relationship(
        back_populates="markings_relation", init=False
    )
    context_relation: Mapped["Context"] = relationship(
        back_populates="markings_relation", init=False
    )


class AssessmentUsability(Base):
    """Table that stores usability assessments."""

    __tablename__ = "assessment_usability"
    __table_args__ = {"schema": "llm_eval"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, init=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), init=True)
    evaluation_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(EvaluationItem.id), unique=True, init=True
    )
    usability_score: Mapped[int]
    comments: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    user_relation: Mapped["User"] = relationship(
        back_populates="assessment_usabilities_relation", init=False
    )
    evaluation_item_relation: Mapped["EvaluationItem"] = relationship(
        back_populates="assessment_usability_relation", init=False
    )
