"""This script loads the evaluation data into the database.

If the database does not exist yet, this script initialises it.
"""

import argparse
import csv
import logging
import os
from pathlib import Path
from typing import Literal, cast

from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker
from umcu_ai_utils.database_connection import get_engine

from umcu_ai_apps.config import configure_logging
from umcu_ai_apps.llm_evaluation.database.models import (
    Base,
    Context,
    EvaluationItem,
    Reference,
    User,
    UserAccess,
)

logger = logging.getLogger(__name__)


class EvaluationRow(BaseModel):
    """Class representing a row in the evaluation data CSV file."""

    reference_id: int
    reference_description: str
    department: str | None = None
    context_text: str
    llm_response: str
    model: str | None = None


def add_evaluation_row(session: Session, row: EvaluationRow, project: str) -> None:
    """Add one evaluation row and its related records to the database."""

    reference = Reference(
        reference_id=row.reference_id,
        reference_description=row.reference_description,
        project=project,
        department=row.department or "Unknown",
    )
    reference.evaluation_item_relation = EvaluationItem(
        llm_response=row.llm_response,
        model=row.model or "Unknown",
    )
    reference.context_relation = Context(context_text=row.context_text)

    session.add(reference)


def prep_evaluation(
    evaluation_data_path: Path, sessionmaker: sessionmaker, project: str
) -> None:
    """Load, validate, and insert evaluation data into the database
    for a specific project.

    Existing entries are skipped based on reference_id.

    Parameters
    ----------
    evaluation_data_path : Path
        Path to the CSV file containing evaluation data.
    sessionmaker : sessionmaker
        SQLAlchemy sessionmaker instance for database interaction.
    project : str
        Project associated with the evaluation data.
    """

    with evaluation_data_path.open(
        encoding="utf-8",
        newline="",
    ) as f:
        reader = csv.DictReader(f)
        rows = [EvaluationRow.model_validate(row) for row in reader]

    if not rows:
        logger.warning("No data to insert into database.")
        return

    with sessionmaker() as session:
        incoming_reference_ids = {row.reference_id for row in rows}

        existing_reference_ids = set(
            session.execute(
                select(Reference.reference_id).where(
                    Reference.reference_id.in_(incoming_reference_ids)
                )
            )
            .scalars()
            .all()
        )

        inserted = 0
        skipped = 0

        for row in rows:
            if row.reference_id in existing_reference_ids:
                logger.info(
                    f"Skipping reference_id {row.reference_id} from "
                    f"department {row.department} — already exists in database.",
                )
                skipped += 1
                continue

            add_evaluation_row(session, row, project)

            # Also prevents duplicate reference_ids within the CSV itself.
            existing_reference_ids.add(row.reference_id)
            inserted += 1

        session.commit()

        logger.info(f"Insert complete. Inserted: {inserted}, Skipped: {skipped}.")


def _setup_cli() -> Engine:
    configure_logging()
    load_dotenv()

    db_env = cast(
        Literal["PROD", "ACC", "DEBUG"],
        os.getenv("DB_ENVIRONMENT"),
    )

    engine = get_engine(
        db_env=db_env,
        schema_name=Reference.__table__.schema,
    )

    logger.info(f"Using database environment: {db_env}")
    return engine


def prep_llm_eval() -> None:
    """Main function to prepare evaluation data"""
    parser = argparse.ArgumentParser(
        description="Prepare evaluation data for the LLM evaluation app.",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to the CSV file containing evaluation data.",
    )
    parser.add_argument(
        "--project",
        "-p",
        dest="project",
        required=True,
        type=str,
        help="Project associated with the evaluation data.",
    )
    args = parser.parse_args()

    engine = _setup_cli()
    Base.metadata.create_all(bind=engine)

    prep_evaluation(args.path, sessionmaker(bind=engine), args.project)


def add_eval_user():
    """Add a new user to the database"""
    parser = argparse.ArgumentParser(
        description="Add a new user to the database.",
    )
    parser.add_argument(
        "email",
        type=str,
        help="Email address of the new user.",
    )
    parser.add_argument(
        "--project",
        "-p",
        dest="project",
        required=True,
        type=str,
        help="Project associated with the new user.",
    )
    parser.add_argument(
        "--department",
        "-d",
        dest="department",
        required=True,
        action="append",
        type=str,
        help="Department associated with the new user.",
    )
    args = parser.parse_args()

    engine = _setup_cli()
    Base.metadata.create_all(bind=engine)

    with sessionmaker(bind=engine)() as session:
        user = session.execute(
            select(User).where(User.email == args.email)
        ).scalar_one_or_none()
        if not user:
            user = User(email=args.email)

        for i in range(len(args.department)):
            user_access = UserAccess(
                project=args.project,
                department=args.department[i],
            )
            user.user_access_relation.append(user_access)

        session.add(user)
        session.commit()
        logger.info(
            "User added/modified with access to project "
            f"{args.project} and departments {', '.join(args.department)}"
        )


if __name__ == "__main__":
    prep_llm_eval()
