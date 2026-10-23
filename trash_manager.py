import os
import json
import shutil
from datetime import datetime


class TrashManager:
    def __init__(self):
        self.trash_dir = os.path.join(os.path.expanduser("~"), ".file_manager_trash")
        os.makedirs(self.trash_dir, exist_ok=True)
        self.meta_file = os.path.join(self.trash_dir, ".trash_meta.json")
        self._load_meta()

    # ─────────────────────────────────────────────
    # METADATA (tracks original paths)
    # ─────────────────────────────────────────────
    def _load_meta(self):
        if os.path.exists(self.meta_file):
            try:
                with open(self.meta_file, 'r') as f:
                    self.meta = json.load(f)
            except Exception:
                self.meta = {}
        else:
            self.meta = {}

    def _save_meta(self):
        try:
            with open(self.meta_file, 'w') as f:
                json.dump(self.meta, f, indent=2)
        except Exception as e:
            print(f"TrashManager: could not save metadata: {e}")

    # ─────────────────────────────────────────────
    # ADD TO TRASH  (called by ui_manager)
    # file_row is a DB tuple:
    # (id, filename, filepath, filetype, filesize, ...)
    # ─────────────────────────────────────────────
    def add_to_trash(self, file_row):
        try:
            filename = file_row[1] if len(file_row) > 1 else "unknown"
            filepath = file_row[2] if len(file_row) > 2 else ""
            filesize = file_row[4] if len(file_row) > 4 else 0
            deleted_date = datetime.now().isoformat()

            if not filepath:
                return False, "No filepath in record"

            if os.path.exists(filepath):
                # physically move the file into trash folder
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                trash_filename = f"{timestamp}_{filename}"
                trash_path = os.path.join(self.trash_dir, trash_filename)
                shutil.move(filepath, trash_path)
            else:
                # file is already gone from disk – still track it
                trash_path = filepath

            # store metadata so we can restore later
            self.meta[trash_path] = {
                "filename":      filename,
                "original_path": filepath,
                "trash_path":    trash_path,
                "deleted_date":  deleted_date,
                "size":          filesize,
            }
            self._save_meta()
            return True, trash_path

        except Exception as e:
            return False, str(e)

    # ─────────────────────────────────────────────
    # RESTORE FILE  (called by ui_manager)
    # ─────────────────────────────────────────────
    def restore_file(self, trash_path):
        try:
            if not os.path.exists(trash_path):
                return False, "File not found in trash folder"

            info = self.meta.get(trash_path, {})
            original_path = info.get("original_path", "")

            if not original_path:
                # Fall back: strip timestamp prefix from filename
                basename = os.path.basename(trash_path)[16:]  # remove YYYYMMDD_HHMMSS_
                original_path = os.path.join(os.path.expanduser("~"), basename)

            # resolve name conflict at destination
            dest = original_path
            if os.path.exists(dest):
                base, ext = os.path.splitext(dest)
                counter = 1
                while os.path.exists(dest):
                    dest = f"{base}_restored_{counter}{ext}"
                    counter += 1

            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            shutil.move(trash_path, dest)

            # remove from metadata
            self.meta.pop(trash_path, None)
            self._save_meta()

            return True, dest

        except Exception as e:
            return False, str(e)

    # ─────────────────────────────────────────────
    # GET TRASH CONTENTS  (called by ui_manager)
    # ─────────────────────────────────────────────
    def get_trash_contents(self):
        self._load_meta()
        contents = []

        for trash_path, info in self.meta.items():
            # skip the meta file itself if it slipped in
            if trash_path == self.meta_file:
                continue

            deleted_date = info.get("deleted_date", "")
            # convert ISO timestamp to readable format
            try:
                deleted_date = (datetime
                                .fromisoformat(deleted_date)
                                .strftime("%Y-%m-%d %H:%M:%S"))
            except Exception:
                pass

            contents.append({
                "filename":      info.get("filename", os.path.basename(trash_path)),
                "trash_path":    trash_path,
                "original_path": info.get("original_path", ""),
                "deleted_date":  deleted_date,
                "size":          info.get("size", 0),
            })

        return contents

    # ─────────────────────────────────────────────
    # EMPTY TRASH  (called by ui_manager)
    # ─────────────────────────────────────────────
    def empty_trash(self):
        try:
            for filename in os.listdir(self.trash_dir):
                if filename == ".trash_meta.json":
                    continue
                filepath = os.path.join(self.trash_dir, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)

            self.meta = {}
            self._save_meta()
            return True, "Trash emptied successfully"

        except Exception as e:
            return False, str(e)

    # ─────────────────────────────────────────────
    # LEGACY HELPER
    # ─────────────────────────────────────────────
    def move_to_trash(self, filepath):
        """Legacy method – accepts a plain file path."""
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        fake_row = (None, filename, filepath, "", filesize)
        return self.add_to_trash(fake_row)

    def restore_from_trash(self, trash_path, original_path=None):
        """Legacy alias for restore_file."""
        return self.restore_file(trash_path)