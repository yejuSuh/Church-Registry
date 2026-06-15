import sqlite3


class DB:
    def __init__(self, path):
        self.path = path

    def _conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def search(self, q="", area="", deleted=False):
        sql = ("SELECT parishioner_no, TRIM(name) name, TRIM(baptism_nm) baptism_nm,"
               " TRIM(host_nm) host_nm, TRIM(relation) relation, TRIM(tel_home) tel_home,"
               " TRIM(lazy_flag) lazy_flag, TRIM(delete_flag) delete_flag,"
               " TRIM(address) address, TRIM(registion_date) registion_date"
               " FROM parishioner WHERE 1=1")
        p = []
        if not deleted:
            sql += " AND (TRIM(delete_flag)!='Y' OR delete_flag IS NULL)"
        if q:
            sql += (" AND (TRIM(name) LIKE ? OR TRIM(baptism_nm) LIKE ?"
                    " OR TRIM(parishioner_no) LIKE ? OR TRIM(host_nm) LIKE ?)")
            p += [f"%{q}%"] * 4
        if area:
            sql += " AND TRIM(parishioner_no) LIKE ?"
            p.append(f"{area}%")
        sql += " ORDER BY parishioner_no"
        with self._conn() as c:
            return c.execute(sql, p).fetchall()

    def get(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM parishioner WHERE parishioner_no=?", (pno,)
            ).fetchone()

    def household(self, host, exclude=None):
        with self._conn() as c:
            base = ("SELECT parishioner_no, TRIM(name) name, TRIM(relation) relation,"
                    " TRIM(baptism_nm) baptism_nm FROM parishioner"
                    " WHERE TRIM(host_nm)=? AND (TRIM(delete_flag)!='Y' OR delete_flag IS NULL)")
            if exclude:
                return c.execute(
                    base + " AND parishioner_no!=? ORDER BY parishioner_no",
                    (host, exclude),
                ).fetchall()
            return c.execute(base + " ORDER BY parishioner_no", (host,)).fetchall()

    def next_no(self, area):
        with self._conn() as c:
            rows = c.execute(
                "SELECT parishioner_no FROM parishioner WHERE parishioner_no LIKE ?",
                (f"{area}%",),
            ).fetchall()
        hi = 0
        for r in rows:
            try:
                hi = max(hi, int(r[0].strip().split("-")[1]))
            except Exception:
                pass
        return f"{area}-{str(hi + 1).zfill(5)}"

    def create(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO parishioner ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values()))
            c.commit()

    def update(self, pno, data):
        sets = ", ".join(f"{k}=?" for k in data)
        with self._conn() as c:
            c.execute(
                f"UPDATE parishioner SET {sets} WHERE parishioner_no=?",
                list(data.values()) + [pno],
            )
            c.commit()

    def soft_delete(self, pno):
        with self._conn() as c:
            c.execute(
                "UPDATE parishioner SET delete_flag='Y' WHERE parishioner_no=?", (pno,)
            )
            c.commit()

    def restore(self, pno):
        with self._conn() as c:
            c.execute(
                "UPDATE parishioner SET delete_flag='N' WHERE parishioner_no=?", (pno,)
            )
            c.commit()

    def hard_delete(self, pno):
        with self._conn() as c:
            c.execute("DELETE FROM parishioner WHERE parishioner_no=?", (pno,))
            c.commit()

    # ── Sacrament records ────────────────────────────────────────────────────

    def get_baptism_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM baptism WHERE TRIM(parishioner_no)=? ORDER BY baptism_date",
                (pno,),
            ).fetchall()

    def get_sacrament_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM sacrament WHERE TRIM(parishioner_no)=? ORDER BY sacrament_date",
                (pno,),
            ).fetchall()

    def get_wedding_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM wedding"
                " WHERE TRIM(m_parishioner_no)=? OR TRIM(w_parishioner_no)=?"
                " ORDER BY wedding_date",
                (pno, pno),
            ).fetchall()

    def get_confession_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM confession WHERE TRIM(parishioner_no)=?"
                " ORDER BY confession_year DESC",
                (pno,),
            ).fetchall()

    def get_death_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM death WHERE TRIM(parishioner_no)=? ORDER BY death_date",
                (pno,),
            ).fetchall()

    # ── Move-in / Move-out records ───────────────────────────────────────────

    def get_movein_record(self, pno):
        with self._conn() as c:
            row = c.execute(
                "SELECT TRIM(movein_no) movein_no FROM parishioner WHERE TRIM(parishioner_no)=?",
                (pno,),
            ).fetchone()
        if not row or not row["movein_no"]:
            return None
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM movein WHERE TRIM(movein_no)=?", (row["movein_no"],)
            ).fetchone()

    def get_moveout_records(self, pno):
        with self._conn() as c:
            return c.execute(
                "SELECT mo.moveout_no, mo.moveout_date, mo.new_parish_nm,"
                " mo.new_parish_church, mo.duty_money, mo.duty_yymm"
                " FROM moveout mo"
                " JOIN moveout_history moh ON TRIM(moh.moveout_no)=TRIM(mo.moveout_no)"
                " WHERE TRIM(moh.parishioner_no)=?"
                " ORDER BY mo.moveout_date",
                (pno,),
            ).fetchall()

    # ── Sacrament records ────────────────────────────────────────────────────

    def create_baptism(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO baptism ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_sacrament_record(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO sacrament ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_wedding_record(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO wedding ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    def create_confession_record(self, data):
        with self._conn() as c:
            c.execute(
                "INSERT INTO confession (parishioner_no, confession_year, spring, fall)"
                " VALUES (?,?,?,?)",
                (data["parishioner_no"], data["confession_year"], data["spring"], data["fall"]),
            )
            c.commit()

    def create_death_record(self, data):
        cols = list(data.keys())
        sql = f"INSERT INTO death ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as c:
            c.execute(sql, list(data.values())); c.commit()

    # ── Statistics ───────────────────────────────────────────────────────────

    def stats(self):
        with self._conn() as c:
            active = c.execute(
                "SELECT COUNT(*) FROM parishioner WHERE (TRIM(delete_flag)!='Y' OR delete_flag IS NULL)"
            ).fetchone()[0]
            lapsed = c.execute(
                "SELECT COUNT(*) FROM parishioner"
                " WHERE TRIM(lazy_flag)='Y' AND (TRIM(delete_flag)!='Y' OR delete_flag IS NULL)"
            ).fetchone()[0]
            baptisms = c.execute("SELECT COUNT(*) FROM baptism").fetchone()[0]
            weddings = c.execute("SELECT COUNT(*) FROM wedding").fetchone()[0]
            areas = c.execute(
                "SELECT SUBSTR(TRIM(parishioner_no),1,5) area, COUNT(*) cnt"
                " FROM parishioner WHERE (TRIM(delete_flag)!='Y' OR delete_flag IS NULL)"
                " GROUP BY area ORDER BY cnt DESC"
            ).fetchall()
        return dict(active=active, lapsed=lapsed, baptisms=baptisms, weddings=weddings, areas=areas)
