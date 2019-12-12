mesito
======

Mesito provides a minimalist Manufacturing Execution System (MES).


Contributing
============
We are very grateful for and welcome contributions: be it opening of the issues,
discussing future features or submitting pull requests.

To submit a pull request:

* Fork the repository and create a feature branch.
* In the repository root, create the virtual environment:

.. code-block:: bash

    python3 -m venv venv

* Activate the virtual environment:

.. code-block:: bash

    source venv/bin/activate

* Install the development dependencies:

.. code-block:: bash

    pip3 install -e .[dev]

* Implement your changes.
* Run precommit.py to execute pre-commit checks locally.
* Commit your changes and create a pull request.

Versioning
==========
We follow `Semantic Versioning <http://semver.org/spec/v1.0.0.html>`_. The version X.Y.Z indicates:

* X is the major version (backward-incompatible),
* Y is the minor version (backward-compatible), and
* Z is the patch version (backward-compatible bug fix).
