# Church Registry

A desktop application for managing parishioner records for the Boston Korean Catholic community.
Supports registration, sacrament records, household grouping, move-in/out history, and Excel/CSV export.

## System Components

1. **`constants.py`**: Theme colors, stylesheet, area/relation lists, and database path (`parish.db`).
2. **`database.py`**: All SQLite queries — parishioners, sacraments, move records, statistics.
3. **`views.py`**: PyQt6 UI — list view, detail panel (tabbed), forms, export dialog.
4. **`church_app.py`**: Entry point — initializes the app, checks for the database file, launches the window.

## Features

- Parishioner list with search by name, baptism name, ID, or household head, and filter by area (구역)
- Full detail panel with edit, soft delete, restore, and permanent delete
- Sacrament records tab: baptism, confirmation, wedding, confession, death — view and add
- Move-in / move-out history tab
- Statistics view: active count, lapsed members, per-area breakdown
- Export current list to CSV or Excel (`.xlsx`) with styled headers
- Window size and position remembered between sessions
- Keyboard shortcuts: `Ctrl+N` new record, `Ctrl+F` focus search, `Escape` clear search

---

### 📦 Requirements

- Python 3.10 or later
- PyQt6
- openpyxl

---

### 🚀 Installation

#### 1. Clone or copy the project folder

Make sure `parish.db` is placed in the same folder as the Python files.

#### 2. Install dependencies

```sh
pip install -r requirements.txt
```

---

### ▶️ Running the Project

```sh
python3 church_app.py
```

The app uses `parish.db` in the project folder as the database.

---

### 💾 Database Backup

The entire database is a single file: `parish.db`.
Copying this file is all that is needed to create a backup.

**Manual backup (Terminal):**

```sh
cp parish.db "parish_$(date +%Y%m%d).db"
```

Example output: `parish_20260614.db`

**Recommendations:**

- Back up after any significant data entry session.
- Store backup files in a separate location (external drive, iCloud, Google Drive, etc.).
- To restore, replace `parish.db` in the project folder with the backup file and rename it to `parish.db`.
