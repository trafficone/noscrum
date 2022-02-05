import unittest
from unittest.mock import patch
from flask_testing import TestCase
from flask_user.tests.utils import utils_prepare_user
from flask import url_for
import noscrum

class noscrumTestCase(TestCase):
    test_user = None

    def create_app(self):
        test_config = dict()
        test_config['SECRET_KEY'] = 'TESTING_KEY'
        test_config['TESTING'] = True
        test_config['DEBUG'] = False
        test_config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:'
        print("Creating App - Testing")
        app = noscrum.create_app(test_config)
        return app

    def setUp(self):
        print("Setting up - testing")
        db = noscrum.db.get_db()
        db.create_all()
        self.test_user = utils_prepare_user(self.app)
        noscrumTestCase.test_user = self.test_user
        self.client = self.app.test_client()
        self.assertIsNotNone(self.app,'App Started')
        self.assertEqual(self.app.debug,False,'App Setup')

    def tearDown(self):
        pass

class noscrumBaseTest(noscrumTestCase):
    test_user = None 

    def test_main_page(self):
        response = self.client.get(url_for('semi_static.index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register',response.data)
        self.assertIn(b'NoScrum', response.data)

    @patch('flask_login.utils._get_user')
    def test_main_page_logged_in(self,current_user):
        user = self.test_user
        current_user.return_value = user
        with self.client as client:
            response = client.get(url_for('semi_static.index'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'NoScrum', response.data)
            self.assertIn(bytes(user.first_name,'UTF-8'),response.data)
            self.assertNotIn(b'Incorrect Username',response.data)

if __name__ == '__main__':
    unittest.main()
 

