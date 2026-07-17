# Church Registry

A desktop application for managing parishioner records for the Boston Korean Catholic community.
Supports registration, sacrament records, household grouping, move-in/out history, and Excel/CSV export.

## System Components

- **`church_app.py`**: Entry point — initializes the app, checks for the database file, launches the window.
- **`core/`**: Non-UI logic.
  - `constants.py`: Theme colors, stylesheet, area/relation lists, and database path (`parish.db`).
  - `database.py`: All SQLite queries — parishioners, sacraments, move records, statistics.
  - `session.py`: The current logged-in user.
- **`ui/`**: Main app screens and shared widgets — `views.py` (top-level exports), `main_window.py`, list/detail/stats/user-management views, the login screens, and `ui_helpers.py`.
- **`forms/`**: Modal dialogs for creating/editing records — the parishioner form, the sacrament application intake forms (adult confirmation, RCIA, infant baptism, youth confirmation), quick-entry sacrament forms, the person-picker widget, and the export dialog.
- **`assets/`**: Static files (icons).
- **`docs/`**: Database schema reference and other project documentation.

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
