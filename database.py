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

    # Shared SELECT projection used by search() and get()
    _MEMBER_SELECT = (
        "SELECT m.member_id, m.reg_area, m.reg_code,"
        " m.reg_area || '-' || m.reg_code AS display_id,"
        " TRIM(m.name_korean) AS name,"
        " TRIM(m.baptismal_name) AS baptismal_name,"
        " TRIM(m.district) AS district,"
        " m.address, m.postal_code,"
        " m.phone_cell, m.phone_home, m.phone_work, m.email,"
        " m.birth_date, m.sex,"
        " TRIM(f.head_of_household) AS head_of_household,"
        " TRIM(f.relation) AS relation,"
        " COALESCE(f.dues_paying, 0) AS dues_paying,"
        " f.monthly_amount AS monthly_dues,"
        " f.dues_start_date AS dues_start,"
        " f.dues_last_date AS dues_last_paid,"
        " COALESCE(f.notes, m.notes) AS notes,"
        " CASE WHEN ms.status='inactive' THEN 1 ELSE 0 END AS is_inactive"
        " FROM member m"
        " LEFT JOIN family f ON f.member_id=m.member_id"
        " LEFT JOIN member_status ms ON ms.member_id=m.member_id"
    )

    def search(self, q="", district=""):
        # Only show real parishioners (numeric reg_area), not placeholder-only members
        sql = self._MEMBER_SELECT + " WHERE m.reg_area GLOB '[0-9]*'"
        p = []
        if q:
            sql += (
                " AND (TRIM(m.name_korean) LIKE ? OR TRIM(m.baptismal_name) LIKE ?"
                " OR (m.reg_area || '-' || m.reg_code) LIKE ?"
                " OR TRIM(f.head_of_household) LIKE ?)"
            )
            p += [f"%{q}%"] * 4
        if district:
            sql += " AND TRIM(m.district)=?"
            p.append(district)
        sql += " ORDER BY m.reg_area, CAST(m.reg_code AS INTEGER)"
        with self._conn() as c:
            return c.execute(sql, p).fetchall()

    def get(self, pno):
        with self._conn() as c:
            return c.execute(
                self._MEMBER_SELECT + " WHERE m.member_id=?",
                (int(pno),),
            ).fetchone()

    def household(self, head, exclude=None):
        with self._conn() as c:
            base = (
                "SELECT m.member_id,"
                " m.reg_area || '-' || m.reg_code AS display_id,"
                " TRIM(m.name_korean) AS name,"
                " TRIM(m.baptismal_name) AS baptismal_name,"
                " TRIM(f.relation) AS relation"
                " FROM member m"
                " LEFT JOIN family f ON f.member_id=m.member_id"
                " WHERE TRIM(f.head_of_household)=?"
            )
            if exclude:
                return c.execute(
                    base + " AND m.member_id!=? ORDER BY m.member_id",
                    (head, int(exclude)),
                ).fetchall()
            return c.execute(base + " ORDER BY m.member_id", (head,)).fetchall()

    def next_no(self, area_code):
        # Only consider rows with the real numeric area code (exclude placeholder prefixes)
        with self._conn() as c:
            rows = c.execute(
                "SELECT reg_code FROM member"
                " WHERE reg_area=? AND reg_area GLOB '[0-9]*'",
                (area_code,),
            ).fetchall()
        hi = 0
        for r in rows:
            try:
                hi = max(hi, int(r[0].strip()))
            except Exception:
                pass
        return f"{area_code}-{str(hi + 1).zfill(5)}"

    def create(self, data):
        # data has flat keys matching old schema; split into member + family rows
        display_id = data.get("member_id", "")
        if "-" in display_id:
            reg_area, reg_code = display_id.split("-", 1)
        else:
            reg_area, reg_code = "", display_id

        with self._conn() as c:
            c.execute(
                "INSERT INTO member (reg_area, reg_code, name_korean, baptismal_name, district)"
                " VALUES (?,?,?,?,?)",
                (
                    reg_area,
                    reg_code,
                    data.get("name", ""),
                    data.get("baptismal_name", "") or "",
                    data.get("district", "") or "",
                ),
            )
            new_mid = c.lastrowid
            c.execute(
                "INSERT INTO family"
                " (member_id, head_of_household, relation, dues_paying,"
                "  monthly_amount, dues_start_date, dues_last_date, notes)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (
                    new_mid,
                    data.get("head_of_household", "") or "",
                    data.get("relation", "") or "",
                    1 if data.get("dues_paying") in (1, "Y", "1", True) else 0,
                    data.get("monthly_dues") or None,
                    data.get("dues_start", "") or "",
                    data.get("dues_last_paid", "") or "",
                    data.get("notes", "") or "",
                ),
            )
            c.execute(
                "INSERT OR IGNORE INTO member_status (member_id, status) VALUES (?, 'active')",
                (new_mid,),
            )
            c.commit()

    def update(self, pno, data):
        mid = int(pno)
        with self._conn() as c:
            c.execute(
                "UPDATE member SET name_korean=?, baptismal_name=?, district=?"
                " WHERE member_id=?",
                (
                    data.get("name", ""),
                    data.get("baptismal_name", "") or "",
                    data.get("district", "") or "",
                    mid,
                ),
            )
            # Upsert family row (may not exist for members imported from sacrament records)
            existing_family = c.execute(
                "SELECT family_id FROM family WHERE member_id=?", (mid,)
            ).fetchone()
            dues = 1 if data.get("dues_paying") in (1, "Y", "1", True) else 0
            if existing_family:
                c.execute(
                    "UPDATE family SET head_of_household=?, relation=?, dues_paying=?,"
                    " monthly_amount=?, dues_start_date=?, dues_last_date=?, notes=?"
                    " WHERE member_id=?",
                    (
                        data.get("head_of_household", "") or "",
                        data.get("relation", "") or "",
                        dues,
                        data.get("monthly_dues") or None,
                        data.get("dues_start", "") or "",
                        data.get("dues_last_paid", "") or "",
                        data.get("notes", "") or "",
                        mid,
                    ),
                )
            else:
                c.execute(
                    "INSERT INTO family"
                    " (member_id, head_of_household, relation, dues_paying,"
                    "  monthly_amount, dues_start_date, dues_last_date, notes)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (
                        mid,
                        data.get("head_of_household", "") or "",
                        data.get("relation", "") or "",
                        dues,
                        data.get("monthly_dues") or None,
                        data.get("dues_start", "") or "",
                        data.get("dues_last_paid", "") or "",
                        data.get("notes", "") or "",
                    ),
                )
            c.commit()

    def hard_delete(self, pno):
        with self._conn() as c:
            c.execute("DELETE FROM member WHERE member_id=?", (int(pno),))
            c.commit()

    # ── Sacrament records ────────────────────────────────────────────────────

    def get_baptism_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM baptism WHERE member_id=? ORDER BY baptism_date",
                (int(pno),),
            ).fetchall()

    def get_confirmation_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM confirmation WHERE member_id=? ORDER BY confirmation_date",
                (int(pno),),
            ).fetchall()

    def get_wedding_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM wedding"
                " WHERE groom_member_id=? OR bride_member_id=?"
                " ORDER BY wedding_date",
                (int(pno), int(pno)),
            ).fetchall()

    def get_death_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM status_death WHERE member_id=? ORDER BY death_date",
                (int(pno),),
            ).fetchall()

    # ── Move-in / Move-out records ───────────────────────────────────────────

    def get_movein_record(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM move_in WHERE member_id=? LIMIT 1",
                (int(pno),),
            ).fetchone()

    def get_moveout_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM move_out WHERE member_id=? ORDER BY moveout_date",
                (int(pno),),
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
        # Inserts into status_death (new schema); also marks member as deceased
        mid = int(data.get("member_id", 0))
        with self._conn() as c:
            c.execute(
                "INSERT INTO status_death (member_id, death_date, cemetery, last_rites_date, viaticum)"
                " VALUES (?,?,?,?,?)",
                (
                    mid,
                    data.get("death_date", "") or "",
                    data.get("cemetery", "") or "",
                    data.get("last_rites_date", "") or "",
                    data.get("viaticum", "") or "",
                ),
            )
            c.execute(
                "INSERT INTO member_status (member_id, status) VALUES (?, 'deceased')"
                " ON CONFLICT(member_id) DO UPDATE SET status='deceased'",
                (mid,),
            )
            c.commit()

    # ── Statistics ───────────────────────────────────────────────────────────

    def stats(self):
        with self._conn() as c:
            active   = c.execute(
                "SELECT COUNT(*) FROM member_status WHERE status='active'"
            ).fetchone()[0]
            lapsed   = c.execute(
                "SELECT COUNT(*) FROM member_status WHERE status='inactive'"
            ).fetchone()[0]
            baptisms = c.execute("SELECT COUNT(*) FROM baptism").fetchone()[0]
            weddings = c.execute("SELECT COUNT(*) FROM wedding").fetchone()[0]
            areas    = c.execute(
                "SELECT TRIM(m.district) area, COUNT(*) cnt"
                " FROM member m"
                " WHERE m.reg_area GLOB '[0-9]*'"
                " GROUP BY TRIM(m.district) ORDER BY cnt DESC"
            ).fetchall()
        return dict(active=active, lapsed=lapsed, baptisms=baptisms, weddings=weddings, areas=areas)
