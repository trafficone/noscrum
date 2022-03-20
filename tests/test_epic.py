import unittest
from unittest.mock import patch
from flask import url_for
from datetime import date
import noscrum
try:
    from test_base import noscrumTestCase
except ModuleNotFoundError:
    from .test_base import noscrumTestCase


class noscrumEpicTest(noscrumTestCase):
    epic_was_created = False
    epic = None

    @patch('flask_login.utils._get_user')
<<<<<<< HEAD
    def create_epic_once(self, current_user):
        user = self.test_user
        current_user.return_value = user
        if not self.epic_was_created:
            self.epic = noscrum.epic.create_epic(
                self.test_epic.epic, self.test_epic.color, self.test_epic.deadline)
=======
    def create_epic_once(self,current_user):
        user = self.test_user
        current_user.return_value = user
        if not self.epic_was_created:
            self.epic = noscrum.epic.create_epic(self.test_epic.epic,self.test_epic.color,self.test_epic.deadline)
>>>>>>> main
            self.epic_was_created = True
        return self.epic

    def setUp(self):
        super().setUp()
<<<<<<< HEAD
        self.test_epic = noscrum.db.Epic(epic='TEST EPIC', color='red', deadline=date(
            2022, 4, 15), user_id=self.test_user.id)

    @patch('flask_login.utils._get_user')
    def test_create_epic(self, current_user):
        user = self.test_user
        current_user.return_value = user
        epic = self.create_epic_once()
        self.assertIsNotNone(epic, 'Epic Not None')
        self.assertEqual(epic.epic, self.test_epic.epic, 'Epic Created')
        self.assertEqual(epic.color, self.test_epic.color,
                         'Epic Color Created')
        self.assertEqual(epic.deadline, self.test_epic.deadline,
                         'Epic Created with Deadline')
        self.assertEqual(epic.user_id, self.test_user.id,
                         'Epic created for test user')

    @patch('flask_login.utils._get_user')
    def test_get_epic(self, current_user):
=======
        self.test_epic = noscrum.db.Epic(epic='TEST EPIC',color='red',deadline=date(2022,4,15),user_id=self.test_user.id)

    @patch('flask_login.utils._get_user')
    def test_create_epic(self,current_user):
        user = self.test_user
        current_user.return_value = user
        epic = self.create_epic_once()
        self.assertIsNotNone(epic,'Epic Not None')
        self.assertEqual(epic.epic,self.test_epic.epic,'Epic Created')
        self.assertEqual(epic.color,self.test_epic.color,'Epic Color Created')
        self.assertEqual(epic.deadline,self.test_epic.deadline,'Epic Created with Deadline')
        self.assertEqual(epic.user_id,self.test_user.id,'Epic created for test user')

    @patch('flask_login.utils._get_user')
    def test_get_epic(self,current_user):
>>>>>>> main
        user = self.test_user
        current_user.return_value = user
        # guarantee Epic is created
        self.create_epic_once()
        epic = noscrum.epic.get_epic(self.epic.id)
<<<<<<< HEAD
        self.assertIsNotNone(epic, 'Epic Not None')
        self.assertEqual(epic.epic, self.test_epic.epic, 'Epic Got by ID')

    @patch('flask_login.utils._get_user')
    def test_get_epic_by_name(self, current_user):
=======
        self.assertIsNotNone(epic,'Epic Not None')
        self.assertEqual(epic.epic,self.test_epic.epic,'Epic Got by ID')

    @patch('flask_login.utils._get_user')
    def test_get_epic_by_name(self,current_user):
>>>>>>> main
        user = self.test_user
        current_user.return_value = user
        self.create_epic_once()
        epic = noscrum.epic.get_epic_by_name(self.test_epic.epic)
<<<<<<< HEAD
        self.assertEqual(epic.epic, self.test_epic.epic, 'Epic Got by Name')

    @patch('flask_login.utils._get_user')
    def test_get_epics(self, current_user):
=======
        self.assertEqual(epic.epic,self.test_epic.epic,'Epic Got by Name')

    @patch('flask_login.utils._get_user')
    def test_get_epics(self,current_user):
>>>>>>> main
        user = self.test_user
        current_user.return_value = user
        epics = noscrum.epic.get_epics()
        for epic in [_ for _ in epics if _.epic == self.test_epic.epic]:
<<<<<<< HEAD
            self.assertEqual(epic.epic, self.test_epic.epic, 'Epic in Epics')
        # the database setup for the special case is too much for now :-/

    @patch('flask_login.utils._get_user')
    def test_update_epic(self, current_user):
=======
            self.assertEqual(epic.epic,self.test_epic.epic,'Epic in Epics')
        # the database setup for the special case is too much for now :-/
    
    @patch('flask_login.utils._get_user')
    def test_update_epic(self,current_user):
>>>>>>> main
        TEST_COLOR = "Blurple"
        user = self.test_user
        current_user.return_value = user
        self.create_epic_once()
<<<<<<< HEAD
        epic = noscrum.epic.update_epic(
            self.epic.id, self.epic.epic, TEST_COLOR, self.epic.deadline)
        self.assertEqual(epic.color, TEST_COLOR)

    @patch('flask_login.utils._get_user')
    def test_view_epic_page(self, current_user):
        user = self.test_user
        current_user.return_value = user
        self.create_epic_once()
        response = self.client.get(url_for('epic.show', epic_id=self.epic.id))
        self.assert200(response)
        self.assertIn(bytes(self.epic.epic, 'UTF-8'), response.data)

    @patch('flask_login.utils._get_user')
    def test_create_epic_api(self, current_user):
        user = self.test_user
        current_user.return_value = user
        with self.client:
            # self.client.post(url_for('user.login'),data={'username':user.username,'password':'Password1'})
            response = self.client.post(url_for('epic.create')+'?is_json=true',
                                        data={'epic': 'POST Create Epic',
                                              'color': 'POSTColor',
                                              'deadline': '2022-02-06'})
            self.assertIn(bytes('POST Create Epic', 'UTF-8'), response.data)


if __name__ == '__main__':
    unittest.main()
=======
        epic = noscrum.epic.update_epic(self.epic.id,self.epic.epic,TEST_COLOR,self.epic.deadline)
        self.assertEqual(epic.color,TEST_COLOR)

    @patch('flask_login.utils._get_user')
    def test_view_epic_page(self,current_user):
        user = self.test_user
        current_user.return_value = user
        self.create_epic_once()
        response = self.client.get(url_for('epic.show',epic_id = self.epic.id))
        self.assert200(response)
        self.assertIn(bytes(self.epic.epic,'UTF-8'),response.data)


    @patch('flask_login.utils._get_user')
    def test_create_epic_api(self,current_user):
        user = self.test_user
        current_user.return_value = user
        with self.client:
            #self.client.post(url_for('user.login'),data={'username':user.username,'password':'Password1'})
            response = self.client.post(url_for('epic.create')+'?is_json=true',
                data={'epic':'POST Create Epic',
                    'color':'POSTColor',
                    'deadline':'2022-02-06'})
            self.assertIn(bytes('POST Create Epic','UTF-8'), response.data)

if __name__ == '__main__':
    unittest.main()
>>>>>>> main
