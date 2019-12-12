#!/usr/bin/env python3
"""Run precommit checks on the repository."""
import argparse
import os
import pathlib
import re
import subprocess
import sys


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        help="Overwrites the unformatted source files with the "
        "well-formatted code in place. If not set, "
        "an exception is raised if any of the files do not conform "
        "to the style guide.",
        action='store_true')

    args = parser.parse_args()

    overwrite = bool(args.overwrite)

    src_root = pathlib.Path(__file__).parent

    if overwrite:
        print('Removing trailing whitespace...')
        for pth in (sorted((src_root / "mesito").glob("**/*.py")) + sorted(
            (src_root / "tests").glob("**/*.py")) +
                    [src_root / "precommit.py"]):
            pth.write_text(
                re.sub(r'[ \t]+$', '', pth.read_text(), flags=re.MULTILINE))

    print("YAPF'ing...")
    if overwrite:
        # yapf: disable
        subprocess.check_call([
            "yapf", "--in-place", "--style=style.yapf", "--recursive",
            "tests", "mesito", "setup.py", "precommit.py"],
            cwd=src_root.as_posix())
        # yapf: enable
    else:
        # yapf: disable
        subprocess.check_call([
            "yapf", "--diff", "--style=style.yapf", "--recursive",
            "tests", "mesito", "setup.py", "precommit.py"],
            cwd=src_root.as_posix())
        # yapf: enable

    print("Mypy'ing...")
    subprocess.check_call(["mypy", "--strict", "mesito", "tests"],
                          cwd=src_root.as_posix())

    print("Pydocstyle'ing...")
    subprocess.check_call(["pydocstyle", "mesito"], cwd=src_root.as_posix())

    print("Pylint'ing...")
    subprocess.check_call(["pylint", "--rcfile=pylint.rc", "tests", "mesito"],
                          cwd=src_root.as_posix())

    print("Testing...")
    env = os.environ.copy()
    env['ICONTRACT_SLOW'] = 'true'

    # yapf: disable
    subprocess.check_call(
        ["coverage", "run",
         "--source", "mesito",
         "-m", "unittest", "discover", "tests"],
        cwd=src_root.as_posix(),
        env=env)
    # yapf: enable

    subprocess.check_call(["coverage", "report"])

    print("Doctesting...")
    for pth in (sorted(
        (src_root / "mesito").glob("**/*.py")) + [src_root / "README.rst"]):
        subprocess.check_call(["python3", "-m", "doctest", pth.as_posix()])

    print("Checking with twine ...")
    subprocess.check_call(["python3", "setup.py", "sdist"],
                          cwd=src_root.as_posix())

    subprocess.check_call(["twine", "check", "dist/*"], cwd=src_root.as_posix())

    return 0


if __name__ == "__main__":
    sys.exit(main())
