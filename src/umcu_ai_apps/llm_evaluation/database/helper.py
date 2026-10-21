import logging
from datetime import datetime

import flask
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from umcu_ai_utils.dash.authentication import get_user_email

from umcu_ai_apps.llm_evaluation.dashboard.dataclasses import (
    MarkingData,
    ReferenceData,
    Selection,
)
from umcu_ai_apps.llm_evaluation.database.models import (
    AssessmentUsability,
    Marking,
    Reference,
    User,
    UserAccess,
)

logger = logging.getLogger(__name__)


def get_user_id(session_factory: sessionmaker) -> int:
    """Return the DB id for the current user

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    """
    email = get_user_email(flask.request)
    with session_factory() as session:
        user = session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user is None:
            user = User(email=email)
            session.add(user)
            session.commit()
            logger.info(f"User {user.email} added")
        return user.id


def load_dropdown_options(session_factory: sessionmaker, user_id: int) -> list[dict]:
    """Query reference labels for the reference dropdown.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    user_id : int
        The ID of the current user.
    """
    with session_factory() as session:
        refs = (
            session.execute(
                select(Reference).where(
                    Reference.project == UserAccess.project,
                    Reference.department == UserAccess.department,
                    UserAccess.user_id == user_id,
                )
            )
            .scalars()
            .all()
        )
    return [
        {
            "label": (f"{r.reference_id} — {r.reference_description or ''}").strip(
                " —"
            ),
            "value": r.id,
        }
        for r in refs
    ]


def load_reference(
    session_factory: sessionmaker, ref_id: int, user_id: int
) -> ReferenceData:
    """Load full data from the database for a specific reference with ref_id.

    Returns context text, LLM response, internal IDs, and the markings.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    ref_id : int
        The Reference.id to load.
    user_id : int
        The ID of the current user.

    Returns
    -------
    ReferenceData
        The loaded reference data including context,
        LLM response, internal IDs, and markings.
    """
    with session_factory() as session:
        ref = session.execute(
            select(Reference).where(
                Reference.id == ref_id,
                Reference.project == UserAccess.project,
                Reference.department == UserAccess.department,
                UserAccess.user_id == user_id,
            )
        ).scalar_one_or_none()
        if ref is None:
            raise ValueError(f"Reference with id {ref_id} not found.")

        eval_item = ref.evaluation_item_relation
        context = ref.context_relation

        db_markings = (
            session.execute(
                select(Marking).where(
                    Marking.evaluation_item_id == eval_item.id,
                )
            )
            .scalars()
            .all()
        )
    return ReferenceData(
        context=context.context_text,
        llm=eval_item.llm_response,
        evaluation_item_id=eval_item.id,
        markings=[
            MarkingData(
                id=m.id,
                sel=Selection(
                    text=m.marking_text,
                    start=m.marking_start,
                    end=m.marking_end,
                    type=m.marking_type,
                ),
                is_severe=m.is_severe,
                comment=m.comment or "",
            )
            for m in db_markings
        ],
    )


def save_marking_to_db(
    session_factory: sessionmaker,
    ref_id: int,
    user_id: int,
    sel: Selection,
) -> None:
    """Insert a new marking into the database.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    ref_id : int
        The Reference.id this marking belongs to.
    user_id : int
        The ID of the current user.
    sel : Selection
        Selection object with "text", "start", "end", and "type" attributes.
    """
    with session_factory() as session:
        ref = session.get(Reference, ref_id)
        if ref is None:
            raise ValueError(f"Reference with id {ref_id} not found.")
        marking = Marking(
            user_id=user_id,
            evaluation_item_id=ref.evaluation_item_relation.id,
            context_id=ref.context_relation.id,
            marking_type=sel.type,
            marking_text=sel.text,
            marking_start=sel.start,
            marking_end=sel.end,
            timestamp=datetime.now(),
        )
        session.add(marking)
        session.commit()


def delete_marking_from_db(
    session_factory: sessionmaker,
    marking_id: int,
) -> None:
    """Delete a marking from the database by its primary key.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    marking_id : int
        The Marking.id to remove.
    """
    with session_factory() as session:
        marking = session.get(Marking, marking_id)
        if marking is not None:
            session.delete(marking)
            session.commit()


def update_marking_severity(
    session_factory: sessionmaker,
    marking_id: int,
    is_severe: bool,
) -> None:
    """Update the severity flag of a marking.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    marking_id : int
        The Marking.id to update.
    is_severe : bool
        Whether the marking should be flagged as severe.
    """
    with session_factory() as session:
        marking = session.get(Marking, marking_id)
        if marking is not None:
            marking.is_severe = is_severe
            session.commit()


def update_marking_comment(
    session_factory: sessionmaker,
    marking_id: int,
    comment: str,
) -> None:
    """Update the free-text comment of a marking.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    marking_id : int
        The Marking.id to update.
    comment : str
        The new comment text.
    """
    with session_factory() as session:
        marking = session.get(Marking, marking_id)
        if marking is not None:
            marking.comment = comment or None
            session.commit()


def load_usability_score(
    session_factory: sessionmaker, ref_id: int, user_id: int
) -> int | None:
    """Fetch the shared usability score for a reference, if one exists.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    ref_id : int
        The Reference.id to look up.
    user_id : int
        The ID of the current user.

    Returns
    -------
    int | None
        The usability score, or ``None`` if the item hasn't been rated yet.
    """
    with session_factory() as session:
        ref = session.execute(
            select(Reference).where(
                Reference.id == ref_id,
                Reference.project == UserAccess.project,
                Reference.department == UserAccess.department,
                UserAccess.user_id == user_id,
            )
        ).scalar_one_or_none()

        if ref is None:
            return None

        assessment = session.execute(
            select(AssessmentUsability).where(
                AssessmentUsability.evaluation_item_id
                == ref.evaluation_item_relation.id,
            )
        ).scalar_one_or_none()

        return assessment.usability_score if assessment is not None else None


def save_usability_assessment(
    session_factory: sessionmaker,
    evaluation_item_id: int,
    usability_score: int,
    user_id: int,
) -> None:
    """Create or update the usability score for an item.

    New scores are overwritten if an assessment already exists.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    evaluation_item_id : int
        The EvaluationItem.id being assessed.
    usability_score : int
        The usability score, from 1 to 5.
    user_id : int
        The ID of the current user.
    """
    with session_factory() as session:
        assessment = session.execute(
            select(AssessmentUsability).where(
                AssessmentUsability.evaluation_item_id == evaluation_item_id,
            )
        ).scalar_one_or_none()

        if assessment is not None:
            assessment.usability_score = usability_score
            assessment.timestamp = datetime.now()
        else:
            session.add(
                AssessmentUsability(
                    user_id=user_id,
                    evaluation_item_id=evaluation_item_id,
                    usability_score=usability_score,
                    comments=None,
                    timestamp=datetime.now(),
                )
            )
        session.commit()
