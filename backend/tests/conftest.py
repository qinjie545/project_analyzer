import os
import pytest
from flask import Flask

# Ensure app import uses relative package
os.environ.setdefault('FLASK_ENV', 'test')

@pytest.fixture(scope='session')
def app():
    from backend import api_server as api
    # init sqlite in-memory for tests
    from backend.utils.db import init_engine, Base
    engine = init_engine(override_url='sqlite+pysqlite:///:memory:')
    if engine is not None:
        Base.metadata.create_all(engine)
    api.app.config.update(TESTING=True)
    yield api.app

@pytest.fixture()
def client(app: Flask):
    return app.test_client()
