import sqlite3
from datetime import datetime

from core.constants import AREAS


class DB:
    def __init__(self, path):
        self.path = path
        self._init_users()
        self._init_districts()
        self._migrate_schema()

    def _migrate_schema(self):
        # Additive column migrations, guarded so they run once per DB file.
        with self._conn() as c:
            wedding_cols = [r["name"] for r in c.execute("PRAGMA table_info(wedding)")]
            # spouse English names captured on the confirmation intake form
            for col in ("groom_name_english", "bride_name_english"):
                if col not in wedding_cols:
                    c.execute(f"ALTER TABLE wedding ADD COLUMN {col} TEXT")

            member_cols = [r["name"] for r in c.execute("PRAGMA table_info(member)")]
            if "phone_cell" in member_cols:
                c.execute("ALTER TABLE member RENAME COLUMN phone_cell TO phone")
            if "phone_home" in member_cols:
                c.execute("ALTER TABLE member DROP COLUMN phone_home")
            if "phone_work" in member_cols:
                c.execute("ALTER TABLE member DROP COLUMN phone_work")

            c.commit()

    def _conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        # SQLite has FK enforcement OFF by default per-connection; without this,
        # the schema's ON DELETE CASCADE / SET NULL rules are silently ignored
        # and deletes leave orphaned rows behind (see family/member_status).
        c.execute("PRAGMA foreign_keys = ON")
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

    def _init_districts(self):
        # reg_area is the stored source of truth for a member's 구역; the
        # human-readable name lives only in this lookup table and is joined in
        # at read time. area_code.txt is the authoritative code→name list
        # (parsed into constants.AREAS), so re-seed with REPLACE on every
        # startup: editing the file is all it takes to rename a district.
        with self._conn() as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS district ("
                " code TEXT PRIMARY KEY,"
                " name TEXT NOT NULL)"
            )
            c.executemany(
                "INSERT OR REPLACE INTO district (code, name) VALUES (?,?)", AREAS
            )
            c.commit()

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
        " TRIM(m.name_english) AS name_english,"
        " TRIM(m.baptismal_name) AS baptismal_name,"
        " d.name AS district,"
        " m.address, m.postal_code,"
        " m.phone, m.email,"
        " m.birth_date, m.sex,"
        " m.place_of_birth, m.occupation,"
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
        " LEFT JOIN district d ON d.code=m.reg_area"
    )

    def search(self, q="", area=""):
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
        if area:
            sql += " AND m.reg_area=?"
            p.append(area)
        sql += " ORDER BY m.reg_area, CAST(m.reg_code AS INTEGER)"
        with self._conn() as c:
            return c.execute(sql, p).fetchall()

    def get(self, pno):
        with self._conn() as c:
            return c.execute(
                self._MEMBER_SELECT + " WHERE m.member_id=?",
                (int(pno),),
            ).fetchone()

    def search_people(self, q, limit=10):
        # Used by PersonPicker to match godparent/sponsor/father/mother/spouse
        # fields on sacrament intake forms against existing parishioners.
        # Restricted to real registered members (numeric reg_area), same as
        # search() -- matching a placeholder/historical row isn't useful here.
        q = (q or "").strip()
        if not q:
            return []
        sql = (
            self._MEMBER_SELECT + " WHERE m.reg_area GLOB '[0-9]*'"
            " AND (TRIM(m.name_korean) LIKE ? OR TRIM(m.name_english) LIKE ?"
            " OR TRIM(m.baptismal_name) LIKE ?)"
            " ORDER BY m.reg_area, CAST(m.reg_code AS INTEGER) LIMIT ?"
        )
        p = [f"%{q}%"] * 3 + [limit]
        with self._conn() as c:
            return c.execute(sql, p).fetchall()

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
                "INSERT INTO member"
                " (reg_area, reg_code, name_korean, name_english, baptismal_name,"
                "  birth_date, sex, address, postal_code, phone, email,"
                "  place_of_birth, occupation)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    reg_area,
                    reg_code,
                    data.get("name", ""),
                    data.get("name_english") or None,
                    data.get("baptismal_name", "") or "",
                    data.get("birth_date") or None,
                    data.get("sex") or None,
                    data.get("address") or None,
                    data.get("postal_code") or None,
                    data.get("phone") or None,
                    data.get("email") or None,
                    data.get("place_of_birth") or None,
                    data.get("occupation") or None,
                ),
            )
            new_mid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
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
                "UPDATE member SET name_korean=?, name_english=?, baptismal_name=?,"
                " birth_date=?, sex=?, address=?, postal_code=?, phone=?, email=?,"
                " place_of_birth=?, occupation=?"
                " WHERE member_id=?",
                (
                    data.get("name", ""),
                    data.get("name_english") or None,
                    data.get("baptismal_name", "") or "",
                    data.get("birth_date") or None,
                    data.get("sex") or None,
                    data.get("address") or None,
                    data.get("postal_code") or None,
                    data.get("phone") or None,
                    data.get("email") or None,
                    data.get("place_of_birth") or None,
                    data.get("occupation") or None,
                    mid,
                ),
            )
            # Upsert family row (may not exist for members imported from sacrament records)
            existing_family = c.execute(
                "SELECT * FROM family WHERE member_id=?", (mid,)
            ).fetchone()

            # The parishioner form no longer carries dues fields, so fall back
            # to the stored values when a key is absent -- otherwise a plain
            # member edit would silently wipe the family's dues data.
            def dv(key, col, default):
                if key in data:
                    return data[key]
                return existing_family[col] if existing_family else default

            dues = 1 if dv("dues_paying", "dues_paying", 0) in (1, "Y", "1", True) else 0
            if existing_family:
                c.execute(
                    "UPDATE family SET head_of_household=?, relation=?, dues_paying=?,"
                    " monthly_amount=?, dues_start_date=?, dues_last_date=?, notes=?"
                    " WHERE member_id=?",
                    (
                        data.get("head_of_household", "") or "",
                        data.get("relation", "") or "",
                        dues,
                        dv("monthly_dues", "monthly_amount", None) or None,
                        dv("dues_start", "dues_start_date", "") or "",
                        dv("dues_last_paid", "dues_last_date", "") or "",
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

    def get_communion_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM communion WHERE member_id=? ORDER BY communion_date",
                (int(pno),),
            ).fetchall()

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

    def create_communion_record(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO communion ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def search_weddings(self, name="", member_id=None, limit=10):
        # Used by the adult confirmation/initiation intake forms to check for
        # an existing wedding row before creating a new one: first by the
        # applicant's own member_id (already recorded as groom/bride), then
        # by a name match against the free-text spouse name.
        with self._conn() as c:
            if member_id:
                rows = c.execute(
                    "SELECT * FROM wedding WHERE groom_member_id=? OR bride_member_id=?"
                    " ORDER BY wedding_date DESC LIMIT ?",
                    (int(member_id), int(member_id), limit),
                ).fetchall()
                if rows:
                    return rows
            name = (name or "").strip()
            if name:
                return c.execute(
                    "SELECT * FROM wedding WHERE groom_name LIKE ? OR bride_name LIKE ?"
                    " ORDER BY wedding_date DESC LIMIT ?",
                    (f"%{name}%", f"%{name}%", limit),
                ).fetchall()
        return []

    def update_member_fields(self, member_id, data):
        # Partial update of `member` columns only (dynamic SET clause, like
        # create_baptism/create_confirmation_record). Used by sacrament intake
        # dialogs to fill in applicant details captured on the paper forms
        # (place_of_birth, occupation, marital_status, etc.) without touching
        # `family` the way the full update() method does.
        if not data:
            return
        cols = list(data.keys())
        set_clause = ",".join(f"{c}=?" for c in cols)
        with self._conn() as c:
            c.execute(
                f"UPDATE member SET {set_clause} WHERE member_id=?",
                list(data.values()) + [int(member_id)],
            )
            c.commit()

    def link_child_to_parent(self, member_id, head_of_household, relation):
        # Sets/updates the child's family row so a matched father/mother
        # actually links the household, not just the FK on the sacrament row.
        with self._conn() as c:
            existing = c.execute(
                "SELECT family_id FROM family WHERE member_id=?", (int(member_id),)
            ).fetchone()
            if existing:
                c.execute(
                    "UPDATE family SET head_of_household=?, relation=? WHERE member_id=?",
                    (head_of_household, relation, int(member_id)),
                )
            else:
                c.execute(
                    "INSERT INTO family (member_id, head_of_household, relation, dues_paying)"
                    " VALUES (?,?,?,0)",
                    (int(member_id), head_of_household, relation),
                )
            c.commit()

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
                "SELECT d.name area, COUNT(*) cnt"
                " FROM member m"
                " LEFT JOIN district d ON d.code=m.reg_area"
                " WHERE m.reg_area GLOB '[0-9]*'"
                " GROUP BY m.reg_area ORDER BY cnt DESC"
            ).fetchall()
        return dict(active=active, lapsed=lapsed, baptisms=baptisms, weddings=weddings, areas=areas)
