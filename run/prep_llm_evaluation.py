"""This script loads the evaluation data into the database.

If the database does not exist yet, this script initialises it.
"""

import csv
import logging
import os
from pathlib import Path
from typing import Literal, cast

from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from umcu_ai_utils.database_connection import get_engine

from umcu_ai_apps.llm_evaluation.models import (
    Base,
    Context,
    EvaluationItem,
    Reference,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Select the database environment within the .env file
load_dotenv()

db_env = cast(
    Literal["PROD", "ACC", "DEBUG"],
    os.getenv("DB_ENVIRONMENT"),
)

engine = get_engine(
    db_env=db_env,
    schema_name=Reference.__table__.schema,
)

logger.info("Using database environment: %s", db_env)

Base.metadata.create_all(bind=engine)

SESSIONMAKER = sessionmaker(bind=engine)


class EvaluationRow(BaseModel):
    """Class representing a row in the evaluation data CSV file."""

    reference_id: int
    reference_description: str
    department: str | None = None
    context_text: str
    llm_response: str
    model: str | None = None


def add_evaluation_row(session: Session, row: EvaluationRow) -> None:
    """Add one evaluation row and its related records to the database."""

    reference = Reference(
        reference_id=row.reference_id,
        reference_description=row.reference_description,
        department=row.department,
    )
    session.add(reference)

    # Get reference.id before creating related records.
    session.flush()

    session.add_all(
        [
            EvaluationItem(
                reference_id=reference.id,
                llm_response=row.llm_response,
                model=row.model,
            ),
            Context(
                reference_id=reference.id,
                context_text=row.context_text,
            ),
        ]
    )


def prep_evaluation(evaluation_data_path: Path) -> None:
    """Load, validate, and insert evaluation data into the database.

    Existing entries are skipped based on reference_id.

    Parameters
    ----------
    evaluation_data_path : Path
        Path to the CSV file containing evaluation data.
    """

    # Open with explicit encoding and replace errors to avoid decode failures.
    with evaluation_data_path.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as f:
        reader = csv.DictReader(f)
        rows = [EvaluationRow.model_validate(row) for row in reader]

    if not rows:
        logger.warning("No data to insert into database.")
        return

    with SESSIONMAKER() as session:
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
                    "Skipping reference_id %s from department %s "
                    "— already exists in database.",
                    row.reference_id,
                    row.department,
                )
                skipped += 1
                continue

            add_evaluation_row(session, row)

            # Also prevents duplicate reference_ids within the CSV itself.
            existing_reference_ids.add(row.reference_id)
            inserted += 1

        session.commit()

        logger.info(
            "Insert complete. Inserted: %d, Skipped: %d.",
            inserted,
            skipped,
        )


if __name__ == "__main__":
    evaluation_data_path = (
        Path(__file__).parents[1] / "data" / "processed" / "llm_evaluation_data.csv"
    )

    prep_evaluation(evaluation_data_path)
