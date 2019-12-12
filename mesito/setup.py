#!/usr/bin/env python3
"""Set up the database."""
import argparse
import logging

import sqlalchemy

import mesito.model

logging.basicConfig(level=logging.INFO)


def main() -> None:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database_url",
        help="SQLAlchemy database URL; "
        "see https://docs.sqlalchemy.org/en/13/core/engines.html",
        required=True)
    args = parser.parse_args()
    database_url = str(args.database_url)

    engine = sqlalchemy.create_engine(database_url)

    logging.info("Creating the database tables...")
    mesito.model.Base.metadata.create_all(engine)
    logging.info("The database tables have been created.")


if __name__ == "__main__":
    main()
