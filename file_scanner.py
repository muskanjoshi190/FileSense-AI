import os
import hashlib
from pathlib import Path


class FileScanner:
    def __init__(self):
        self.supported_text_extensions = {
            '.txt', '.py', '.java', '.cpp', '.html', '.css',
            '.js', '.json', '.xml', '.md', '.csv', '.ini',
            '.conf', '.log', '.rtf', '.doc', '.docx'
        }

    # ─────────────────────────────────────────────
    # FILE HASH
    # ─────────────────────────────────────────────
    def get_file_hash(self, filepath, chunk_size=8192):
        """Generate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error hashing file {filepath}: {e}")
            return None

    # ─────────────────────────────────────────────
    # FILE INFO
    # ─────────────────────────────────────────────
    def get_file_info(self, filepath):
        """Extract full metadata for system"""
        try:
            path  = Path(filepath)
            stats = os.stat(filepath)
            return {
                "filename":      path.name,
                "filepath":      str(path.absolute()),
                "filetype":      path.suffix.lower(),
                "filesize":      stats.st_size,
                "modified_time": stats.st_mtime,
                "category":      self.get_category(path.suffix.lower()),
                "hash":          self.get_file_hash(filepath),
            }
        except Exception as e:
            print(f"Error getting file info: {e}")
            return None

    # ─────────────────────────────────────────────
    # CATEGORY
    # ─────────────────────────────────────────────
    def get_category(self, extension):
        categories = {
            '.txt':  'Documents', '.doc':  'Documents',
            '.docx': 'Documents', '.odt':  'Documents', '.rtf': 'Documents',
            '.xls':  'Spreadsheets', '.xlsx': 'Spreadsheets', '.csv': 'Spreadsheets',
            '.jpg':  'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images',
            '.bmp':  'Images', '.svg':  'Images', '.webp': 'Images',
            '.mp3':  'Audio', '.wav':  'Audio', '.flac': 'Audio', '.aac': 'Audio',
            '.mp4':  'Video', '.avi':  'Video', '.mkv':  'Video', '.mov': 'Video',
            '.py':   'Code', '.java': 'Code', '.cpp':  'Code', '.html': 'Code',
            '.css':  'Code', '.js':   'Code', '.json': 'Code',
            '.zip':  'Archives', '.rar': 'Archives', '.7z': 'Archives', '.tar': 'Archives',
            '.exe':  'Executables', '.msi': 'Executables', '.app': 'Executables',
            '.pdf':  'PDFs',
        }
        return categories.get(extension, 'Other')

    # ─────────────────────────────────────────────
    # MAIN SCAN  ← FIXED
    # ─────────────────────────────────────────────
    def scan_directory(self, directory, progress_callback=None):
        """
        Walk *directory* recursively and return a list of absolute file paths.

        progress_callback(current_dir: str) is called each time the scanner
        enters a new sub-folder, so the UI can show live progress.
        """
        found_files = []

        try:
            for root, dirs, filenames in os.walk(directory):
                # Notify the UI which folder we are currently scanning
                if progress_callback:
                    progress_callback(root)

                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    try:
                        # Skip broken symlinks / unreadable entries
                        if os.path.isfile(filepath):
                            found_files.append(filepath)
                    except Exception:
                        pass

        except Exception as e:
            print(f"Error scanning directory '{directory}': {e}")

        return found_files