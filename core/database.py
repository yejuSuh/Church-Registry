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
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS household (
                    household_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    head_member_id INTEGER REFERENCES member(member_id) ON DELETE RESTRICT,
                    created_at     TEXT
                )
            """)
            family_cols = [r[1] for r in c.execute("PRAGMA table_info(family)").fetchall()]
            if not family_cols or "head_of_household" in family_cols:
                c.execute("DROP TABLE IF EXISTS family")
                c.execute("""
                    CREATE TABLE family (
                        family_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                        member_id       INTEGER NOT NULL REFERENCES member(member_id) ON DELETE CASCADE,
                        household_id    INTEGER REFERENCES household(household_id) ON DELETE SET NULL,
                        relation        TEXT,
                        dues_paying     INTEGER NOT NULL DEFAULT 0 CHECK(dues_paying IN (0,1)),
                        monthly_amount  REAL,
                        dues_start_date TEXT,
                        dues_last_date  TEXT,
                        notes           TEXT,
                        created_at      TEXT
                    )
                """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_family_member    ON family(member_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_family_household ON family(household_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_household_head   ON household(head_member_id)")
            # Human-facing registration number (AAA-BB-HHH-MM). Internal placeholder,
            # separate from the immutable member_id PK; the original legacy number is
            # preserved in member.notes.
            member_cols = [r[1] for r in c.execute("PRAGMA table_info(member)").fetchall()]
            if member_cols and "reg_no" not in member_cols:
                c.execute("ALTER TABLE member ADD COLUMN reg_no TEXT")
            wedding_cols = [r[1] for r in c.execute("PRAGMA table_info(wedding)").fetchall()]
            if wedding_cols and "status" not in wedding_cols:
                c.execute("ALTER TABLE wedding ADD COLUMN status TEXT")
            c.commit()

        # Add surrogate AUTOINCREMENT PK to sacrament/event tables.
        # Text identifier columns are kept as UNIQUE (nullable for legacy
        # records without a number); no Python query code changes needed.
        with self._conn() as c:
            for tbl, id_col, extra_cols, extra_schema, indexes, trigger_body in [
                (
                    "baptism", "baptism_no",
                    "member_id,is_adp,date,diocese,parish,officiant_name,"
                    "officiant_name_bapt,godparent_member_id,godparent_name_ko,"
                    "godparent_name_en,godparent_name_bapt,status,created_at",
                    "member_id           INTEGER REFERENCES member(member_id) ON DELETE SET NULL,\n"
                    "            is_adp              INTEGER DEFAULT 0 CHECK(is_adp IN (0,1)),\n"
                    "            date                TEXT,\n"
                    "            diocese             TEXT,\n"
                    "            parish              TEXT,\n"
                    "            officiant_name      TEXT,\n"
                    "            officiant_name_bapt TEXT,\n"
                    "            godparent_member_id INTEGER REFERENCES member(member_id) ON DELETE SET NULL,\n"
                    "            godparent_name_ko   TEXT,\n"
                    "            godparent_name_en   TEXT,\n"
                    "            godparent_name_bapt TEXT,\n"
                    "            status              TEXT,\n"
                    "            created_at          TEXT",
                    ["CREATE INDEX IF NOT EXISTS idx_baptism_member ON baptism(member_id)"],
                    "AFTER INSERT ON baptism WHEN NEW.created_at IS NULL\n"
                    "        BEGIN UPDATE baptism SET created_at = strftime('%m/%d/%Y','now') WHERE rowid = NEW.rowid; END",
                ),
                (
                    "confirmation", "confirmation_no",
                    "member_id,is_adp,date,diocese,parish,officiant_name,"
                    "officiant_name_bapt,godparent_member_id,godparent_name_ko,"
                    "godparent_name_en,godparent_name_bapt,status,created_at",
                    "member_id           INTEGER REFERENCES member(member_id) ON DELETE SET NULL,\n"
                    "            is_adp              INTEGER DEFAULT 0 CHECK(is_adp IN (0,1)),\n"
                    "            date                TEXT,\n"
                    "            diocese             TEXT,\n"
                    "            parish              TEXT,\n"
                    "            officiant_name      TEXT,\n"
                    "            officiant_name_bapt TEXT,\n"
                    "            godparent_member_id INTEGER REFERENCES member(member_id) ON DELETE SET NULL,\n"
                    "            godparent_name_ko   TEXT,\n"
                    "            godparent_name_en   TEXT,\n"
                    "            godparent_name_bapt TEXT,\n"
                    "            status              TEXT,\n"
                    "            created_at          TEXT",
                    ["CREATE INDEX IF NOT EXISTS idx_confirm_member ON confirmation(member_id)"],
                    "AFTER INSERT ON confirmation WHEN NEW.created_at IS NULL\n"
                    "        BEGIN UPDATE confirmation SET created_at = strftime('%m/%d/%Y','now') WHERE rowid = NEW.rowid; END",
                ),
                (
                    "death", "death_id",
                    "member_id,date_death,cemetery,last_rites_date,viaticum,created_at",
                    "member_id       INTEGER NOT NULL UNIQUE REFERENCES member(member_id) ON DELETE CASCADE,\n"
                    "            date_death      TEXT,\n"
                    "            cemetery        TEXT,\n"
                    "            last_rites_date TEXT,\n"
                    "            viaticum        TEXT,\n"
                    "            created_at      TEXT",
                    ["CREATE INDEX IF NOT EXISTS idx_death_member ON death(member_id)"],
                    "AFTER INSERT ON death WHEN NEW.created_at IS NULL\n"
                    "        BEGIN UPDATE death SET created_at = strftime('%m/%d/%Y','now') WHERE rowid = NEW.rowid; END",
                ),
                (
                    "movein", "movein_id",
                    "member_id,date,former_diocese,former_parish,created_at",
                    "member_id      INTEGER NOT NULL REFERENCES member(member_id) ON DELETE CASCADE,\n"
                    "            date           TEXT,\n"
                    "            former_diocese TEXT,\n"
                    "            former_parish  TEXT,\n"
                    "            created_at     TEXT",
                    ["CREATE INDEX IF NOT EXISTS idx_movein_member ON movein(member_id)"],
                    "AFTER INSERT ON movein WHEN NEW.created_at IS NULL\n"
                    "        BEGIN UPDATE movein SET created_at = strftime('%m/%d/%Y','now') WHERE rowid = NEW.rowid; END",
                ),
                (
                    "moveout", "moveout_id",
                    "member_id,date,dest_diocese,dest_parish,created_at",
                    "member_id    INTEGER NOT NULL REFERENCES member(member_id) ON DELETE CASCADE,\n"
                    "            date         TEXT,\n"
                    "            dest_diocese TEXT,\n"
                    "            dest_parish  TEXT,\n"
                    "            created_at   TEXT",
                    ["CREATE INDEX IF NOT EXISTS idx_moveout_member ON moveout(member_id)"],
                    "AFTER INSERT ON moveout WHEN NEW.created_at IS NULL\n"
                    "        BEGIN UPDATE moveout SET created_at = strftime('%m/%d/%Y','now') WHERE rowid = NEW.rowid; END",
                ),
            ]:
                cols = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()]
                if cols and "id" not in cols:
                    c.execute(f"""
                        CREATE TABLE {tbl}_new (
                            id        INTEGER PRIMARY KEY AUTOINCREMENT,
                            {id_col}  TEXT UNIQUE,
                            {extra_schema}
                        )
                    """)
                    c.execute(
                        f"INSERT INTO {tbl}_new ({id_col},{extra_cols})"
                        f" SELECT {id_col},{extra_cols} FROM {tbl}"
                    )
                    c.execute(f"DROP TABLE {tbl}")
                    c.execute(f"ALTER TABLE {tbl}_new RENAME TO {tbl}")
                    for idx_sql in indexes:
                        c.execute(idx_sql)
                    trigger_name = f"trg_{tbl}_created_at"
                    c.execute(
                        f"CREATE TRIGGER IF NOT EXISTS {trigger_name} {trigger_body}"
                    )
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
            existing = {r[0]: r[1] for r in c.execute("SELECT code, name FROM district")}
            dirty = [(code, name) for code, name in AREAS if existing.get(code) != name]
            if dirty:
                c.executemany(
                    "INSERT OR REPLACE INTO district (code, name) VALUES (?,?)", dirty
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

    # ── Member queries ───────────────────────────────────────────────────────

    # Shared projection used by search() and get()
    _MEMBER_SELECT = (
        "SELECT m.member_id, m.reg_area,"
        " COALESCE(m.reg_no, m.reg_area || '-' || printf('%05d', m.member_id)) AS display_id,"
        " TRIM(m.name_ko) AS name,"
        " TRIM(m.name_en) AS name_english,"
        " TRIM(m.baptismal_name) AS baptismal_name,"
        " d.name AS district,"
        " m.address, m.postal_code,"
        " m.phone, m.email,"
        " m.birth_date, m.sex,"
        " m.occupation,"
        " f.household_id,"
        " h.head_member_id,"
        " TRIM(mh.name_ko) AS head_of_household,"
        " CASE WHEN h.head_member_id=m.member_id THEN 1 ELSE 0 END AS is_head,"
        " TRIM(f.relation) AS relation,"
        " COALESCE(f.dues_paying, 0) AS dues_paying,"
        " f.monthly_amount AS monthly_dues,"
        " f.dues_start_date AS dues_start,"
        " f.dues_last_date AS dues_last_paid,"
        " COALESCE(f.notes, m.notes) AS notes,"
        " CASE WHEN ms.status='inactive' THEN 1 ELSE 0 END AS is_inactive"
        " FROM member m"
        " LEFT JOIN family f ON f.member_id=m.member_id"
        " LEFT JOIN household h ON h.household_id=f.household_id"
        " LEFT JOIN member mh ON mh.member_id=h.head_member_id"
        " LEFT JOIN member_status ms ON ms.member_id=m.member_id"
        " LEFT JOIN district d ON d.code=m.reg_area"
    )

    def search(self, q="", area=""):
        # Only show real parishioners (numeric reg_area), not placeholder-only members
        sql = self._MEMBER_SELECT + " WHERE m.reg_area GLOB '[0-9]*'"
        p = []
        if q:
            sql += (
                " AND (TRIM(m.name_ko) LIKE ? OR TRIM(m.baptismal_name) LIKE ?"
                " OR TRIM(mh.name_ko) LIKE ?)"
            )
            p += [f"%{q}%"] * 3
        if area:
            sql += " AND m.reg_area=?"
            p.append(area)
        sql += " ORDER BY m.reg_area, m.member_id"
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
            " AND (TRIM(m.name_ko) LIKE ? OR TRIM(m.name_en) LIKE ?"
            " OR TRIM(m.baptismal_name) LIKE ?)"
            " ORDER BY m.reg_area, m.member_id LIMIT ?"
        )
        p = [f"%{q}%"] * 3 + [limit]
        with self._conn() as c:
            return c.execute(sql, p).fetchall()

    def household(self, household_id, exclude=None):
        if not household_id:
            return []
        hid = int(household_id)
        with self._conn() as c:
            sql = (
                "SELECT m.member_id,"
                " COALESCE(m.reg_no, m.reg_area || '-' || printf('%05d', m.member_id)) AS display_id,"
                " TRIM(m.name_ko) AS name,"
                " TRIM(m.baptismal_name) AS baptismal_name,"
                " TRIM(f.relation) AS relation,"
                " h.head_member_id"
                " FROM member m"
                " JOIN family f ON f.member_id=m.member_id"
                " JOIN household h ON h.household_id=f.household_id"
                " WHERE f.household_id=?"
            )
            params = [hid]
            if exclude:
                sql += " AND m.member_id!=?"
                params.append(int(exclude))
            sql += " ORDER BY CASE WHEN h.head_member_id=m.member_id THEN 0 ELSE 1 END, m.member_id"
            return c.execute(sql, params).fetchall()

    @staticmethod
    def _next_house(reg_nos):
        """Given the existing reg_no strings for an area, return the next free
        3-digit house number. reg_no format: AAA-BB-HHH-MM (district-반-house-member)."""
        max_h = 0
        for rn in reg_nos:
            parts = (rn or "").split("-")
            if len(parts) >= 3 and parts[2].isdigit():
                max_h = max(max_h, int(parts[2]))
        return max_h + 1

    def next_no(self, area_code):
        # New registration number: AAA-BB-HHH-MM (district-반-house-member).
        # 반 is not tracked yet -> 00; a new member starts a new house at member 01.
        with self._conn() as c:
            reg_nos = [r[0] for r in c.execute(
                "SELECT reg_no FROM member WHERE reg_area=? AND reg_no IS NOT NULL",
                (area_code,),
            ).fetchall()]
        return f"{area_code}-00-{self._next_house(reg_nos):03d}-01"

    def _next_record_id(self, c, table, id_col):
        """Generate the next YYYY-#### primary key for inactive/death/movein/moveout."""
        year = datetime.now().year
        row = c.execute(
            f"SELECT {id_col} FROM {table} WHERE {id_col} LIKE ? ORDER BY {id_col} DESC LIMIT 1",
            (f"{year}-%",),
        ).fetchone()
        seq = (int(row[0].rsplit("-", 1)[-1]) + 1) if (row and row[0]) else 1
        return f"{year}-{seq:04d}"

    def create(self, data):
        display_id = data.get("member_id", "")
        reg_area = display_id.split("-", 1)[0] if "-" in display_id else display_id

        with self._conn() as c:
            c.execute(
                "INSERT INTO member"
                " (reg_area, name_ko, name_en, baptismal_name,"
                "  birth_date, sex, address, postal_code, phone, email, occupation)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    reg_area,
                    data.get("name", ""),
                    data.get("name_english") or None,
                    data.get("baptismal_name", "") or "",
                    data.get("birth_date") or None,
                    data.get("sex") or None,
                    data.get("address") or None,
                    data.get("postal_code") or None,
                    data.get("phone") or None,
                    data.get("email") or None,
                    data.get("occupation") or None,
                ),
            )
            new_mid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            c.execute(
                "INSERT INTO family"
                " (member_id, dues_paying, monthly_amount, dues_start_date, dues_last_date, notes)"
                " VALUES (?,?,?,?,?,?)",
                (
                    new_mid,
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
            # Assign the new-format registration number (AAA-BB-HHH-MM). Generated
            # fresh from the current area occupancy so it can never collide, even
            # if the value shown on the form went stale.
            if reg_area and reg_area.isdigit():
                reg_nos = [r[0] for r in c.execute(
                    "SELECT reg_no FROM member WHERE reg_area=? AND reg_no IS NOT NULL"
                    " AND member_id!=?",
                    (reg_area, new_mid),
                ).fetchall()]
                c.execute(
                    "UPDATE member SET reg_no=? WHERE member_id=?",
                    (f"{reg_area}-00-{self._next_house(reg_nos):03d}-01", new_mid),
                )
            c.commit()
        return new_mid

    def update(self, pno, data):
        mid = int(pno)
        with self._conn() as c:
            c.execute(
                "UPDATE member SET name_ko=?, name_en=?, baptismal_name=?,"
                " birth_date=?, sex=?, address=?, postal_code=?, phone=?, email=?,"
                " occupation=?"
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
                    "UPDATE family SET dues_paying=?,"
                    " monthly_amount=?, dues_start_date=?, dues_last_date=?, notes=?"
                    " WHERE member_id=?",
                    (
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
                    " (member_id, dues_paying, monthly_amount, dues_start_date, dues_last_date, notes)"
                    " VALUES (?,?,?,?,?,?)",
                    (
                        mid,
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
                "SELECT * FROM baptism WHERE member_id=? ORDER BY date",
                (int(pno),),
            ).fetchall()

    def get_confirmation_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM confirmation WHERE member_id=? ORDER BY date",
                (int(pno),),
            ).fetchall()

    def get_wedding_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM wedding"
                " WHERE groom_id=? OR bride_id=?"
                " ORDER BY date",
                (int(pno), int(pno)),
            ).fetchall()

    def get_death_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM death WHERE member_id=? ORDER BY date_death",
                (int(pno),),
            ).fetchall()

    # ── Move-in / Move-out records ───────────────────────────────────────────

    def get_communion_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM communion WHERE member_id=? ORDER BY date",
                (int(pno),),
            ).fetchall()

    def get_movein_record(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM movein WHERE member_id=? LIMIT 1",
                (int(pno),),
            ).fetchone()

    def get_moveout_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM moveout WHERE member_id=? ORDER BY date",
                (int(pno),),
            ).fetchall()

    # ── Sacrament write methods ──────────────────────────────────────────────

    def create_baptism(self, data):
        data.setdefault("status", "예정")
        cols = list(data.keys())
        sql = f"INSERT INTO baptism ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_confirmation_record(self, data):
        data.setdefault("status", "예정")
        cols = list(data.keys())
        sql = f"INSERT INTO confirmation ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_wedding_record(self, data):
        data.setdefault("status", "예정")
        cols = list(data.keys())
        sql = f"INSERT INTO wedding ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_communion_record(self, data):
        data.setdefault("status", "예정")
        cols = list(data.keys())
        sql = f"INSERT INTO communion ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def update_sacrament_status(self, table, pk_col, pk_val, status):
        with self._conn() as c:
            c.execute(f"UPDATE {table} SET status=? WHERE {pk_col}=?", (status, pk_val))
            c.commit()

    def search_weddings(self, name="", member_id=None, limit=10):
        # Used by the adult confirmation/initiation intake forms to check for
        # an existing wedding row before creating a new one: first by the
        # applicant's own member_id (already recorded as groom/bride), then
        # by a name match against the free-text spouse name.
        with self._conn() as c:
            if member_id:
                rows = c.execute(
                    "SELECT * FROM wedding WHERE groom_id=? OR bride_id=?"
                    " ORDER BY date DESC LIMIT ?",
                    (int(member_id), int(member_id), limit),
                ).fetchall()
                if rows:
                    return rows
            name = (name or "").strip()
            if name:
                return c.execute(
                    "SELECT * FROM wedding WHERE groom_name LIKE ? OR bride_name LIKE ?"
                    " ORDER BY date DESC LIMIT ?",
                    (f"%{name}%", f"%{name}%", limit),
                ).fetchall()
        return []

    def update_member_fields(self, member_id, data):
        # Partial update of `member` columns only (dynamic SET clause).
        # Keys must match actual column names in the member table.
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

    def link_child_to_parent(self, member_id, parent_member_id, relation):
        # Links a child to their parent's household when a parent is matched
        # on a sacrament intake form. No-op if the parent has no household yet.
        mid = int(member_id)
        pmid = int(parent_member_id)
        with self._conn() as c:
            row = c.execute(
                "SELECT household_id FROM family WHERE member_id=?", (pmid,)
            ).fetchone()
            if not row or not row[0]:
                return
            hid = row[0]
            existing = c.execute(
                "SELECT family_id FROM family WHERE member_id=?", (mid,)
            ).fetchone()
            if existing:
                c.execute(
                    "UPDATE family SET household_id=?, relation=? WHERE member_id=?",
                    (hid, relation, mid),
                )
            else:
                c.execute(
                    "INSERT INTO family (member_id, household_id, relation, dues_paying)"
                    " VALUES (?,?,?,0)",
                    (mid, hid, relation),
                )
            c.commit()

    # ── Household methods ────────────────────────────────────────────────────

    def create_household(self, head_member_id):
        """Create a new household with head_member_id as the 세대주.
        Sets that member's family row to household_id + relation='본인'.
        Returns the new household_id."""
        head_mid = int(head_member_id)
        with self._conn() as c:
            c.execute(
                "INSERT INTO household (head_member_id) VALUES (?)", (head_mid,)
            )
            hid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            existing = c.execute(
                "SELECT family_id FROM family WHERE member_id=?", (head_mid,)
            ).fetchone()
            if existing:
                c.execute(
                    "UPDATE family SET household_id=?, relation='본인' WHERE member_id=?",
                    (hid, head_mid),
                )
            else:
                c.execute(
                    "INSERT INTO family (member_id, household_id, relation, dues_paying)"
                    " VALUES (?,?,?,0)",
                    (head_mid, hid, "본인"),
                )
            c.commit()
        return hid

    def join_household(self, member_id, household_id, relation):
        """Add (or move) a member into an existing household with the given relation.
        Only updates household_id and relation; dues fields are untouched."""
        mid = int(member_id)
        hid = int(household_id)
        with self._conn() as c:
            existing = c.execute(
                "SELECT family_id FROM family WHERE member_id=?", (mid,)
            ).fetchone()
            if existing:
                c.execute(
                    "UPDATE family SET household_id=?, relation=? WHERE member_id=?",
                    (hid, relation, mid),
                )
            else:
                c.execute(
                    "INSERT INTO family (member_id, household_id, relation, dues_paying)"
                    " VALUES (?,?,?,0)",
                    (mid, hid, relation),
                )
            c.commit()

    def leave_household(self, member_id):
        """Detach a member from their current household (sets household_id=NULL)."""
        mid = int(member_id)
        with self._conn() as c:
            c.execute(
                "UPDATE family SET household_id=NULL, relation='' WHERE member_id=?",
                (mid,),
            )
            c.commit()

    def set_household_head(self, household_id, new_head_member_id):
        """Change the 세대주 of a household.
        Updates household.head_member_id and sets the new head's relation to '본인'."""
        hid = int(household_id)
        new_mid = int(new_head_member_id)
        with self._conn() as c:
            c.execute(
                "UPDATE household SET head_member_id=? WHERE household_id=?",
                (new_mid, hid),
            )
            c.execute(
                "UPDATE family SET relation='본인' WHERE member_id=? AND household_id=?",
                (new_mid, hid),
            )
            c.commit()

    def get_household_members(self, household_id, exclude=None):
        """Return all members of a household ordered head-first."""
        if not household_id:
            return []
        hid = int(household_id)
        with self._conn() as c:
            sql = (
                "SELECT m.member_id,"
                " COALESCE(m.reg_no, m.reg_area || '-' || printf('%05d', m.member_id)) AS display_id,"
                " TRIM(m.name_ko) AS name,"
                " TRIM(m.baptismal_name) AS baptismal_name,"
                " TRIM(f.relation) AS relation,"
                " CASE WHEN h.head_member_id=m.member_id THEN 1 ELSE 0 END AS is_head"
                " FROM member m"
                " JOIN family f ON f.member_id=m.member_id"
                " JOIN household h ON h.household_id=f.household_id"
                " WHERE f.household_id=?"
            )
            params = [hid]
            if exclude:
                sql += " AND m.member_id!=?"
                params.append(int(exclude))
            sql += " ORDER BY is_head DESC, m.member_id"
            return c.execute(sql, params).fetchall()

    def search_households(self, q, limit=10):
        """Search households by 세대주 name or baptismal name."""
        q = (q or "").strip()
        if not q:
            return []
        with self._conn() as c:
            return c.execute(
                "SELECT h.household_id, TRIM(m.name_ko) AS head_name,"
                " TRIM(m.baptismal_name) AS head_bapt,"
                " COALESCE(m.reg_no, m.reg_area || '-' || printf('%05d', m.member_id)) AS head_display_id"
                " FROM household h"
                " JOIN member m ON m.member_id=h.head_member_id"
                " WHERE TRIM(m.name_ko) LIKE ? OR TRIM(m.baptismal_name) LIKE ?"
                " LIMIT ?",
                (f"%{q}%", f"%{q}%", limit),
            ).fetchall()

    def create_death_record(self, data):
        mid = int(data.get("member_id", 0))
        with self._conn() as c:
            death_id = self._next_record_id(c, "death", "death_id")
            c.execute(
                "INSERT INTO death (death_id, member_id, date_death, cemetery, last_rites_date, viaticum)"
                " VALUES (?,?,?,?,?,?)",
                (
                    death_id,
                    mid,
                    data.get("date_death", "") or "",
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
