import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path="file_registry.db"):
        self.db_path = db_path
        self.init_database()

    # ─────────────────────────────────────────────
    # INIT DB
    # ─────────────────────────────────────────────
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT UNIQUE,
                filetype TEXT,
                filesize INTEGER,
                hash_value TEXT,
                upload_date TEXT,
                category TEXT,
                is_duplicate INTEGER DEFAULT 0,
                duplicate_group_id INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS similar_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id1 INTEGER,
                file_id2 INTEGER,
                similarity_score REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trash (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                original_path TEXT,
                trash_path TEXT,
                deletion_date TEXT,
                filesize INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────
    # INSERT FILE — accepts a dict from FileScanner
    # ─────────────────────────────────────────────
    def insert_file_object(self, file_obj):
        """Insert a file using a dict returned by FileScanner.get_file_info()"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO file_registry
                (filename, filepath, filetype, filesize,
                 hash_value, upload_date, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_obj["filename"],
                file_obj["filepath"],
                file_obj["filetype"],
                file_obj["filesize"],
                file_obj.get("hash") or file_obj.get("hash_value"),
                datetime.now().isoformat(),
                file_obj["category"]
            ))
            conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            # File path already exists in DB — skip silently
            return None

        finally:
            conn.close()

    def insert_file(self, filepath, filename, filetype, filesize,
                    hash_value, category):
        """Insert a file using individual keyword arguments."""
        return self.insert_file_object({
            "filename":  filename,
            "filepath":  filepath,
            "filetype":  filetype,
            "filesize":  filesize,
            "hash":      hash_value,
            "category":  category,
        })

    # ─────────────────────────────────────────────
    # GET ALL FILES
    # ─────────────────────────────────────────────
    def get_all_files(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM file_registry ORDER BY upload_date DESC")
        rows = cursor.fetchall()

        conn.close()
        return rows

    # ─────────────────────────────────────────────
    # GET BY ID
    # ─────────────────────────────────────────────
    def get_file_by_id(self, file_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM file_registry WHERE id=?", (file_id,))
        row = cursor.fetchone()

        conn.close()
        return row

    # ─────────────────────────────────────────────
    # GET BY PATH
    # ─────────────────────────────────────────────
    def get_file_by_path(self, path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM file_registry WHERE filepath=?", (path,))
        row = cursor.fetchone()

        conn.close()
        return row

    # ─────────────────────────────────────────────
    # DELETE FILE
    # ─────────────────────────────────────────────
    def delete_file(self, file_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM file_registry WHERE id=?", (file_id,))
        conn.commit()

        conn.close()

    # ─────────────────────────────────────────────
    # MARK DUPLICATES
    # ─────────────────────────────────────────────
    def mark_duplicates(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE file_registry
            SET is_duplicate = 1
            WHERE hash_value IN (
                SELECT hash_value
                FROM file_registry
                GROUP BY hash_value
                HAVING COUNT(*) > 1
            )
        """)

        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────
    # TRASH
    # ─────────────────────────────────────────────
    def add_to_trash(self, file_row):
        """
        file_row is a tuple from get_file_by_id() / get_file_by_path():
        (id, filename, filepath, filetype, filesize, hash_value,
         upload_date, category, is_duplicate, duplicate_group_id)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        filename  = file_row[1] if len(file_row) > 1 else ""
        filepath  = file_row[2] if len(file_row) > 2 else ""
        filesize  = file_row[4] if len(file_row) > 4 else 0

        cursor.execute('''
            INSERT INTO trash (filename, original_path, trash_path,
                               deletion_date, filesize)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            filename,
            filepath,
            filepath,
            datetime.now().isoformat(),
            filesize,
        ))

        conn.commit()
        conn.close()

    def get_trash_contents(self):
        """Returns a list of dicts for easy access in the UI."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM trash ORDER BY deletion_date DESC")
        rows = cursor.fetchall()

        conn.close()

        result = []
        for row in rows:
            result.append({
                "id":           row[0],
                "filename":     row[1] if row[1] else "Unknown",
                "original_path":row[2] if row[2] else "",
                "trash_path":   row[3] if row[3] else "",
                "deleted_date": row[4] if row[4] else "",
                "size":         row[5] if row[5] else 0,
            })

        return result

    def delete_from_trash(self, trash_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM trash WHERE trash_path=?", (trash_path,))
        conn.commit()

        conn.close()

    def clear_trash(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM trash")
        conn.commit()

        conn.close()

    # ─────────────────────────────────────────────
    # UTIL
    # ─────────────────────────────────────────────
    def clear_all_files(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM file_registry")
        cursor.execute("DELETE FROM similar_files")

        conn.commit()
        conn.close()

        return True