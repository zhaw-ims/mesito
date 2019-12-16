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
            cwd=str(src_root))
        # yapf: enable
    else:
        # yapf: disable
        subprocess.check_call([
            "yapf", "--diff", "--style=style.yapf", "--recursive",
            "tests", "mesito", "setup.py", "precommit.py"],
            cwd=str(src_root))
        # yapf: enable

    print("Mypy'ing...")
    subprocess.check_call(["mypy", "--strict", "mesito", "tests"],
                          cwd=str(src_root))

    print("Pydocstyle'ing...")
    subprocess.check_call(["pydocstyle", "mesito"], cwd=str(src_root))

    print("Pylint'ing...")
    subprocess.check_call(["pylint", "--rcfile=pylint.rc", "tests", "mesito"],
                          cwd=str(src_root))

    print("Erasing any previous code coverage...")
    subprocess.check_call(['coverage', 'erase'])

    print("Running unit tests...")

    env = os.environ.copy()
    env['ICONTRACT_SLOW'] = 'true'

    # yapf: disable
    subprocess.check_call(
        ["coverage", "run",
         "-m", "unittest", "discover", "tests"],
        cwd=src_root.as_posix(),
        env=env)
    # yapf: enable

    print("Running component tests...")
    # yapf: disable
    subprocess.check_call(
        ['tests/component_test_mesito.py',
         '--port', '0',
         '--with_coverage'],
        cwd=str(src_root),
        env=env)  # yapf: enable

    subprocess.check_call(["coverage", "report"])

    print("Doctesting...")
    for pth in (sorted(
            (src_root / "mesito").glob("**/*.py")) + [src_root / "README.rst"]):
        subprocess.check_call(["python3", "-m", "doctest", str(pth)])

    print("Checking with twine ...")
    subprocess.check_call(["python3", "setup.py", "sdist"], cwd=str(src_root))

    subprocess.check_call(["twine", "check", "dist/*"], cwd=str(src_root))

    return 0


if __name__ == "__main__":
    sys.exit(main())
