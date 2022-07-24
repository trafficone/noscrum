"""
Test the base functionality of NoScrum
- Index Loads
- Logged-in Index Page Loads
- Task Showcase Loads
- Sprint Showcase editable/non-editable loads
- User Profile Page Loads
- Login Page Loads 
  - Redirect happens for logged-in users
"""
import unittest
import logging
from flask import url_for
from flask_login import FlaskLoginClient
import pytest
import noscrum.noscrum_api as noscrum
import noscrum.noscrum_backend.user as backend_user
logger = logging.getLogger()

@pytest.fixture()
def app():
    """
    Create Test NoScrum Flask Application
    """
    test_config = dict()
    test_config['SECRET_KEY'] = 'TESTING_KEY'
    test_config['TESTING'] = True
    test_config['DEBUG'] = False
    test_config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    test_config['APPLICATION_ROOT'] = '/'
    test_config['SERVER_NAME'] = 'localhost.localdomain'
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

@pytest.fixture()
def runner(app):
    """
    Return Flask test CLI for NoScrum
    """
    return app.test_cli_runner()

@pytest.fixture()
def test_user():
    """
    Return the UserClass of a test user. 
    Creates user if doesn't exist.
    """
    user_record = backend_user.get_user_by_username('TEST_USER')
    if user_record is None:
        user = backend_user.UserClass.create_user(**{
            'username':'TEST_USER',
            'insecure_password':'test_password',
            'first_name':'Testerson'
        })
    else:
        user = backend_user.UserClass(user_record.id)
    return user

@pytest.fixture()
def logged_in_client(app,test_user):
    """
    Return a client which has a logged in test user.
    """
    return app.test_client(user=test_user)

def test_main_page(client,app):
    with app.app_context():
        response = client.get(url_for('semi_static.index'))
    assert response.status_code == 200
    assert b'Register' in response.data
    assert b'NoScrum' in response.data

def test_main_page_logged_in(logged_in_client,test_user,app):
    with app.app_context():
        response = logged_in_client.get(url_for('semi_static.index'))
    assert response.status_code == 200
    assert b'NoScrum' in response.data
    assert bytes(test_user.user.first_name,'utf-8') in response.data
    assert b'Incorrect Username' not in response.data

def test_logout(logged_in_client,app):
    with app.app_context():
        response = logged_in_client.get(url_for('user.logout'))
    assert response.status_code == 302
    assert b'<a href="/">' in response.data
    response2 = logged_in_client.get('/')
    assert b'Sign in' in response2.data


def test_task_showcase(logged_in_client,app):
    with app.app_context():
        response = logged_in_client.get(url_for('task.list_all'))
    assert response.status_code == 200
    assert b'Task Showcase' in response.data

def test_active_sprint(logged_in_client,app):
    with app.app_context():
        response = logged_in_client.get(url_for('sprint.active'))
    assert response.status_code == 200
    assert b'Editing Sprint Showcase' in response.data

def test_sprint_list(logged_in_client,app):
    with app.app_context():
        response = logged_in_client.get(url_for('sprint.list_all'))
    assert response.status_code == 200
    assert b'All Sprints' in response.data

def test_search_results(logged_in_client,app):
    with app.app_context():
        response = logged_in_client.get(url_for('search.query')+'?s=')
    assert response.status_code == 200
    assert b'Search Results' in response.data


if __name__ == '__main__':
    unittest.main()
