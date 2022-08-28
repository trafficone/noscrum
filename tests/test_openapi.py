import tempfile
import pytest
from json import loads
from openapi3_fuzzer import FuzzIt
from flask_testing import TestCase
import schemathesis
import noscrum.noscrum_api as noscrum
from flask_login import FlaskLoginClient
import logging

logger = logging.getLogger()


@pytest.fixture()
def app():
    """
    Create Test NoScrum Flask Application
    """
    test_config = dict()
    test_config["SECRET_KEY"] = "TESTING_KEY"
    test_config["TESTING"] = True
    test_config["DEBUG"] = False
    test_config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    test_config["APPLICATION_ROOT"] = "/"
    test_config["SERVER_NAME"] = "localhost.localdomain"
    logger.info("Creating App - Testing")
    app = noscrum.create_app(test_config)
    app.test_client_class = FlaskLoginClient
    # other setup goes here
    yield app
    # cleanup goes here


@pytest.fixture()
def client(app):
    """
    Return standard test client for Flask App
    """
    return app.test_client()


OPENAPI_PATH = "openapi/openapi.json"


@pytest.fixture()
def openapi_filepath(client, app):
    with app.app_context():
        response = client.get(OPENAPI_PATH)
    f = tempfile.NamedTemporaryFile(mode="w+t", delete=False)
    f.write(str(response.data, "utf-8"))
    filename = f.name
    f.close()
    return filename


@pytest.fixture()
def bearer_token(app):
    # TODO: I have no idea how to implement this
    return None


"""
@pytest.fixture(name='schema')
def schema_fixture(openapi_filepath):
    with open(openapi_filepath,'r') as f:
        schema = schemathesis.from_file(f)
    return schema

@pytest.fixture()
def test_api_wrapper(schema):
    return schema.parametrize()(lambda case: case.call_and_validate())

def test_api(test_api_wrapper):
    test_api_wrapper()
"""
schema = schemathesis.from_uri("http://localhost:5000/" + OPENAPI_PATH)


@schema.parametrize()
def test_api(case, bearer_token):
    case.call_and_validate(headers={"Authorization": "Bearer <MY-TOKEN>"})


def test_api_fuzzing(openapi_filepath, bearer_token):
    class TestAPIFuzz(TestCase):
        def test_fuzzing(self):
            pass
            # FuzzIt(openapi_filepath,berer_token,self)
