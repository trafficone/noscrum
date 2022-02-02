# NoScrum

NoScrum is not scrum, there are no scrums, you are one person and you need to get things done.

## Purpose

NoScrum came out of a need for personal project management tooling that was rich and 
versatile enough to meet my needs, without the overhead of managing all my projects via Excel.

## Installation

**WARNING: This is a Beta release, use at your own risk!**

Currently the installation "process" is to

- clone the repository
- create a venv
- install the requirements.txt
- create a .env file for the necessary environment variables
- use `flask run` (which is both slow and insecure)

``` bash
git clone git@github.com:trafficone/noscrum.git
cd noscrum
python -m venv venv
source venv/bin/activate #may be different depending on your environment
cat << EOF > .env
FLASK_ENV=dev
FLASK_APP=MyNoscrumApp
FLASK_SECRET_KEY=changeme
EOF
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt
flask run
```

Then install the Foundation platform along with jquery to the noscrum/static directory, such that
you have the following files:

- css/foundation-float.css
- css/jquery-ui.min.css
- js/jquery-ui.js
- js/vendor/foundation.js
- js/vendor/jquery.js
- js/vendor/what-input.js

A proper deployment process is in the backlog.

## Usage

### Terminology

If you're familiar with agile/scrum project management then you may be somewhat familiar with the
terminology below:

#### Scrum

A periodic meeting of everyone on the team. Since you are but one person, you won't be doing
this.^[However, having an accountability buddy can help]

#### Epic

This is the largest scale of a project, and it may not have a clearly defined end-goal yet. Things
like learning a language or earning a degree would be examples of epics.

#### Story

Under each *Epic* are multiple *Stories*, these have clearly defined goals, deadlines, and can be
broken down as needed into *Tasks*

#### Task

Each *Task* is an amount of work you can accomplish during a *Sprint*. It has a clear deadline,
goal, and scope. By breaking down work this way, a large project becomes several much more
manageable tasks.

#### Sprint

A *Sprint* is the periodic heartbeat of the NoScrum process. Each sprint is a set length, typically
a week or two, and the tasks assigned at the start of each sprint **should** be finished by the end.

### Process

Once you've added some of your epics, stories, and tasks to your backlog, you're ready to start your
first sprint. 

Each sprint involves four steps.

1. Backlog Management - Go through your backlog and make sure it's still leading you to success
2. Sprint Planning - Figure out what you're going to do during the week
3. Working - Have an awesome sprint and get stuff done!
4. Retrospective - What worked? What didn't? What should you change about *your* process?

Sprint planning starts from the backlog where you pick out the tasks you want to accomplish in this
sprint.

Sprint planning involves scheduling out the sprint in fine-grained chunks of time. You're not
obligated to stick to this plan, but it guarantees you know exactly what's planned for the sprint
before it's even started.

Think you bit off too much? Take it off the schedule and remember your capacity for next sprint.
Think you could do a bit more? You can add work mid-sprint if need be.
Did something you didn't plan on? You can add tasks without epics during the sprint. 

Don't sweat the process **during** the working phase. Just jot down what's happening, and get back
to it at the retrospective.

The retrospective is a **celebration** of what you did this sprint. If you didn't finish all your
tasks, that's not important. Meet yourself where you're at, and reward yourself for what you **did**
accomplish.

That's not to say every sprint is your best. It might help starting out to even have an epic
centered around tuning how to best fit NoScrum into your life.
