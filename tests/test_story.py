from re import T
import unittest
from unittest.mock import patch
from datetime import date
import noscrum
try:
    from test_base import noscrumTestCase
except ModuleNotFoundError:
    from .test_base import noscrumTestCase

<<<<<<< HEAD

class noscrumEpicTest(noscrumTestCase):

=======
class noscrumEpicTest(noscrumTestCase):
    
>>>>>>> main
    @patch('flask_login.utils._get_user')
    def create_story(self, current_user):
        user = self.test_user
        current_user.return_value = user
        if not self.story_created:
            self.story_created = True
<<<<<<< HEAD
            self.epic = noscrum.epic.create_epic(
                self.test_epic.epic, self.test_epic.color, self.test_epic.deadline)
=======
            self.epic = noscrum.epic.create_epic(self.test_epic.epic,self.test_epic.color,self.test_epic.deadline)
>>>>>>> main
            self.story = noscrum.story.create_story(
                self.test_story.epic_id,
                self.test_story.story,
                self.test_story.prioritization,
                self.test_story.deadline)
        return self.story
<<<<<<< HEAD

    def setUp(self):
        super().setUp()
        self.story_created = False
        self.test_epic = noscrum.db.Epic(
            epic='TEST EPIC', color='red', deadline=date(2022, 4, 15))
        self.test_story = noscrum.db.Story(story='TEST Story',
                                           prioritization=3,
                                           epic_id=1,
                                           deadline=date(2022, 4, 15),
                                           user_id=self.test_user.id)

    @patch('flask_login.utils._get_user')
    def test_create_story(self, current_user):
        user = self.test_user
        current_user.return_value = user
        story = self.create_story()
        self.assertIsNotNone(story, 'Story Exists')
        self.assertEquals(story.story, self.test_story.story,
                          'Story Name Created')
        self.assertEquals(
            story.epic_id, self.test_story.epic_id, 'Story Epic Created')
        self.assertEquals(
            story.deadline, self.test_story.deadline, 'Story Deadline Created')
        self.assertEquals(story.prioritization,
                          self.test_story.prioritization, 'Story Pri')

    @patch('flask_login.utils._get_user')
    def test_get_story(self, current_user):
=======
    
    def setUp(self):
        super().setUp()
        self.story_created = False
        self.test_epic = noscrum.db.Epic(epic='TEST EPIC',color='red',deadline=date(2022,4,15))
        self.test_story = noscrum.db.Story(story='TEST Story',
                                        prioritization=3,
                                        epic_id = 1,
                                        deadline=date(2022,4,15),
                                        user_id=self.test_user.id)

    @patch('flask_login.utils._get_user')
    def test_create_story(self,current_user):
        user = self.test_user
        current_user.return_value = user
        story = self.create_story()
        self.assertIsNotNone(story,'Story Exists')
        self.assertEquals(story.story,self.test_story.story,'Story Name Created')
        self.assertEquals(story.epic_id,self.test_story.epic_id,'Story Epic Created')
        self.assertEquals(story.deadline,self.test_story.deadline,'Story Deadline Created')
        self.assertEquals(story.prioritization,self.test_story.prioritization,'Story Pri')

    @patch('flask_login.utils._get_user')
    def test_get_story(self,current_user):
>>>>>>> main
        user = self.test_user
        current_user.return_value = user
        self.create_story()
        story = noscrum.story.get_story(self.story.id)
<<<<<<< HEAD
        self.assertIsNotNone(story, 'Story Found')
        self.assertEquals(story.id, self.story.id, 'Story ID Check')

    @patch('flask_login.utils._get_user')
    def test_get_null_story(self, current_user):
=======
        self.assertIsNotNone(story,'Story Found')
        self.assertEquals(story.id,self.story.id,'Story ID Check')

    @patch('flask_login.utils._get_user')
    def test_get_null_story(self,current_user):
>>>>>>> main
        user = self.test_user
        current_user.return_value = user
        self.create_story()
        null_story = noscrum.story.get_null_story_for_epic(self.epic.id)
        self.assertIsNotNone(null_story)
<<<<<<< HEAD
        self.assertEquals(null_story.epic_id, self.epic.id)
        self.assertIsNone(null_story.deadline)
        self.assertEquals(null_story.story, 'NULL')

    @patch('flask_login.utils._get_user')
    def test_get_stories_by_epic(self, current_user):
=======
        self.assertEquals(null_story.epic_id,self.epic.id)
        self.assertIsNone(null_story.deadline)
        self.assertEquals(null_story.story,'NULL')

    @patch('flask_login.utils._get_user')
    def test_get_stories_by_epic(self,current_user):
>>>>>>> main
        user = self.test_user
        current_user.return_value = user
        self.create_story()
        stories = noscrum.story.get_stories_by_epic(self.epic.id)
        for story in stories:
            if story.id == self.story.id:
<<<<<<< HEAD
                self.assertEquals(story.story, self.story.story)

    @patch('flask_login.utils._get_user')
    def test_update_story(self, current_user):
=======
                self.assertEquals(story.story,self.story.story)

    @patch('flask_login.utils._get_user')
    def test_update_story(self,current_user):
>>>>>>> main
        user = self.test_user
        current_user.return_value = user
        self.create_story()
        story = noscrum.story.update_story(self.story.id,
<<<<<<< HEAD
                                           self.story.story,
                                           self.story.epic_id,
                                           5,
                                           date(2022, 8, 12))
        self.assertEquals(story.prioritization, 5)
        self.assertEquals(story.deadline, date(2022, 8, 12))

    # def test_get_tag_story(self,current_user):

    # def


if __name__ == '__main__':
    unittest.main()
=======
                        self.story.story,
                        self.story.epic_id,
                        5,
                        date(2022,8,12))
        self.assertEquals(story.prioritization,5)
        self.assertEquals(story.deadline,date(2022,8,12))

    #def test_get_tag_story(self,current_user):

    #def 
    
if __name__ == '__main__':
    unittest.main()
>>>>>>> main
