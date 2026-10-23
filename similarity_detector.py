import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein


class SimilarityDetector:
    def __init__(self):
        self.text_cache = {}
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            lowercase=True
        )

    # ─────────────────────────────────────────────
    # EXTRACT TEXT
    # ─────────────────────────────────────────────
    def extract_text(self, filepath):
        if filepath in self.text_cache:
            return self.text_cache[filepath]

        try:
            if not os.path.exists(filepath):
                return ""
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read(2000).strip()
                self.text_cache[filepath] = text
                return text
        except Exception:
            self.text_cache[filepath] = ""
            return ""

    # ─────────────────────────────────────────────
    # FILENAME SIMILARITY
    # ─────────────────────────────────────────────
    def filename_similarity(self, name1, name2):
        name1 = os.path.splitext(name1)[0]
        name2 = os.path.splitext(name2)[0]

        if not name1 or not name2:
            return 0.0

        distance = Levenshtein.distance(name1.lower(), name2.lower())
        max_len = max(len(name1), len(name2))

        return 1.0 - (distance / max_len if max_len else 0)

    # ─────────────────────────────────────────────
    # CONTENT SIMILARITY (name-only fallback)
    # ─────────────────────────────────────────────
    def _content_similarity_matrix(self, texts):
        """
        Returns an n×n cosine-similarity matrix.
        Falls back to a zero matrix if TF-IDF cannot be computed
        (e.g. all texts are empty / only stop-words).
        """
        # Filter out completely empty strings for fitting
        non_empty = [t for t in texts if t.strip()]

        if len(non_empty) < 2:
            # Not enough readable text – return zero matrix
            n = len(texts)
            return [[0.0] * n for _ in range(n)]

        try:
            # Re-initialise vectorizer each call to avoid state issues
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                lowercase=True
            )
            tfidf = vectorizer.fit_transform(texts)
            matrix = cosine_similarity(tfidf)
            return matrix
        except Exception as e:
            print(f"SimilarityDetector: TF-IDF failed – {e}")
            n = len(texts)
            return [[0.0] * n for _ in range(n)]

    # ─────────────────────────────────────────────
    # MAIN FUNCTION
    # ─────────────────────────────────────────────
    def find_similar_files(self, db, threshold=0.75):
        """
        Called by ui_manager:
            results = self.similarity_detector.find_similar_files(self.db)
        Returns a list of dicts with file pairs above the similarity threshold.
        """
        files = db.get_all_files()

        if len(files) < 2:
            return []

        # Build structured dataset
        # DB row: (id, filename, filepath, filetype, filesize, hash,
        #          upload_date, category, is_duplicate, dup_group_id)
        data = []
        for f in files:
            filepath = f[2] if len(f) > 2 else ""
            data.append({
                "id":       f[0],
                "filename": f[1] if len(f) > 1 else "",
                "filepath": filepath,
                "content":  self.extract_text(filepath),
            })

        texts = [d["content"] for d in data]
        sim_matrix = self._content_similarity_matrix(texts)

        results = []
        n = len(data)

        for i in range(n):
            for j in range(i + 1, n):
                content_sim = float(sim_matrix[i][j])
                name_sim    = self.filename_similarity(
                    data[i]["filename"],
                    data[j]["filename"]
                )
                combined = (content_sim * 0.7) + (name_sim * 0.3)

                if combined >= threshold:
                    results.append({
                        "file_id1":           data[i]["id"],
                        "file_id2":           data[j]["id"],
                        "file1":              data[i]["filename"],
                        "file2":              data[j]["filename"],
                        "content_similarity": content_sim,
                        "filename_similarity":float(name_sim),
                        "combined_similarity":float(combined),
                    })

        # Sort by combined similarity descending
        results.sort(key=lambda x: x["combined_similarity"], reverse=True)
        return results