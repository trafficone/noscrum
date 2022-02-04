import unittest
import pytest
from flask_testing import TestCase
from flask_user import current_user
from flask_user.tests.utils import utils_prepare_user
from flask import url_for, app
from noscrum.db import get_db, User
import noscrum
from bs4 import BeautifulSoup

TEST_USER = 'testuser'
TEST_PASSWORD = 'Password1'

class noscrumBaseTest(TestCase):

    @pytest.fixture
    def session(request):
        return request.session()

    def create_app(self):
        test_config = dict()
        test_config['SECRET_KEY'] = 'TESTING_KEY'
        test_config['TESTING'] = True
        test_config['DEBUG'] = False
        test_config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:'
        app = noscrum.create_app(test_config)
        return app

    def setUp(self):
        self.test_user = utils_prepare_user(self.app)
        self.client = self.app.test_client()
        self.assertEqual(self.app.debug,False,'App Setup')

    def tearDown(self):
       pass

    def test_main_page(self):
        response = self.client.get(url_for('semi_static.index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register',response.data)
        self.assertIn(b'NoScrum', response.data)


    def test_main_page_logged_in(self):
        with self.client as client:
            u = self.test_user
            print(u.username,u.password)
            response = client.post(url_for('user.login'),
                json=dict(username=TEST_USER,password=TEST_PASSWORD))
            print(self.test_user)
            print(current_user)
            #print('data')
            #print(response.data)
            self.assert_redirects(response,url_for('semi_static.index'))
            self.assertFalse(current_user.is_anonymous)
            self.assertTrue(current_user.username==TEST_USER)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'NoScrum', response.data)
            self.assertIn(bytes(TEST_USER,'UTF-8'),response.data)
            self.assertNotIn(b'Incorrect Username',response.data)
            #self.assertNotIn(b'New here?',response.data)
            #self.assertNotIn(b'Register',response.data)


if __name__ == '__main__':
    unittest.main()
 

