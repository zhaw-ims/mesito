#!/usr/bin/env python3
"""Run a mesito server."""

# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports

import gevent.monkey

gevent.monkey.patch_all()

import logging
import argparse

import sqlalchemy
import sqlalchemy.orm


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


    socketio, app = mesito.app.produce(session_factory=session_factory)

    app.logger.info("Serving forever on port {} ...".format(args.port))

    #http_server = WSGIServer(('', 8000), app, handler_class=WebSocketHandler)
    #mesito.app.register_server(server=http_server, app=app)

    #http_server.serve_forever()
    #app.config['SECRET_KEY'] = 'secret!'


    #app.run(port=port)
    socketio.run(app)
    app.logger.info("Goodbye.")


if __name__ == "__main__":
    main()
