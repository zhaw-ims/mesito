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
import flask_socketio
import sqlalchemy
import sqlalchemy.orm

import mesito.app

logging.basicConfig(level=logging.INFO)


class Args:
    """Represent parsed program arguments."""

    def __init__(
            self, port: int, database_url: str,
            cors_allowed_all_origins: bool) -> None:
        """Initialize with the given values."""
        self.port = port
        self.database_url = database_url
        self.cors_allowed_all_origins = cors_allowed_all_origins

def parse_args(command_line_args: Sequence[str]) -> Args:
    """Parse the given command-line arguments and raise exceptions on errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",
                        help="port on which to serve",
                        required=True,
                        type=int)
    parser.add_argument(
        "--database_url",
        help="SQLAlchemy database URL; "
        "see https://docs.sqlalchemy.org/en/13/core/engines.html",
        required=True)
    parser.add_argument(
        "--cors_allowed_all_origins",
        help="If set, allows CORS on all origins",
        action="store_true"
    )
    args = parser.parse_args(args=command_line_args)

    return Args(
        port=int(args.port),
        database_url=str(args.database_url),
        cors_allowed_all_origins=bool(args.cors_allowed_all_origins))

# yapf: disable
def create_server(
    port: int,
    database_url: str,
    cors_allowed_all_origins: bool
) -> Tuple[
    flask.Flask,
    flask_socketio.SocketIO]:  # yapf: enable
    """Create the dependencies, the Flask application and the server."""
    engine = sqlalchemy.create_engine(database_url)
    session_factory = sqlalchemy.orm.scoped_session(
        sqlalchemy.orm.sessionmaker(bind=engine))

    app, socketio = mesito.app.produce(
        session_factory=session_factory,
        cors_allowed_all_origins=cors_allowed_all_origins)

    return app, socketio


def main(command_line_args: Sequence[str]) -> int:
    """Execute the main routine."""
    args = parse_args(command_line_args=command_line_args)

    app, socketio = create_server(
        port=args.port, database_url=args.database_url,
        cors_allowed_all_origins=args.cors_allowed_all_origins)

    def shutdown(signal_name: str) -> None:
        """Signal the server to shut down gracefully."""
        app.logger.info("Received signal: {}".format(signal_name))
        app.logger.info("Signalling the server to shut down...")
        socketio.stop()

    if platform.system() in ['Linux', 'Darwin']:
        signal.signal(signal.SIGTERM, lambda: shutdown('SIGTERM'))
        signal.signal(signal.SIGINT, lambda: shutdown('SIGINT'))
    else:
        raise NotImplementedError(
            "Unhandled gracefull shutdown for platform system: {}".format(
                platform.system()))

    app.logger.info("Serving forever on port {} ...".format(args.port))

    socketio.run(app=app, port=args.port)

    app.logger.info("Goodbye.")
    logging.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main(command_line_args=sys.argv[1:]))
