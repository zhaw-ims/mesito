#!/usr/bin/env python3
"""Run a mesito server."""

# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports
import gevent.monkey
gevent.monkey.patch_all()

import logging
import argparse
import platform
import signal
import sys
from typing import Sequence, Tuple

import flask
import gevent.time
import gevent.pywsgi
import sqlalchemy
import sqlalchemy.orm

import mesito.app

logging.basicConfig(level=logging.INFO)


class Args:
    """Represent parsed program arguments."""

    def __init__(self, port: int, database_url: str) -> None:
        """Initialize with the given values."""
        self.port = port
        self.database_url = database_url


def parse_args(command_line_args: Sequence[str]) -> Args:
    """Parse the given command-line arguments and raise exceptions on errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port", help="port on which to serve", required=True, type=int)
    parser.add_argument(
        "--database_url",
        help="SQLAlchemy database URL; "
        "see https://docs.sqlalchemy.org/en/13/core/engines.html",
        required=True)
    args = parser.parse_args(args=command_line_args)
    port = int(args.port)
    database_url = str(args.database_url)

    return Args(port=port, database_url=database_url)


def create_app_and_server(port: int, database_url: str
                          ) -> Tuple[flask.Flask, gevent.pywsgi.WSGIServer]:
    """Create the dependencies, the Flask application and the server."""
    engine = sqlalchemy.create_engine(database_url)
    session_factory = sqlalchemy.orm.scoped_session(
        sqlalchemy.orm.sessionmaker(bind=engine))

    server = gevent.pywsgi.WSGIServer(listener=('0.0.0.0', port))

    app = mesito.app.produce(session_factory=session_factory)

    server.application = app

    return app, server


def main(command_line_args: Sequence[str]) -> int:
    """Execute the main routine."""
    args = parse_args(command_line_args=command_line_args)

    app, server = create_app_and_server(
        port=args.port, database_url=args.database_url)

    def shutdown(signal_name: str) -> None:
        """Signal the server to shut down gracefully."""
        app.logger.info("Received signal: {}".format(signal_name))
        app.logger.info("Signalling the server to shut down...")
        server.stop()

    if platform.system() in ['Linux', 'Darwin']:
        gevent.signal(signal.SIGTERM, lambda: shutdown('SIGTERM'))
        gevent.signal(signal.SIGINT, lambda: shutdown('SIGINT'))
    else:
        raise NotImplementedError(
            "Unhandled gracefull shutdown for platform system: {}".format(
                platform.system()))

    app.logger.info("Serving forever on port {} ...".format(args.port))

    def log_when_ready() -> None:
        """Log when the server is ready to serve."""
        while True:
            gevent.time.sleep(0.1)

            if server.started:
                app.logger.info("Server started.")

            if server.started or server.closed:
                break

    log_when_ready_task = gevent.spawn(log_when_ready)

    server.serve_forever()

    gevent.joinall([log_when_ready_task])

    app.logger.info("Goodbye.")
    logging.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main(command_line_args=sys.argv[1:]))
