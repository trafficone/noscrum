"""
Use Playwright to execute tests via a browser
Tests from integration test list
"""
import re
import pytest
import logging
from flask import url_for
from playwright.sync_api import Page, expect
import noscrum.noscrum_api as noscrum
import noscrum.noscrum_backend.user as backend_user
logger = logging.getLogger()

TEST_PASSWORD = 'test_password'

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
            'insecure_password':TEST_PASSWORD,
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

@pytest.fixture()
def task_shocs_url(app):
    with app.app_context():
        url = url_for('task.list_all')
    return url

@pytest.fixture()
def all_sprints_url(app):
    with app.app_context():
        url = url_for('sprints.list_all')
    return url

@pytest.fixture(scope="function", autouse=True)
def before_each_after_each(page: Page, logged_in_client):
    with app.app_context():
        # verify user has been created and can log in
        response = logged_in_client.get(url_for('semi_static.index'))

def test_task_shocs_create_epic(page: Page, task_shocs_url):
    page.goto(task_shocs_url)


def test_task_shocs_epic_rename():
    pass

def test_task_shocs_epic_change_color():
    # FIXME: NOT IMPLEMENTED
    pass

def test_task_shocs_story_create():
    pass

def test_task_shocs_story_rename():
    pass

def test_task_shocs_story_set_deadline():
    pass

def test_task_shocs_archive_story():
    # Create separate story for this test
    pass

def test_task_shocs_task_create():
    pass

def test_task_shocs_task_deadline_set():
    pass

def test_task_shocs_task_deadline_update():
    pass

def test_task_shocs_task_name_update():
    pass

def test_task_shocs_task_est_update():
    pass

def test_task_shocs_task_status_update():
    pass

def test_task_shocs_task_make_recurring():
    pass

def test_task_shocs_filter_status():
    # Create 3 tasks, one of each status
    # Then test filter functionality
    pass

def test_task_shocs_filter_date_user():
    # Set deadline on 3 tasks to 3 consecutive days,
    # Set start filter after first
    # then end filter before last
    # then combine both
    pass

def test_task_shocs_filter_date_defaults():
    # update deadlines to 1,2, & 4 weeks out
    # test each filter
    pass

def test_task_shocs_sprint_plan():
    pass

def test_task_shocs_sprint_add_to():
    pass

def test_all_sprints_static():
    pass

def test_all_sprints_non_static():
    pass

def test_sprint_showcase_schedule_on_blank():
    pass

def test_sprint_showcase_schedule_recurring():
    pass

def test_sprint_showcase_schedlue_on_slot():
    pass

def test_sprint_showcase_set_note():
    pass

def test_sprint_showcase_do_not_schedule():
    # Back out of scheduling a task
    # Verify task was not scheduled
    pass

def test_sprint_showcase_stable():
    # Sprint showcase should be the same before+after reload
    pass

def test_sprint_showcase_reschedule_to_blank():
    pass

def test_sprint_showcase_reschedule_to_slot():
    pass

def test_sprint_showcase_unschedule():
    pass

def test_sprint_showcase_work_hours():
    pass

#CODEGEN
"""
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:5000/
    page.goto("http://localhost:5000/")

    # CREATE USER
    # Click text=Register for Free
    page.locator("text=Register for Free").click()
    # expect(page).to_have_url("http://localhost:5000/user/create")

    # Click input[name="username"]
    page.locator("input[name=\"username\"]").click()

    # Fill input[name="username"]
    page.locator("input[name=\"username\"]").fill("playwright_user")

    # Press Tab
    page.locator("input[name=\"username\"]").press("Tab")

    # Fill input[name="password"]
    page.locator("input[name=\"password\"]").fill("pw_pass")

    # Press Tab
    page.locator("input[name=\"password\"]").press("Tab")

    # Fill input[name="password_verify"]
    page.locator("input[name=\"password_verify\"]").fill("pw_pass")

    # Press Tab
    page.locator("input[name=\"password_verify\"]").press("Tab")

    # Press Tab
    page.locator("input[name=\"email\"]").press("Tab")

    # Fill input[name="firstname"]
    page.locator("input[name=\"firstname\"]").fill("pw_user")

    # Click text=Login
    page.locator("text=Login").click()
    # expect(page).to_have_url("http://localhost:5000/")

    # TASK BOARD
    # Click text=Task Board
    page.locator("text=Task Board").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click button:has-text("Create Epic")
    page.locator("button:has-text(\"Create Epic\")").click()

    # Click [placeholder="Thesis"]
    page.locator("[placeholder=\"Thesis\"]").click()

    # Fill [placeholder="Thesis"]
    page.locator("[placeholder=\"Thesis\"]").fill("PW_EPIC_CREATE")

    # Select purple
    page.locator("select[name=\"color\"]").select_option("purple")

    # Click section form >> text=Create
    page.locator("section form >> text=Create").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click text=PW_EPIC_CREATE
    page.locator("text=PW_EPIC_CREATE").click()

    # Click text=PW_EPIC_CREATE
    page.locator("text=PW_EPIC_CREATE").click()

    # Click text=PW_EPIC_CREATE
    page.locator("text=PW_EPIC_CREATE").click()

    # Press ArrowRight
    page.locator("text=PW_EPIC_CREATE").press("ArrowRight")

    # Press End with modifiers
    page.locator("text=PW_EPIC_CREATE").press("Shift+End")

    # Click text=Create Story >> nth=1
    page.locator("text=Create Story").nth(1).click()

    # Click input[name="story"]
    page.locator("input[name=\"story\"]").click()

    # Fill input[name="story"]
    page.locator("input[name=\"story\"]").fill("PW_CREATE_STORY")

    # Select 3
    page.locator("select[name=\"prioritization\"]").select_option("3")

    # Click section form >> text=Create
    page.locator("section form >> text=Create").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click text=Create Story >> nth=1
    page.locator("text=Create Story").nth(1).click()

    # Click input[name="story"]
    page.locator("input[name=\"story\"]").click()

    # Fill input[name="story"]
    page.locator("input[name=\"story\"]").fill("PW ARCHIVE_STORY")

    # Select 2
    page.locator("select[name=\"prioritization\"]").select_option("2")

    # Click section form >> text=Create
    page.locator("section form >> text=Create").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click #story_summary_24 >> text=Archive Story
    page.locator("#story_summary_24 >> text=Archive Story").click()

    # Click text=PW_CREATE_STORY
    page.locator("text=PW_CREATE_STORY").click()

    # Click text=PW_CREATE_STORY
    page.locator("text=PW_CREATE_STORY").click()

    # Press ArrowRight
    page.locator("text=PW_CREATE_STORY").press("ArrowRight")

    # Press End
    page.locator("text=PW_CREATE_STORY").press("End")

    # Press Enter
    page.locator("text=PW_CREATE_STORY").press("Enter")

    # Click #story_summary_23 >> text=Create Task
    page.locator("#story_summary_23 >> text=Create Task").click()

    # Click [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").click()

    # Fill [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").fill("PW_FIRST_TASK")

    # Click [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").click()

    # Fill [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").fill("1")

    # Click #story_summary_23 form button:has-text("Create")
    page.locator("#story_summary_23 form button:has-text(\"Create\")").click()

    # Click #story_summary_23 >> text=Create Task
    page.locator("#story_summary_23 >> text=Create Task").click()

    # Click [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").click()

    # Fill [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").fill("PW_SECOND_TASK")

    # Press Tab
    page.locator("[placeholder=\"Task Name\"]").press("Tab")

    # Fill [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").fill("2")

    # Press Enter
    page.locator("[placeholder=\"\\33 \\.5\"]").press("Enter")

    # Click #story_summary_23 >> text=Create Task
    page.locator("#story_summary_23 >> text=Create Task").click()

    # Click [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").click()

    # Fill [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").fill("PW_ThirdTask")

    # Click [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").click()

    # Fill [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").fill("3")

    # Press Tab
    page.locator("[placeholder=\"\\33 \\.5\"]").press("Tab")

    # Press Enter
    page.locator("#story_summary_23 form button:has-text(\"Create\")").press("Enter")

    # Click #story_summary_23 >> text=Create Task
    page.locator("#story_summary_23 >> text=Create Task").click()

    # Click [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").click()

    # Fill [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").fill("PW_RECURRING_TASK")

    # Click [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").click()

    # Fill [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").fill("24")

    # Click #story_summary_23 form button:has-text("Create")
    page.locator("#story_summary_23 form button:has-text(\"Create\")").click()

    # Click text=PW_ThirdTask
    page.locator("text=PW_ThirdTask").click()

    # Click text=PW_ThirdTask
    page.locator("text=PW_ThirdTask").click()

    # Press ArrowLeft
    page.locator("text=PW_ThirdTask").press("ArrowLeft")

    # Press End with modifiers
    page.locator("text=PW_ThirdTask").press("Shift+End")

    # Click span:has-text("24")
    page.locator("span:has-text(\"24\")").click()

    # Click #task_deadline_80
    page.locator("#task_deadline_80").click()

    # Click #ui-datepicker-div a:has-text("23")
    page.locator("#ui-datepicker-div a:has-text(\"23\")").click()

    # Click #task_deadline_81
    page.locator("#task_deadline_81").click()

    # Click #ui-datepicker-div >> text=24
    page.locator("#ui-datepicker-div >> text=24").click()

    # Click #task_deadline_82
    page.locator("#task_deadline_82").click()

    # Click #ui-datepicker-div >> text=25
    page.locator("#ui-datepicker-div >> text=25").click()

    # Click #task_83 >> text=One-Time
    page.locator("#task_83 >> text=One-Time").click()

    # Go to http://localhost:5000/task/
    page.goto("http://localhost:5000/task/")

    # Click #story_summary_23 >> text=One-Time >> nth=3
    page.locator("#story_summary_23 >> text=One-Time").nth(3).click()

    # Click #task_status_82
    page.locator("#task_status_82").click()

    # Click #task_status_81
    page.locator("#task_status_81").click()

    # Click #task_status_82
    page.locator("#task_status_82").click()

    # Click button:has-text("Status")
    page.locator("button:has-text(\"Status\")").click()

    # Uncheck input[name="to-do"]
    page.locator("input[name=\"to-do\"]").uncheck()

    # Uncheck input[name="in-progress"]
    page.locator("input[name=\"in-progress\"]").uncheck()

    # Click #status_filter_submit
    page.locator("#status_filter_submit").click()

    # Click button:has-text("Status")
    page.locator("button:has-text(\"Status\")").click()

    # Check input[name="in-progress"]
    page.locator("input[name=\"in-progress\"]").check()

    # Uncheck input[name="done"]
    page.locator("input[name=\"done\"]").uncheck()

    # Click #status_filter_submit
    page.locator("#status_filter_submit").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due Between: >> input[name="date"]
    page.locator("text=Due Between: >> input[name=\"date\"]").click()

    # Click #ui-datepicker-div a:has-text("23")
    page.locator("#ui-datepicker-div a:has-text(\"23\")").click()

    # Click #deadline_filter_submit
    page.locator("#deadline_filter_submit").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=and >> input[name="date"]
    page.locator("text=and >> input[name=\"date\"]").click()

    # Click #ui-datepicker-div a:has-text("23")
    page.locator("#ui-datepicker-div a:has-text(\"23\")").click()

    # Click #deadline_filter_submit
    page.locator("#deadline_filter_submit").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due in 1 Weeks
    page.locator("text=Due in 1 Weeks").click()

    # Click text=2022-07-24
    page.locator("text=2022-07-24").click()

    # Click #ui-datepicker-div a:has-text("31")
    page.locator("#ui-datepicker-div a:has-text(\"31\")").click()

    # Click text=2022-07-25
    page.locator("text=2022-07-25").click()

    # Click #ui-datepicker-div a:has-text("Next")
    page.locator("#ui-datepicker-div a:has-text(\"Next\")").click()

    # Click #ui-datepicker-div >> text=14
    page.locator("#ui-datepicker-div >> text=14").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due in 2 Weeks
    page.locator("text=Due in 2 Weeks").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due in 4 Weeks
    page.locator("text=Due in 4 Weeks").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due in 4 Weeks
    page.locator("text=Due in 4 Weeks").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # ---------------------
    context.storage_state(path="pw_auth.json")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
"""
"""
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:5000/
    page.goto("http://localhost:5000/")

    # Click text=Register for Free
    page.locator("text=Register for Free").click()
    # expect(page).to_have_url("http://localhost:5000/user/create")

    # Click input[name="username"]
    page.locator("input[name=\"username\"]").click()

    # Fill input[name="username"]
    page.locator("input[name=\"username\"]").fill("playwright_user")

    # Press Tab
    page.locator("input[name=\"username\"]").press("Tab")

    # Fill input[name="password"]
    page.locator("input[name=\"password\"]").fill("pw_pass")

    # Press Tab
    page.locator("input[name=\"password\"]").press("Tab")

    # Fill input[name="password_verify"]
    page.locator("input[name=\"password_verify\"]").fill("pw_pass")

    # Press Tab
    page.locator("input[name=\"password_verify\"]").press("Tab")

    # Press Tab
    page.locator("input[name=\"email\"]").press("Tab")

    # Fill input[name="firstname"]
    page.locator("input[name=\"firstname\"]").fill("pw_user")

    # Click text=Login
    page.locator("text=Login").click()
    # expect(page).to_have_url("http://localhost:5000/")

    # Click text=Task Board
    page.locator("text=Task Board").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click button:has-text("Create Epic")
    page.locator("button:has-text(\"Create Epic\")").click()

    # Click [placeholder="Thesis"]
    page.locator("[placeholder=\"Thesis\"]").click()

    # Fill [placeholder="Thesis"]
    page.locator("[placeholder=\"Thesis\"]").fill("PW_EPIC_CREATE")

    # Select purple
    page.locator("select[name=\"color\"]").select_option("purple")

    # Click section form >> text=Create
    page.locator("section form >> text=Create").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click text=PW_EPIC_CREATE
    page.locator("text=PW_EPIC_CREATE").click()

    # Click text=PW_EPIC_CREATE
    page.locator("text=PW_EPIC_CREATE").click()

    # Click text=PW_EPIC_CREATE
    page.locator("text=PW_EPIC_CREATE").click()

    # Press ArrowRight
    page.locator("text=PW_EPIC_CREATE").press("ArrowRight")

    # Press End with modifiers
    page.locator("text=PW_EPIC_CREATE").press("Shift+End")

    # Click text=Create Story >> nth=1
    page.locator("text=Create Story").nth(1).click()

    # Click input[name="story"]
    page.locator("input[name=\"story\"]").click()

    # Fill input[name="story"]
    page.locator("input[name=\"story\"]").fill("PW_CREATE_STORY")

    # Select 3
    page.locator("select[name=\"prioritization\"]").select_option("3")

    # Click section form >> text=Create
    page.locator("section form >> text=Create").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click text=Create Story >> nth=1
    page.locator("text=Create Story").nth(1).click()

    # Click input[name="story"]
    page.locator("input[name=\"story\"]").click()

    # Fill input[name="story"]
    page.locator("input[name=\"story\"]").fill("PW ARCHIVE_STORY")

    # Select 2
    page.locator("select[name=\"prioritization\"]").select_option("2")

    # Click section form >> text=Create
    page.locator("section form >> text=Create").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click #story_summary_24 >> text=Archive Story
    page.locator("#story_summary_24 >> text=Archive Story").click()

    # Click text=PW_CREATE_STORY
    page.locator("text=PW_CREATE_STORY").click()

    # Click text=PW_CREATE_STORY
    page.locator("text=PW_CREATE_STORY").click()

    # Press ArrowRight
    page.locator("text=PW_CREATE_STORY").press("ArrowRight")

    # Press End
    page.locator("text=PW_CREATE_STORY").press("End")

    # Press Enter
    page.locator("text=PW_CREATE_STORY").press("Enter")

    # Click #story_summary_23 >> text=Create Task
    page.locator("#story_summary_23 >> text=Create Task").click()

    # Click [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").click()

    # Fill [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").fill("PW_FIRST_TASK")

    # Click [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").click()

    # Fill [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").fill("1")

    # Click #story_summary_23 form button:has-text("Create")
    page.locator("#story_summary_23 form button:has-text(\"Create\")").click()

    # Click #story_summary_23 >> text=Create Task
    page.locator("#story_summary_23 >> text=Create Task").click()

    # Click [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").click()

    # Fill [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").fill("PW_SECOND_TASK")

    # Press Tab
    page.locator("[placeholder=\"Task Name\"]").press("Tab")

    # Fill [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").fill("2")

    # Press Enter
    page.locator("[placeholder=\"\\33 \\.5\"]").press("Enter")

    # Click #story_summary_23 >> text=Create Task
    page.locator("#story_summary_23 >> text=Create Task").click()

    # Click [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").click()

    # Fill [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").fill("PW_ThirdTask")

    # Click [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").click()

    # Fill [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").fill("3")

    # Press Tab
    page.locator("[placeholder=\"\\33 \\.5\"]").press("Tab")

    # Press Enter
    page.locator("#story_summary_23 form button:has-text(\"Create\")").press("Enter")

    # Click #story_summary_23 >> text=Create Task
    page.locator("#story_summary_23 >> text=Create Task").click()

    # Click [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").click()

    # Fill [placeholder="Task Name"]
    page.locator("[placeholder=\"Task Name\"]").fill("PW_RECURRING_TASK")

    # Click [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").click()

    # Fill [placeholder="\33 \.5"]
    page.locator("[placeholder=\"\\33 \\.5\"]").fill("24")

    # Click #story_summary_23 form button:has-text("Create")
    page.locator("#story_summary_23 form button:has-text(\"Create\")").click()

    # Click text=PW_ThirdTask
    page.locator("text=PW_ThirdTask").click()

    # Click text=PW_ThirdTask
    page.locator("text=PW_ThirdTask").click()

    # Press ArrowLeft
    page.locator("text=PW_ThirdTask").press("ArrowLeft")

    # Press End with modifiers
    page.locator("text=PW_ThirdTask").press("Shift+End")

    # Click span:has-text("24")
    page.locator("span:has-text(\"24\")").click()

    # Click #task_deadline_80
    page.locator("#task_deadline_80").click()

    # Click #ui-datepicker-div a:has-text("23")
    page.locator("#ui-datepicker-div a:has-text(\"23\")").click()

    # Click #task_deadline_81
    page.locator("#task_deadline_81").click()

    # Click #ui-datepicker-div >> text=24
    page.locator("#ui-datepicker-div >> text=24").click()

    # Click #task_deadline_82
    page.locator("#task_deadline_82").click()

    # Click #ui-datepicker-div >> text=25
    page.locator("#ui-datepicker-div >> text=25").click()

    # Click #task_83 >> text=One-Time
    page.locator("#task_83 >> text=One-Time").click()

    # Go to http://localhost:5000/task/
    page.goto("http://localhost:5000/task/")

    # Click #story_summary_23 >> text=One-Time >> nth=3
    page.locator("#story_summary_23 >> text=One-Time").nth(3).click()

    # Click #task_status_82
    page.locator("#task_status_82").click()

    # Click #task_status_81
    page.locator("#task_status_81").click()

    # Click #task_status_82
    page.locator("#task_status_82").click()

    # Click button:has-text("Status")
    page.locator("button:has-text(\"Status\")").click()

    # Uncheck input[name="to-do"]
    page.locator("input[name=\"to-do\"]").uncheck()

    # Uncheck input[name="in-progress"]
    page.locator("input[name=\"in-progress\"]").uncheck()

    # Click #status_filter_submit
    page.locator("#status_filter_submit").click()

    # Click button:has-text("Status")
    page.locator("button:has-text(\"Status\")").click()

    # Check input[name="in-progress"]
    page.locator("input[name=\"in-progress\"]").check()

    # Uncheck input[name="done"]
    page.locator("input[name=\"done\"]").uncheck()

    # Click #status_filter_submit
    page.locator("#status_filter_submit").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due Between: >> input[name="date"]
    page.locator("text=Due Between: >> input[name=\"date\"]").click()

    # Click #ui-datepicker-div a:has-text("23")
    page.locator("#ui-datepicker-div a:has-text(\"23\")").click()

    # Click #deadline_filter_submit
    page.locator("#deadline_filter_submit").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=and >> input[name="date"]
    page.locator("text=and >> input[name=\"date\"]").click()

    # Click #ui-datepicker-div a:has-text("23")
    page.locator("#ui-datepicker-div a:has-text(\"23\")").click()

    # Click #deadline_filter_submit
    page.locator("#deadline_filter_submit").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due in 1 Weeks
    page.locator("text=Due in 1 Weeks").click()

    # Click text=2022-07-24
    page.locator("text=2022-07-24").click()

    # Click #ui-datepicker-div a:has-text("31")
    page.locator("#ui-datepicker-div a:has-text(\"31\")").click()

    # Click text=2022-07-25
    page.locator("text=2022-07-25").click()

    # Click #ui-datepicker-div a:has-text("Next")
    page.locator("#ui-datepicker-div a:has-text(\"Next\")").click()

    # Click #ui-datepicker-div >> text=14
    page.locator("#ui-datepicker-div >> text=14").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due in 2 Weeks
    page.locator("text=Due in 2 Weeks").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due in 4 Weeks
    page.locator("text=Due in 4 Weeks").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click button:has-text("Deadline")
    page.locator("button:has-text(\"Deadline\")").click()

    # Click text=Due in 4 Weeks
    page.locator("text=Due in 4 Weeks").click()

    # Click text=Clear Filters
    page.locator("text=Clear Filters").click()

    # Click text=Sign out
    page.locator("text=Sign out").click()
    # expect(page).to_have_url("http://localhost:5000/")

    # Click text=Sign in
    page.locator("text=Sign in").click()
    # expect(page).to_have_url("http://localhost:5000/user/login")

    # Click input[name="username"]
    page.locator("input[name=\"username\"]").click()

    # Fill input[name="username"]
    page.locator("input[name=\"username\"]").fill("playwright_user")

    # Press Tab
    page.locator("input[name=\"username\"]").press("Tab")

    # Fill input[name="password"]
    page.locator("input[name=\"password\"]").fill("pw_pass")

    # Press Enter
    page.locator("input[name=\"password\"]").press("Enter")
    # expect(page).to_have_url("http://localhost:5000/user/login")

    # Go to http://localhost:5000/user/login
    page.goto("http://localhost:5000/user/login")

    # Click input[name="password"]
    page.locator("input[name=\"password\"]").click()

    # Fill input[name="password"]
    page.locator("input[name=\"password\"]").fill("pw_pass")

    # Press Enter
    page.locator("input[name=\"password\"]").press("Enter")
    # expect(page).to_have_url("http://localhost:5000/")

    # Click text=All Sprints
    page.locator("text=All Sprints").click()
    # expect(page).to_have_url("http://localhost:5000/sprint/")

    # Click text=View Sprint
    page.locator("text=View Sprint").click()
    # expect(page).to_have_url("http://localhost:5000/sprint/19")

    # Click #unsch_0_3 >> text=No Task Scheduled
    page.locator("#unsch_0_3 >> text=No Task Scheduled").click()

    # Go to http://localhost:5000/sprint/19
    page.goto("http://localhost:5000/sprint/19")

    # Click #unsch_0_3 >> text=No Task Scheduled
    page.locator("#unsch_0_3 >> text=No Task Scheduled").click()

    # Click #unsch_0_3 div >> nth=1
    page.locator("#unsch_0_3 div").nth(1).click()

    # Click text=2022-07-19 Tuesday Hours Scheduled for Day: 0 No Task Scheduled >> div >> nth=4
    page.locator("text=2022-07-19 Tuesday Hours Scheduled for Day: 0 No Task Scheduled >> div").nth(4).click()

    # Click text=Sprint Showcase From 2022-07-18 to 2022-07-24 Sprint List >> a
    page.locator("text=Sprint Showcase From 2022-07-18 to 2022-07-24 Sprint List >> a").click()
    # expect(page).to_have_url("http://localhost:5000/sprint/")

    # Click text=Schedule Sprint Tasks
    page.locator("text=Schedule Sprint Tasks").click()
    # expect(page).to_have_url("http://localhost:5000/sprint/19?static=False")

    # Click #unsch_0_3 >> text=No Task Scheduled - click to schedule
    page.locator("#unsch_0_3 >> text=No Task Scheduled - click to schedule").click()

    # Click text=Unschedule Task Add Unplanned Task Planned Tasks Recurring Tasks First Epic Crea >> [aria-label="Close"]
    page.locator("text=Unschedule Task Add Unplanned Task Planned Tasks Recurring Tasks First Epic Crea >> [aria-label=\"Close\"]").click()

    # Click text=Task Board
    page.locator("text=Task Board").click()
    # expect(page).to_have_url("http://localhost:5000/task/")

    # Click #sprintPlan
    page.locator("#sprintPlan").click()

    # Click a:has-text("23")
    page.locator("a:has-text(\"23\")").click()

    # Click #SprintPlanActivate
    page.locator("#SprintPlanActivate").click()

    # Click #task_sprint_btn_80
    page.locator("#task_sprint_btn_80").click()

    # Click #task_sprint_btn_81
    page.locator("#task_sprint_btn_81").click()

    # Click #task_sprint_btn_82
    page.locator("#task_sprint_btn_82").click()

    # Click #task_sprint_btn_83
    page.locator("#task_sprint_btn_83").click()

    # Click text=All Sprints
    page.locator("text=All Sprints").click()
    # expect(page).to_have_url("http://localhost:5000/sprint/")

    # Click text=Schedule Sprint Tasks
    page.locator("text=Schedule Sprint Tasks").click()
    # expect(page).to_have_url("http://localhost:5000/sprint/19?static=False")

    # Click #unsch_1_1 >> text=No Task Scheduled - click to schedule
    page.locator("#unsch_1_1 >> text=No Task Scheduled - click to schedule").click()

    # Click text=PW_FIRST_TASK
    page.locator("text=PW_FIRST_TASK").click()

    # Click #plan_hours_button
    page.locator("#plan_hours_button").click()

    # Click #unsch_2_1 >> text=No Task Scheduled - click to schedule
    page.locator("#unsch_2_1 >> text=No Task Scheduled - click to schedule").click()

    # Click text=Recurring Tasks
    page.locator("text=Recurring Tasks").click()

    # Click text=PW_RECURRING_TASK
    page.locator("text=PW_RECURRING_TASK").click()

    # Click text=Hours Hours must be a number. >> [placeholder="\32 "]
    page.locator("text=Hours Hours must be a number. >> [placeholder=\"\\32 \"]").click()

    # Fill text=Hours Hours must be a number. >> [placeholder="\32 "]
    page.locator("text=Hours Hours must be a number. >> [placeholder=\"\\32 \"]").fill("1")

    # Click #plan_hours_button
    # with page.expect_navigation(url="http://localhost:5000/sprint/19?static=False"):
    with page.expect_navigation():
        page.locator("#plan_hours_button").click()

    # Click text=Est:25.0 Plan:1.00 Worked This Day:0 Log Work >> [placeholder="Schedule-specific Note"]
    page.locator("text=Est:25.0 Plan:1.00 Worked This Day:0 Log Work >> [placeholder=\"Schedule-specific Note\"]").click()

    # Fill text=Est:25.0 Plan:1.00 Worked This Day:0 Log Work >> [placeholder="Schedule-specific Note"]
    page.locator("text=Est:25.0 Plan:1.00 Worked This Day:0 Log Work >> [placeholder=\"Schedule-specific Note\"]").fill("NOTE TEST")

    # Click #task_80_62 >> text=Log Work
    page.locator("#task_80_62 >> text=Log Work").click()

    # Click text=Hours: Hours worked must be a number. >> [placeholder="\32 "]
    page.locator("text=Hours: Hours worked must be a number. >> [placeholder=\"\\32 \"]").click()

    # Fill text=Hours: Hours worked must be a number. >> [placeholder="\32 "]
    page.locator("text=Hours: Hours worked must be a number. >> [placeholder=\"\\32 \"]").fill("1")

    # Click button:has-text("Log Work")
    page.locator("button:has-text(\"Log Work\")").click()

    # Click text=Est:1.0 Plan:1.00 Worked This Day:1 Log Work >> [placeholder="Schedule-specific Note"]
    page.locator("text=Est:1.0 Plan:1.00 Worked This Day:1 Log Work >> [placeholder=\"Schedule-specific Note\"]").click()

    # Fill text=Est:1.0 Plan:1.00 Worked This Day:1 Log Work >> [placeholder="Schedule-specific Note"]
    page.locator("text=Est:1.0 Plan:1.00 Worked This Day:1 Log Work >> [placeholder=\"Schedule-specific Note\"]").fill("NOTE")

    # Click #r_1_1 > div >> nth=0
    page.locator("#r_1_1 > div").first.click()

    # Click text=Sign out
    page.locator("text=Sign out").click()
    # expect(page).to_have_url("http://localhost:5000/")

    # ---------------------
    context.storage_state(path="pw_auth.json")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
"""