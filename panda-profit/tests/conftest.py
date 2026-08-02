"""Shared pytest configuration for the Panda Profit test suite.

Several test modules repoint ``database.DB_PATH`` at a throwaway database in
``setUpClass`` but never put it back in ``tearDownClass``. That leaks the last
test database into whatever module runs next, making the suite order
dependent -- and, worse, leaves DB_PATH pointing somewhere unexpected.

The autouse fixture below snapshots ``database.DB_PATH`` before each test
module and restores it afterwards, so no module can affect another. It is
module scoped, which means it is set up *before* and torn down *after*
unittest's class-scoped ``setUpClass`` / ``tearDownClass`` fixtures.
"""

import os
import sys

import pytest

# Make the project root importable regardless of how pytest is invoked
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module", autouse=True)
def restore_db_path():
    """Restore database.DB_PATH after every test module."""
    import database

    original_db_path = database.DB_PATH
    try:
        yield
    finally:
        database.DB_PATH = original_db_path
