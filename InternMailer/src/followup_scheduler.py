import sqlite3
import logging
import time
from typing import Optional

logging.basicConfig(level=logging.INFO)

class FollowupScheduler:
    """
    Schedules and tracks follow-up emails using SQLite.
    """
    def __init__(self, db_path: str = 'followups.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS followups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    first_sent INTEGER,
                    followup1_sent INTEGER,
                    followup2_sent INTEGER,
                    completed INTEGER DEFAULT 0
                )
            ''')

    def log_first_send(self, email: str):
        now = int(time.time())
        with self.conn:
            self.conn.execute('INSERT INTO followups (email, first_sent) VALUES (?, ?)', (email, now))
        logging.info(f"Logged first send for {email}")

    def schedule_followups(self):
        now = int(time.time())
        with self.conn:
            cur = self.conn.execute('SELECT id, email, first_sent, followup1_sent, followup2_sent, completed FROM followups WHERE completed=0')
            for row in cur.fetchall():
                id, email, first_sent, f1, f2, completed = row
                if not f1 and now - first_sent > 7*24*3600:
                    self.conn.execute('UPDATE followups SET followup1_sent=? WHERE id=?', (now, id))
                    logging.info(f"Scheduled first follow-up for {email}")
                elif f1 and not f2 and now - f1 > 7*24*3600:
                    self.conn.execute('UPDATE followups SET followup2_sent=? WHERE id=?', (now, id))
                    logging.info(f"Scheduled second follow-up for {email}")
                elif f2 and now - f2 > 2*24*3600:
                    self.conn.execute('UPDATE followups SET completed=1 WHERE id=?', (id,))
                    logging.info(f"Marked follow-ups completed for {email}")

    def mark_completed(self, email: str):
        with self.conn:
            self.conn.execute('UPDATE followups SET completed=1 WHERE email=?', (email,))
        logging.info(f"Marked follow-ups completed for {email}")

# TODO: Add unit tests for FollowupScheduler 