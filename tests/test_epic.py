import unittest
from unittest.mock import patch
from datetime import date
import noscrum
from .test_base import noscrumTestCase

class noscrumEpicTest(noscrumTestCase):
    epic_was_created = False
    epic = None

    @patch('flask_login.utils._get_user')
    def create_epic_once(self,current_user):
        user = self.test_user
        current_user.return_value = user
        if not self.epic_was_created:
            self.epic = noscrum.epic.create_epic(self.test_epic.epic,self.test_epic.color,self.test_epic.deadline)
            self.epic_was_created = True
        return self.epic

    def setUp(self):
        super().setUp()
        self.test_epic = noscrum.db.Epic(epic='TEST EPIC',color='red',deadline=date(2022,4,15),user_id=self.test_user.id)
        #db = noscrum.db.get_db()
        #db.session.add(self.test_epic)
        #db.session.commit()

    @patch('flask_login.utils._get_user')
    def testCreateEpic(self,current_user):
        user = self.test_user
        current_user.return_value = user
        epic = self.create_epic_once()
        self.assertIsNotNone(epic,'Epic Not None')
        self.assertEqual(epic.epic,self.test_epic.epic,'Epic Created')
        self.assertEqual(epic.color,self.test_epic.color,'Epic Color Created')
        self.assertEqual(epic.deadline,self.test_epic.deadline,'Epic Created with Deadline')
        self.assertEqual(epic.user_id,self.test_user.id,'Epic created for test user')

    @patch('flask_login.utils._get_user')
    def testGetEpic(self,current_user):
        user = self.test_user
        current_user.return_value = user
        # guarantee Epic is created
        self.create_epic_once()
        epic = noscrum.epic.get_epic(self.test_epic.id)
        self.assertIsNotNone(epic,'Epic Not None')
        self.assertEqual(epic.epic,self.test_epic.epic,'Epic Got by ID')

    @patch('flask_login.utils._get_user')
    def testGetEpicByName(self,current_user):
        user = self.test_user
        current_user.return_value = user
        self.create_epic_once()
        epic = noscrum.epic.get_epic_by_name(self.test_epic.epic)
        self.assertEqual(epic.epic,self.test_epic.epic,'Epic Got by Name')

    @patch('flask_login.utils._get_user')
    def testGetEpics(self,current_user):
        user = self.test_user
        current_user.return_value = user
        epics = noscrum.epic.get_epics()
        for epic in [_ for _ in epics if _.epic == self.test_epic.epic]:
            self.assertEqual(epic.epic,self.test_epic.epic,'Epic in Epics')
        # the database setup for the special case is too much for now :-/
    
if __name__ == '__main__':
    unittest.main()