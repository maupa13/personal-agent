"""Two daily text-only trial requests; persistent and atomic reservations."""
import hashlib
import threading
import time
import uuid

from db_compat import connect_app_db


class DemoService:
    LIMIT = 2

    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.RLock()
        self.slots = threading.BoundedSemaphore(2)

    def init_schema(self):
        with connect_app_db(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS demo_requests (
                    id TEXT PRIMARY KEY, visitor TEXT NOT NULL, ip TEXT NOT NULL,
                    created_at INTEGER NOT NULL, completed INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS demo_requests_time ON demo_requests(created_at);
            """)
            conn.commit()

    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode()).hexdigest()

    def _remaining(self, conn, visitor, ip):
        count = conn.execute(
            "SELECT COUNT(*) FROM demo_requests WHERE created_at>=? AND (visitor=? OR ip=?)",
            (int(time.time()) - 86400, self.digest(visitor), self.digest(ip)),
        ).fetchone()[0]
        return max(0, self.LIMIT - count)

    def remaining(self, visitor, ip):
        with self.lock, connect_app_db(self.db_path) as conn:
            conn.execute("DELETE FROM demo_requests WHERE created_at<? OR (completed=0 AND created_at<?)",
                         (int(time.time()) - 86400, int(time.time()) - 600))
            conn.commit()
            return self._remaining(conn, visitor, ip)

    def reserve(self, visitor, ip):
        with self.lock, connect_app_db(self.db_path) as conn:
            if self._remaining(conn, visitor, ip) <= 0:
                return None
            request_id = uuid.uuid4().hex
            conn.execute("INSERT INTO demo_requests(id,visitor,ip,created_at) VALUES(?,?,?,?)",
                         (request_id, self.digest(visitor), self.digest(ip), int(time.time())))
            conn.commit()
            return request_id

    def finish(self, request_id, success):
        with self.lock, connect_app_db(self.db_path) as conn:
            if success:
                conn.execute("UPDATE demo_requests SET completed=1 WHERE id=?", (request_id,))
            else:
                conn.execute("DELETE FROM demo_requests WHERE id=?", (request_id,))
            conn.commit()
