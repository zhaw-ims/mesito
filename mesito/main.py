#!/usr/bin/env python3
"""Run a mesito server."""

# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports
import platform

import gevent.monkey
from gevent import signal

gevent.monkey.patch_all()

import logging
import argparse

import sqlalchemy
import sqlalchemy.orm
import gevent.pywsgi

import mesito.app

logging.basicConfig(level=logging.INFO)


def main() -> None:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port", help="port on which to serve", required=True, type=int)
    parser.add_argument(
        "--database_url",
        help="SQLAlchemy database URL; "
        "see https://docs.sqlalchemy.org/en/13/core/engines.html",
        required=True)
    args = parser.parse_args()
    port = int(args.port)
    database_url = str(args.database_url)

    engine = sqlalchemy.create_engine(database_url)
    session_factory = sqlalchemy.orm.scoped_session(
        sqlalchemy.orm.sessionmaker(bind=engine))

    server = gevent.pywsgi.WSGIServer(listener=('0.0.0.0', port))

    app = mesito.app.produce(session_factory=session_factory)

    server.application = app

    def shutdown() -> None:
        """Signal the server to shut down gracefully."""
        app.logger.info("Signalling the server to shut down...")
        server.stop()

    if platform.system() in ['Linux', 'Darwin']:
        gevent.signal(signal.SIGTERM, shutdown)
        gevent.signal(signal.SIGINT, shutdown)
    else:
        raise NotImplementedError(
            "Unhandled gracefull shutdown for platform system: {}".format(
                platform.system()))

    app.logger.info("Serving forever on port {} ...".format(args.port))
    server.serve_forever()

    app.logger.info("Goodbye.")


if __name__ == "__main__":
    main()
