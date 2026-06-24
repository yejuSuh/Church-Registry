import sqlite3
from datetime import datetime


class DB:
    def __init__(self, path):
        self.path = path
        self._init_users()

    def _conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init_users(self):
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS app_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    baptism_name TEXT NOT NULL DEFAULT '—',
                    user_level TEXT NOT NULL DEFAULT 'staff',
                    created_at TEXT,
                    last_login TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            try:
                c.execute("ALTER TABLE app_users ADD COLUMN baptism_name TEXT NOT NULL DEFAULT '—'")
            except sqlite3.OperationalError:
                pass
            c.commit()
            if c.execute("SELECT COUNT(*) FROM app_users").fetchone()[0] == 0:
                self.create_user("admin", "admin1234", "관리자", "—", "admin")

    # ── User / auth methods ──────────────────────────────────────────────────

    def get_user(self, username):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM app_users WHERE username=?", (username,)
            ).fetchone()

    def verify_login(self, username, password):
        import bcrypt
        user = self.get_user(username)
        if not user:
            return None
        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return user
        return None

    def username_exists(self, username):
        with self._conn() as c:
            return c.execute(
                "SELECT 1 FROM app_users WHERE username=?", (username,)
            ).fetchone() is not None

    def create_user(self, username, password, name, baptism_name="—", user_level="staff"):
        import bcrypt
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._conn() as c:
            c.execute(
                "INSERT INTO app_users"
                " (username, password_hash, name, baptism_name, user_level, created_at)"
                " VALUES (?,?,?,?,?,?)",
                (username, pw_hash, name, baptism_name, user_level, now),
            )
            c.commit()

    def update_user(self, username, name, baptism_name, user_level, password=None):
        if password:
            import bcrypt
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            with self._conn() as c:
                c.execute(
                    "UPDATE app_users SET name=?, baptism_name=?, user_level=?, password_hash=?"
                    " WHERE username=?",
                    (name, baptism_name, user_level, pw_hash, username),
                )
                c.commit()
        else:
            with self._conn() as c:
                c.execute(
                    "UPDATE app_users SET name=?, baptism_name=?, user_level=? WHERE username=?",
                    (name, baptism_name, user_level, username),
                )
                c.commit()

    def update_user_level(self, username, new_level):
        with self._conn() as c:
            c.execute(
                "UPDATE app_users SET user_level=? WHERE username=?", (new_level, username)
            )
            c.commit()

    def deactivate_user(self, username):
        with self._conn() as c:
            c.execute("UPDATE app_users SET is_active=0 WHERE username=?", (username,))
            c.commit()

    def activate_user(self, username):
        with self._conn() as c:
            c.execute("UPDATE app_users SET is_active=1 WHERE username=?", (username,))
            c.commit()

    def delete_user(self, username):
        with self._conn() as c:
            target = c.execute(
                "SELECT user_level FROM app_users WHERE username=?", (username,)
            ).fetchone()
            if target and target["user_level"] == "admin":
                admin_count = c.execute(
                    "SELECT COUNT(*) FROM app_users WHERE user_level='admin'"
                ).fetchone()[0]
                if admin_count <= 1:
                    return False
            c.execute("DELETE FROM app_users WHERE username=?", (username,))
            c.commit()
        return True

    def list_users(self):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM app_users ORDER BY user_level, username"
            ).fetchall()

    def find_username_by_name(self, name, baptism_name):
        with self._conn() as c:
            return c.execute(
                "SELECT username FROM app_users WHERE name=? AND baptism_name=? AND is_active=1",
                (name, baptism_name),
            ).fetchall()

    def reset_password_by_identity(self, username, name, baptism_name, new_password):
        import bcrypt
        with self._conn() as c:
            row = c.execute(
                "SELECT id FROM app_users WHERE username=? AND name=? AND baptism_name=? AND is_active=1",
                (username, name, baptism_name),
            ).fetchone()
            if not row:
                return False
            pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            c.execute(
                "UPDATE app_users SET password_hash=? WHERE username=?",
                (pw_hash, username),
            )
            c.commit()
        return True

    def update_last_login(self, username):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._conn() as c:
            c.execute(
                "UPDATE app_users SET last_login=? WHERE username=?", (now, username)
            )
            c.commit()

    # ── Member queries ───────────────────────────────────────────────────────

    def search(self, q="", district=""):
        sql = (
            "SELECT r.member_id, TRIM(r.name) name, TRIM(r.baptismal_name) baptismal_name,"
            " TRIM(r.district) district, TRIM(r.head_of_household) head_of_household,"
            " TRIM(r.relation) relation, r.dues_paying,"
            " CASE WHEN EXISTS(SELECT 1 FROM inactive i WHERE i.member_id=r.member_id)"
            "      THEN 1 ELSE 0 END AS is_inactive"
            " FROM registration r WHERE 1=1"
        )
        p = []
        if q:
            sql += (" AND (TRIM(r.name) LIKE ? OR TRIM(r.baptismal_name) LIKE ?"
                    " OR TRIM(r.member_id) LIKE ? OR TRIM(r.head_of_household) LIKE ?)")
            p += [f"%{q}%"] * 4
        if district:
            sql += " AND TRIM(r.district)=?"
            p.append(district)
        sql += " ORDER BY r.member_id"
        with self._conn() as c:
            return c.execute(sql, p).fetchall()

    def get(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT r.*,"
                " CASE WHEN EXISTS(SELECT 1 FROM inactive i WHERE i.member_id=r.member_id)"
                "      THEN 1 ELSE 0 END AS is_inactive"
                " FROM registration r WHERE r.member_id=?",
                (pno,),
            ).fetchone()

    def household(self, head, exclude=None):
        with self._conn() as c:
            base = (
                "SELECT member_id, TRIM(name) name, TRIM(relation) relation,"
                " TRIM(baptismal_name) baptismal_name"
                " FROM registration WHERE TRIM(head_of_household)=?"
            )
            if exclude:
                return c.execute(
                    base + " AND member_id!=? ORDER BY member_id", (head, exclude)
                ).fetchall()
            return c.execute(base + " ORDER BY member_id", (head,)).fetchall()

    def next_no(self, area_code):
        with self._conn() as c:
            rows = c.execute(
                "SELECT member_id FROM registration WHERE member_id LIKE ?",
                (f"{area_code}%",),
            ).fetchall()
        hi = 0
        for r in rows:
            try:
                hi = max(hi, int(r[0].strip().split("-")[1]))
            except Exception:
                pass
        return f"{area_code}-{str(hi + 1).zfill(5)}"

    def create(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO registration ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values()))
            c.commit()

    def update(self, pno, data):
        sets = ", ".join(f"{k}=?" for k in data)
        with self._conn() as c:
            c.execute(
                f"UPDATE registration SET {sets} WHERE member_id=?",
                list(data.values()) + [pno],
            )
            c.commit()

    def hard_delete(self, pno):
        with self._conn() as c:
            c.execute("DELETE FROM registration WHERE member_id=?", (pno,))
            c.commit()

    # ── Sacrament records ────────────────────────────────────────────────────

    def get_baptism_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM baptism WHERE TRIM(member_id)=? ORDER BY baptism_date",
                (pno,),
            ).fetchall()

    def get_confirmation_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM confirmation WHERE TRIM(member_id)=? ORDER BY confirmation_date",
                (pno,),
            ).fetchall()

    def get_wedding_records(self, pno):
        with self._conn() as c:
            reg = c.execute(
                "SELECT name FROM registration WHERE member_id=?", (pno,)
            ).fetchone()
            if not reg:
                return []
            name = (reg["name"] or "").strip()
            return c.execute(
                "SELECT * FROM wedding"
                " WHERE TRIM(groom_name)=? OR TRIM(bride_name)=?"
                " ORDER BY wedding_date",
                (name, name),
            ).fetchall()

    def get_death_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM death WHERE TRIM(member_id)=? ORDER BY death_date",
                (pno,),
            ).fetchall()

    # ── Move-in / Move-out records ───────────────────────────────────────────

    def get_movein_record(self, pno):
        with self._conn() as c:
            reg = c.execute(
                "SELECT name FROM registration WHERE member_id=?", (pno,)
            ).fetchone()
            if not reg:
                return None
            name = (reg["name"] or "").strip()
            return c.execute(
                "SELECT * FROM move_in WHERE TRIM(name)=? OR TRIM(head_of_household)=? LIMIT 1",
                (name, name),
            ).fetchone()

    def get_moveout_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM move_out WHERE TRIM(member_id)=? ORDER BY moveout_date",
                (pno,),
            ).fetchall()

    # ── Sacrament write methods ──────────────────────────────────────────────

    def create_baptism(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO baptism ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_confirmation_record(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO confirmation ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_wedding_record(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO wedding ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_death_record(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO death ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    # ── Statistics ───────────────────────────────────────────────────────────

    def stats(self):
        with self._conn() as c:
            active   = c.execute("SELECT COUNT(*) FROM registration").fetchone()[0]
            lapsed   = c.execute("SELECT COUNT(DISTINCT member_id) FROM inactive").fetchone()[0]
            baptisms = c.execute("SELECT COUNT(*) FROM baptism").fetchone()[0]
            weddings = c.execute("SELECT COUNT(*) FROM wedding").fetchone()[0]
            areas    = c.execute(
                "SELECT TRIM(district) area, COUNT(*) cnt"
                " FROM registration"
                " GROUP BY TRIM(district) ORDER BY cnt DESC"
            ).fetchall()
        return dict(active=active, lapsed=lapsed, baptisms=baptisms, weddings=weddings, areas=areas)
