#!/usr/bin/env python3
"""Test mesito as a whole component."""

import argparse
import contextlib
import logging
import pathlib
import signal
import subprocess
import tempfile
import time

logging.basicConfig(level=logging.INFO)


def main() -> None:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port",
        help="port on which mesito will listen to",
        required=True,
        type=int)
    parser.add_argument("--forever", help="serve forever", action='store_true')
    args = parser.parse_args()

    port = int(args.port)
    forever = bool(args.forever)

    with contextlib.ExitStack() as exit_stack:
        tmpdir = tempfile.TemporaryDirectory()
        exit_stack.push(tmpdir)

        database_url = 'sqlite:////{}'.format(
            pathlib.Path(tmpdir.name) / 'data.sqlite3')

        subprocess.check_call(['mesito-setup', '--database_url', database_url])

        # yapf: disable
        proc = subprocess.Popen([
            'mesito',
            '--port', str(port),
            '--database_url', database_url])
        # yapf: enable
        exit_stack.callback(callback=proc.terminate)

        logging.info("Sleeping so that the server can properly start.")
        time.sleep(1)

        ##
        # Terminate
        ##

        if forever:
            logging.info("Sleeping forever...")
            while True:
                time.sleep(0.1)
        else:
            logging.info("Shutting down...")
            proc.send_signal(signal.SIGTERM)


if __name__ == "__main__":
    main()
