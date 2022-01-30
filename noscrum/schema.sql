DROP TABLE IF EXISTS epic;
DROP TABLE IF EXISTS sprint;
DROP TABLE IF EXISTS story;
DROP TABLE IF EXISTS tag;
DROP TABLE IF EXISTS tag_story;
DROP TABLE IF EXISTS task;
DROP TABLE IF EXISTS work;
CREATE TABLE epic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic TEXT UNIQUE NOT NULL,
    deadline DATE,
    color text,
    userid INTEGER REFERENCES user(id) NOT NULL
);

CREATE TABLE sprint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    startDate DATE NOT NULL,
    endDate DATE NOT NULL,
    userid INTEGER REFERENCES user(id) NOT NULL
);

CREATE TABLE story (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story TEXT NOT NULL,
    epic_id INTEGER NOT NULL,
    prioritization INTEGER NOT NULL DEFAULT 1,
    deadline DATE,
    FOREIGN KEY (epic_id) REFERENCES epic (id),
    userid INTEGER REFERENCES user(id) NOT NULL
);

CREATE TABLE tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT UNIQUE NOT NULL,
    userid INTEGER REFERENCES user(id) NOT NULL
);

CREATE TABLE tag_story (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tagID INTEGER NOT NULL,
    story_id INTEGER NOT NULL,
    FOREIGN KEY (tagID) REFERENCES tag (id),
    FOREIGN KEY (story_id) REFERENCES story (id),
    userid INTEGER REFERENCES user(id) NOT NULL
);

CREATE TABLE task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    story_id INTEGER NOT NULL,
    sprint_id INTEGER,
    estimate NUMBER,
    actual NUMBER,
    deadline DATE,
    recurring BOOLEAN,
    status TEXT NOT NULL DEFAULT 'To-Do',
    FOREIGN KEY (story_id) REFERENCES story (id),
    FOREIGN KEY (sprint_id) REFERENCES sprint (id),
    userid INTEGER REFERENCES user(id) NOT NULL
);

CREATE TABLE work (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_date DATE NOT NULL DEFAULT CURRENT_DATE,
    hours_worked NUMBER NOT NULL DEFAULT 0,
    task_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES task (id),
    userid INTEGER REFERENCES user(id) NOT NULL
);

CREATE TABLE schedule_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES task(id) NOT NULL,
    sprint_id INTEGER REFERENCES sprint(id) NOT NULL,
    sprint_day DATE NOT NULL,
    sprint_hour INTEGER NOT NULL,
    note TEXT,
    userid INTEGER REFERENCES user(id) NOT NULL
)

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    user_salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT NOT NULL,
    message_opt_in BOOLEAN NOT NULL DEFAULT 0
);