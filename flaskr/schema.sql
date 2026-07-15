DROP TABLE IF EXISTS keys;
DROP TABLE IF EXISTS clubs;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS borrow_records;
DROP TABLE IF EXISTS activity_reports;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS club_messages;


CREATE TABLE clubs (
id INTEGER PRIMARY KEY AUTOINCREMENT,

name TEXT UNIQUE NOT NULL,

room_number TEXT NOT NULL,

leader_student_id TEXT,

status TEXT NOT NULL
DEFAULT 'locked',

message TEXT,

icon_color TEXT NOT NULL,

category TEXT NOT NULL
);



CREATE TABLE keys (
id INTEGER PRIMARY KEY AUTOINCREMENT,

club_id INTEGER NOT NULL,

key_number TEXT UNIQUE NOT NULL,

available INTEGER NOT NULL
DEFAULT 1,

FOREIGN KEY (club_id)
REFERENCES clubs(id)
);



CREATE TABLE members (
id INTEGER PRIMARY KEY AUTOINCREMENT,

student_id TEXT NOT NULL,

name TEXT NOT NULL,

club_id INTEGER NOT NULL,

role TEXT NOT NULL
DEFAULT 'member',

registered_at TIMESTAMP
DEFAULT CURRENT_TIMESTAMP,

UNIQUE(student_id, club_id),

FOREIGN KEY (club_id)
REFERENCES clubs(id)
);



CREATE TABLE borrow_records (
id INTEGER PRIMARY KEY AUTOINCREMENT,

club_id INTEGER NOT NULL,

student_id TEXT NOT NULL,

student_name TEXT NOT NULL,

key_number TEXT NOT NULL,

borrowed_at TIMESTAMP
DEFAULT CURRENT_TIMESTAMP,

returned_at TIMESTAMP,

FOREIGN KEY (club_id)
REFERENCES clubs(id)
);



CREATE TABLE activity_reports (
id INTEGER PRIMARY KEY AUTOINCREMENT,

club_id INTEGER NOT NULL,

reporter_name TEXT NOT NULL,

student_id TEXT NOT NULL,

report_date TEXT NOT NULL,

description TEXT NOT NULL,

created_at TIMESTAMP
DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY (club_id)
REFERENCES clubs(id)
);



CREATE TABLE favorites (
student_id TEXT NOT NULL,

club_id INTEGER NOT NULL,

PRIMARY KEY (
student_id,
club_id
),

FOREIGN KEY (club_id)
REFERENCES clubs(id)
);



CREATE TABLE club_messages (
id INTEGER PRIMARY KEY AUTOINCREMENT,

club_id INTEGER NOT NULL,

student_id TEXT NOT NULL,

sender_name TEXT NOT NULL,

content TEXT NOT NULL,

is_private INTEGER NOT NULL
DEFAULT 0,

created_at TIMESTAMP
DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY (club_id)
REFERENCES clubs(id)
);