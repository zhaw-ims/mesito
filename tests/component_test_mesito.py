#!/usr/bin/env python3
"""Test mesito as a whole component."""

import argparse
import contextlib
import logging
import pathlib
import subprocess
import tempfile
import time

import requests

logging.basicConfig(level=logging.INFO)


def main() -> None:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port",
        help="port on which mesito will listen to",
        type=int,
        default=8000)
    parser.add_argument(
        '--with_coverage',
        help="If set, use coverage.py to call the commands",
        action="store_true")
    parser.add_argument("--forever", help="serve forever", action='store_true')
    args = parser.parse_args()

    port = int(args.port)
    with_coverage = bool(args.with_coverage)
    forever = bool(args.forever)

    with contextlib.ExitStack() as exit_stack:
        tmpdir = tempfile.TemporaryDirectory()
        exit_stack.push(tmpdir)

        database_url = 'sqlite:////{}'.format(
            pathlib.Path(tmpdir.name) / 'data.sqlite3')

        coverage_prefix = [] if not with_coverage else ['coverage', 'run', '-a']

        # yapf: disable
        subprocess.check_call(
            coverage_prefix + [
                'bin/mesito-setup',
                '--database_url', database_url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        # yapf: enable

        # yapf: disable
        proc = subprocess.Popen(
            coverage_prefix + [
                'bin/mesito',
                '--port', str(port),
                '--database_url', database_url,
                '--cors_allowed_all_origins'])
        # yapf: enable

        logging.info('Waiting for the server to start...')
        time.sleep(5)

        logging.info('Adding machines...')
        resp = requests.post(
            'http://localhost:{}/api/v1/machines'.format(port),
            json={
                'name': 'Some Machine'
            }).json()
        assert isinstance(resp, int)
        machine_id = resp

        logging.info('Added a machine with the ID: %d', machine_id)

        resp = requests.post(
            'http://localhost:{}/api/v1/machines'.format(port),
            json={
                'name': 'Another Machine'
            }).json()
        assert isinstance(resp, int)
        machine_id = resp

        logging.info('Added a machine with the ID: %d', machine_id)

        ##
        # Terminate
        ##

        if forever:
            logging.info("Sleeping forever...")
            while True:
                time.sleep(0.1)
        else:
            logging.info("Shutting down...")
            proc.terminate()

            while proc.poll() is None:
                time.sleep(0.1)

            if proc.returncode != 0:
                raise AssertionError(
                    ("Unexpected return code: {}").format(proc.returncode))


if __name__ == "__main__":
    main()
