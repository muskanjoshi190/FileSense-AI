import os
import shutil
from datetime import datetime


class FileOrganizer:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.expanduser("~/OrganizedFiles")

    # ─────────────────────────────────────────────
    # CREATE FOLDER STRUCTURE
    # ─────────────────────────────────────────────
    def create_folder_structure(self):
        folders = [
            'Documents', 'Spreadsheets', 'Images', 'Audio', 'Video',
            'Code', 'Archives', 'Executables', 'PDFs', 'Other',
            'Duplicates', 'Similar_Files'
        ]
        for folder in folders:
            os.makedirs(os.path.join(self.base_dir, folder), exist_ok=True)
        return self.base_dir

    # ─────────────────────────────────────────────
    # ORGANIZE SINGLE FILE
    # ─────────────────────────────────────────────
    def organize_file(self, filepath, category):
        try:
            target_dir = os.path.join(self.base_dir, category)
            os.makedirs(target_dir, exist_ok=True)

            filename  = os.path.basename(filepath)
            dest_path = os.path.join(target_dir, filename)

            # resolve name conflict
            if os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                counter   = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
                    counter  += 1

            shutil.move(filepath, dest_path)
            return dest_path, None

        except Exception as e:
            return None, str(e)

    # ─────────────────────────────────────────────
    # BULK ORGANIZE FROM DB  (FIXED)
    # After moving a file, the DB record is updated
    # with the new path instead of being deleted.
    # ─────────────────────────────────────────────
    def organize_files_from_db(self, db, scanner):
        """
        Main function called by ui_manager:
            moved, errors = self.organizer.organize_files_from_db(self.db, self.scanner)
        """
        self.create_folder_structure()

        files  = db.get_all_files()
        moved  = 0
        errors = []

        for f in files:
            try:
                file_id  = f[0]
                filepath = f[2]  if len(f) > 2 else ""
                category = f[7] if len(f) > 7 else "Other"    # yeh sahi hai already ✅
                # lekin is_duplicate check ke liye:
                # f[8] = is_duplicate

                if not filepath or not os.path.exists(filepath):
                    continue

                # Don't re-organize files already inside OrganizedFiles
                if os.path.abspath(filepath).startswith(
                        os.path.abspath(self.base_dir)):
                    continue

                new_path, err = self.organize_file(filepath, category)

                if new_path:
                    # Remove old DB record
                    db.delete_file(file_id)

                    # Re-insert with updated path so the UI stays in sync
                    new_info = scanner.get_file_info(new_path)
                    if new_info:
                        db.insert_file_object(new_info)

                    moved += 1
                else:
                    errors.append(err or "Unknown error")

            except Exception as e:
                errors.append(str(e))

        return moved, errors

    # ─────────────────────────────────────────────
    # ORGANIZE BY DATE
    # ─────────────────────────────────────────────
    def organize_by_date(self, filepath):
        try:
            mtime    = os.path.getmtime(filepath)
            date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m')

            date_dir  = os.path.join(self.base_dir, 'By_Date', date_str)
            os.makedirs(date_dir, exist_ok=True)

            filename  = os.path.basename(filepath)
            dest_path = os.path.join(date_dir, filename)

            if os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                counter   = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(date_dir, f"{name}_{counter}{ext}")
                    counter  += 1

            shutil.move(filepath, dest_path)
            return dest_path, None

        except Exception as e:
            return None, str(e)