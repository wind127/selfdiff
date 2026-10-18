import pytest
from selfdiff.store.database import Database


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / 'local.db')
    database.initialize()
    return database
