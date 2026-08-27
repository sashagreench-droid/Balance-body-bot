import sqlite3
from pathlib import Path

DB_PATH = Path("bot.sqlite3")

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = connect()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY,
        name TEXT,
        current_day INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        reminder_hour INTEGER DEFAULT 9,
        reminder_sent_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS days (
        tg_id INTEGER,
        day INTEGER,
        status TEXT DEFAULT 'AVAILABLE',
        reflection TEXT,
        completed_at TEXT,
        PRIMARY KEY (tg_id, day)
    );
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER, day INTEGER, kind TEXT, value TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER, day INTEGER, file_id TEXT, caption TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER, day INTEGER, text TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS badges (
        tg_id INTEGER, badge TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (tg_id, badge)
    );
    CREATE TABLE IF NOT EXISTS system_items (
        tg_id INTEGER, field TEXT, value TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (tg_id, field)
    );
    """)
    # Safe migration for databases created by earlier versions.
    cols = {r["name"] for r in con.execute("PRAGMA table_info(users)").fetchall()}
    if "reminder_sent_date" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN reminder_sent_date TEXT")
    con.commit()
    con.close()

def ensure_user(tg_id, name):
    con = connect()
    con.execute("INSERT OR IGNORE INTO users(tg_id,name) VALUES(?,?)", (tg_id,name))
    for d in range(1,50):
        status = "AVAILABLE" if d == 1 else "LOCKED"
        con.execute("INSERT OR IGNORE INTO days(tg_id,day,status) VALUES(?,?,?)", (tg_id,d,status))
    con.commit(); con.close()

def user(tg_id):
    con=connect(); row=con.execute("SELECT * FROM users WHERE tg_id=?",(tg_id,)).fetchone(); con.close(); return row

def day_row(tg_id, day):
    con=connect(); row=con.execute("SELECT * FROM days WHERE tg_id=? AND day=?",(tg_id,day)).fetchone(); con.close(); return row

def start_day(tg_id, day):
    con=connect(); con.execute("UPDATE days SET status='IN_PROGRESS' WHERE tg_id=? AND day=? AND status='AVAILABLE'",(tg_id,day)); con.commit(); con.close()

def complete_day(tg_id, day, reflection):
    con=connect()
    row=con.execute("SELECT status FROM days WHERE tg_id=? AND day=?",(tg_id,day)).fetchone()
    if not row or row["status"] == "COMPLETED": con.close(); return False
    con.execute("UPDATE days SET status='COMPLETED', reflection=?, completed_at=CURRENT_TIMESTAMP WHERE tg_id=? AND day=?",(reflection,tg_id,day))
    if day < 49:
        con.execute("UPDATE days SET status='AVAILABLE' WHERE tg_id=? AND day=? AND status='LOCKED'",(tg_id,day+1))
    con.execute("UPDATE users SET current_day=? WHERE tg_id=?",(min(day+1,49),tg_id))
    con.commit(); con.close(); return True

def add_xp(tg_id, amount):
    con=connect(); con.execute("UPDATE users SET xp=xp+? WHERE tg_id=?",(amount,tg_id)); con.commit(); con.close()

def save_answer(tg_id,day,kind,value):
    con=connect(); con.execute("INSERT INTO answers(tg_id,day,kind,value) VALUES(?,?,?,?)",(tg_id,day,kind,str(value))); con.commit(); con.close()

def save_photo(tg_id,day,file_id,caption):
    con=connect(); con.execute("INSERT INTO photos(tg_id,day,file_id,caption) VALUES(?,?,?,?)",(tg_id,day,file_id,caption)); con.commit(); con.close()

def add_question(tg_id,day,text):
    con=connect(); cur=con.execute("INSERT INTO questions(tg_id,day,text) VALUES(?,?,?)",(tg_id,day,text)); con.commit(); qid=cur.lastrowid; con.close(); return qid

def add_badge(tg_id,badge):
    con=connect(); cur=con.execute("INSERT OR IGNORE INTO badges(tg_id,badge) VALUES(?,?)",(tg_id,badge)); changed=cur.rowcount; con.commit(); con.close(); return changed

def badges(tg_id):
    con=connect(); rows=con.execute("SELECT badge FROM badges WHERE tg_id=? ORDER BY created_at",(tg_id,)).fetchall(); con.close(); return [r["badge"] for r in rows]

def set_system_item(tg_id,field,value):
    con=connect(); con.execute("INSERT INTO system_items(tg_id,field,value,updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(tg_id,field) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP",(tg_id,field,value)); con.commit(); con.close()

def system_items(tg_id):
    con=connect(); rows=con.execute("SELECT field,value FROM system_items WHERE tg_id=?",(tg_id,)).fetchall(); con.close(); return {r["field"]:r["value"] for r in rows}

def claim_reminder(tg_id, date_key):
    """Atomically claim today's reminder. Returns True only once per user/date."""
    con = connect()
    cur = con.execute(
        "UPDATE users SET reminder_sent_date=? WHERE tg_id=? AND (reminder_sent_date IS NULL OR reminder_sent_date<>?)",
        (date_key, tg_id, date_key),
    )
    con.commit(); con.close()
    return cur.rowcount == 1
